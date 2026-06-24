# PRIS-114 / Detect Duplicate Files — 功能逻辑与测试分析

> 仓库：`app-prismax-rp-backend`

---

## 1) 功能概述

系统通过**两个相互独立的重复检测层**识别重复上传数据，并驱动 episode/upload 状态机：

- **Layer 1（尺寸级，阻断型）**：在 MCAP 验证之前比对文件大小，命中即立即失败，不进入后续任何流程。
- **Layer 2（vPDQ 感知 Hash，审核型）**：在 episode 成功派生后比对视频内容相似度，命中则写入待审核记录，等待人工决策后再驱动状态回写。

---

## 2) 主线逻辑总图

```
上传会话阶段（无重复检查）
  POST /data/upload-sessions      → 创建 data_uploads + data_episodes（UPLOADING）
  POST /data/upload-sessions/.../resume → 续传，不做重复判定
  ↓
  客户端直传文件到 GCS raw bucket
  ↓
Worker 触发（GCS Eventarc/Pub-Sub，_MANIFEST.json 落地时触发）
  ↓
  ┌──────────────────────────────────────────────────────────┐
  │  Layer 1：尺寸级重复检测（_find_existing_duplicate_files）  │
  │  阻断型，在 MCAP 验证之前执行                              │
  │  命中 → episode 直接置 DERIVED_VALIDATION_FAILED，返回    │
  └──────────────────────────────────────────────────────────┘
  ↓ 未命中
  MCAP 验证、视频压缩、派生资产生成
  ↓
  episode → DERIVED_READY
  ↓
  ┌──────────────────────────────────────────────────────────┐
  │  Layer 2：vPDQ 感知 hash 检测（_sync_episode_vpdq_reviews）│
  │  非阻断型，在 DERIVED_READY 之后执行                       │
  │  命中阈值 → 写 data_video_duplicate_reviews（PENDING）    │
  │  需人工审核，episode 继续保持 DERIVED_READY                │
  └──────────────────────────────────────────────────────────┘
  ↓
admin 在审核接口（POST .../decision）判定 DUPLICATED / NOT_DUPLICATED
  ↓
系统据判定回写 episode 状态与 processing_error
  ↓
upload 聚合状态同步更新；失败数据可通过 failed_only 下载链路导出定位
```

---

## 3) Layer 1：尺寸级重复检测（阻断型）

### 触发时机

在 `_process_manifest_object()` 中，于 MCAP 验证**之前**执行，是第一道防线。

对应函数：`_find_existing_duplicate_files(conn, upload_id, raw_folder, mcap_size, video_size)` — `worker.py`

### 比较字段

**不使用文件名、不使用 SHA256/MD5**，只比较**聚合字节数**：

| 字段 | 来源 |
|------|------|
| `mcap_size_bytes` | manifest 中 `.mcap` 文件大小 |
| `video_size_bytes` | manifest 中**全部** `.mp4` 大小之和 |

### 匹配条件（SQL 逻辑）

```sql
WHERE e.mcap_size_bytes = :mcap_size
  AND e.video_size_bytes = :video_size
  AND UPPER(COALESCE(e.status, '')) = 'DERIVED_READY'    -- 仅匹配已成功派生的
  AND NOT (e.upload_id = :upload_id AND e.raw_video_folder_path = :raw_folder)  -- 排除自身重跑
ORDER BY e.episode_id DESC
LIMIT 1
```

- 候选范围：**全局**（不限 task、不限 machine、不限 slot）。
- 仅 `DERIVED_READY` 状态的 episode 可作为候选。

### 命中后处理

- episode 状态 → `DERIVED_VALIDATION_FAILED`（立即，不进入 MCAP 验证）
- `processing_error` 结构：

```json
{
  "step": "duplicate_file_validation",
  "error_message": "duplicate files",
  "details": {
    "validation_error_code": "duplicate_files",
    "matched_episode_id": "<id>",
    "matched_upload_id": "<id>",
    "matched_status": "DERIVED_READY",
    "mcap_size_bytes": 12345,
    "video_size_bytes": 67890
  }
}
```

- **无 `duplicate_detection_algorithm` 字段**（Layer 2 的 vPDQ 才有）
- **无 `duplicate_review_id` 字段**（Layer 1 不创建 review 记录）
- upload 聚合状态通过 `_update_upload_status()` 同步更新
- Worker 返回 HTTP 200，`{ ok: false, status: "DERIVED_VALIDATION_FAILED", error: "duplicate files" }`

### 跳过条件（检测失效场景）

| 条件 | 行为 |
|------|------|
| `mcap_size` 或 `video_size` 为 null / ≤ 0 | 整个 Layer 1 检测**跳过**（返回 None），不报错 |
| `task_id == 12`（`DUPLICATE_SIZE_SKIP_TASK_ID`） | Layer 1 检测**整体跳过** |
| episode 已是 `DERIVED_READY` | 提前返回 `"already derived"`，不触发任何检测 |

---

## 4) Layer 2：vPDQ 感知 Hash 检测（审核型）

### 触发时机

episode 进入 `DERIVED_READY` 之后，由 `_sync_episode_vpdq_reviews()` 触发，**不阻断**主流程。

### 可疑判定阈值（满足任一即创建 review）

| 参数名 | 默认值 | 含义 |
|--------|--------|------|
| `VPDQ_DISTANCE_THRESHOLD` | 31 | 逐帧 Hamming 距离阈值（≤此值视为匹配帧） |
| `VPDQ_REVIEW_SCORE_THRESHOLD` | 35% | 最佳 offset 下较短视频覆盖率阈值 |
| `VPDQ_REVIEW_SHORTER_COVERAGE_THRESHOLD` | 40% | 整体 `shorter_coverage_pct` 阈值 |
| `VPDQ_REVIEW_CONTIGUOUS_SECONDS_THRESHOLD` | 10s | 最长连续匹配片段时长阈值 |
| `VPDQ_SECONDS_PER_HASH` | 1.0s | 采样间隔（每秒生成一帧 hash） |
| `VPDQ_OFFSET_BUCKET_SECONDS` | 1.0s | 时间偏移分桶精度 |

### 候选筛选维度

- 同 `task_id` + 同 `video_slot`，不同 `episode_id`
- `video_slot` 由文件名推断（`_map_api_video_slot()`）：

| 文件名特征 | 映射值 |
|-----------|--------|
| 包含 `left`（不区分大小写） | `left` |
| 包含 `right`（不区分大小写） | `right` |
| 其他 | `env` |

**仅同 slot 的视频参与比较**，跨 slot 不参与匹配。

### Artifact 存储路径

```
gs://{VPDQ_HASH_BUCKET}/{VPDQ_HASH_PREFIX}/task_{task_id}/slot_{slot}/metadata_{metadata_id}.json
```

### 命中后处理

写入 `data_video_duplicate_reviews`（`status = PENDING`），`ON CONFLICT DO NOTHING`（unique pair 去重）。episode 继续保持 `DERIVED_READY`，等待人工审核。

### Admin 审核决策

| 输入值（新/旧均接受） | review 状态 | episode 效果 |
|----------------------|-------------|-------------|
| `DUPLICATED` / `APPROVED` | `APPROVED` | source episode → `DERIVED_VALIDATION_FAILED`，写入 `processing_error`（含 `duplicate_detection_algorithm: vpdq`、`duplicate_review_id`） |
| `NOT_DUPLICATED` / `REJECTED` | `REJECTED` | 若 episode 当前失败**仅由该 review 导致**，则恢复 `DERIVED_READY` 并清理 `processing_error` |

upload 聚合状态通过 `_sync_duplicate_review_upload_status()` 重新计算。

---

## 5) Layer 1 与 Layer 2 关键差异对比

| 维度 | Layer 1 尺寸比对 | Layer 2 vPDQ 感知 Hash |
|------|-----------------|------------------------|
| 触发时机 | MCAP 验证之前 | `DERIVED_READY` 之后 |
| 是否阻断 | 是，立即失败 | 否，只创建审核记录 |
| 比较字段 | `mcap_size_bytes` + `video_size_bytes` | 逐帧感知 hash（Hamming 距离） |
| 候选范围 | 全局所有 `DERIVED_READY` episode | 同 `task_id` + 同 `video_slot` |
| 命中结果 | 直接 `DERIVED_VALIDATION_FAILED` | 创建 `PENDING` review，等待人工 |
| `processing_error` 差异 | 含 `matched_episode_id` 等尺寸字段，无 `duplicate_detection_algorithm` | 含 `duplicate_detection_algorithm: vpdq`、`duplicate_review_id` |
| 绕过方式 | `task_id=12` 或 size 为 null/0 | vPDQ 库 import 失败时降级跳过 |
| 可逆性 | **不可通过 admin 审核接口恢复**（无对应 review 记录） | 可通过 NOT_DUPLICATED 决策恢复 |

---

## 6) 关键设计演进点

### 6.1 匹配范围演进（Layer 2）

- 早期：同 task + 同 machine + 同 slot。
- 后期：同 task + 同 slot（移除 machine 限制）。
- 收益：跨 machine 的重复数据可被发现。
- 代价：候选量增加，计算/读取成本提升，需要日志和阈值策略支撑。

### 6.2 数据类型演进

- `machine_id` 从数值假设改为字符串兼容（含 schema 与序列化层）。
- 避免"实际数据是字符串 ID"导致的转换失败和链路中断。

### 6.3 从"记录"到"业务闭环"

- 初期只写 review 记录。
- 后期将 review 决策与 episode/upload 状态机打通，形成可执行的质量治理流程。

---

## 7) 风险点

- 匹配范围扩大后，误报概率与审核量可能上升。
- `processing_error` 回写与恢复条件耦合 `review_id`，需防止错误恢复。
- 大批量 backfill + sync 可能触发存储与数据库热点。
- **Layer 1 尺寸误判风险**：不同内容但 mcap+video 总字节数完全相同的 episode 会被错误阻断（概率低但可能存在）。
- **Layer 1 无法通过 admin 接口恢复**：Layer 1 失败的 episode 没有对应的 duplicate review 记录，无法通过现有 NOT_DUPLICATED 审核接口解除失败状态，需单独的运维手段。
- **Layer 1 跳过条件导致漏检**：`task_id=12` 整体豁免、size 为 null/0 时静默跳过，均不产生任何告警，可能使重复数据被无声引入。
- **admin decision API 旧值兼容**：同时接受 `APPROVED`/`REJECTED`（旧）和 `DUPLICATED`/`NOT_DUPLICATED`（新），前端升级过渡期混用场景需验证。

---

## 8) 完整测试策略

### 8.1 测试目标与质量门槛

- 目标 1：重复检测结果可解释且可追踪（artifact、score、候选来源完整可查）。
- 目标 2：人工审核决策严格驱动状态机，不出现"误恢复/误失败"。
- 目标 3：扩容后（task+slot）性能可控，不影响核心接口 SLA。
- 目标 4：回填与补录流程可幂等重跑，不产生脏数据或重复 review。

发布门槛（Go/No-Go）：

- 功能通过率：P0/P1 用例 100% 通过。
- 状态一致性：episode 与 upload 聚合状态一致性校验 100% 通过。
- 幂等性：关键回填接口重复执行 3 次结果一致。
- 性能：关键 API P95 不劣化超过基线 20%。

### 8.2 分层测试设计

#### A. 单元测试（算法与规则）

- `_find_existing_duplicate_files()`（Layer 1）
  - mcap_size + video_size 均完全匹配时返回候选记录。
  - mcap_size 或 video_size 为 null/0 时返回 None（跳过）。
  - 自身 upload_id + raw_folder 被正确排除（重跑不触发误判）。
  - 仅 `DERIVED_READY` 的 episode 被纳入候选（非 `DERIVED_READY` 不命中）。
- `vpdq_compare_helper.py`
  - `_hamming_distance`、`_coverage`、`_longest_contiguous_run` 的边界值测试。
  - 低质量帧过滤、采样间隔策略正确。
  - 输入为空/特征过少时返回值稳定且可解释。
- worker 内判定逻辑
  - `_is_vpdq_suspicious` 在阈值边界上下行为正确。
  - `decision_status_map`（DUPLICATED/NOT_DUPLICATED）映射正确。
  - `_sync_duplicate_review_upload_status` 对混合 episode 状态聚合结果正确。

#### B. 集成测试（DB + Storage + Worker）

- 相同 mcap_size + video_size 的两条 manifest 依次触发 worker，第二条 episode 应置 `DERIVED_VALIDATION_FAILED`，`processing_error` 含 `matched_episode_id`。
- `task_id=12` 的 manifest 即使尺寸与已有 `DERIVED_READY` episode 完全一致，也不触发 Layer 1 失败。
- Layer 1 失败的 episode 不进入 MCAP 验证、不生成 vPDQ artifact、不创建 review 记录。
- vPDQ artifact 写入与读取（GCS/MinIO）端到端贯通。
- review 表写入去重逻辑（unique pair）生效。
- `machine_id` 为 string/number/null 时全链路可执行。
- review helper 缺失时，artifact 仍写入且日志符合预期。
- candidate artifact 缺失时仅跳过该候选，不中断整批。

#### C. API 合约测试

- `GET /data/admin/video-duplicate-reviews`
  - `status=ALL/PENDING/...`、limit/offset、分页字段一致性。
- `POST /data/admin/video-duplicate-reviews/{review_id}/decision`
  - 输入 DUPLICATED/NOT_DUPLICATED 时返回体和状态变更一致。
  - 旧值 APPROVED/REJECTED 向后兼容验证。
  - 非法 decision、越权、review 不存在时错误码与 msg 正确。
- `POST /admin/backfill-vpdq-artifacts`
  - dry_run 与非 dry_run 字段结构一致，`sync_results` 行为正确。
- 下载相关接口（failed_only/include_test_uploads）
  - 过滤规则与返回 payload 字段完整性正确。

#### D. 回归与兼容测试

- 旧数据中 numeric machine_id 与新 string machine_id 混合共存。
- 历史 review 数据在新默认 `status=ALL` 查询下兼容。
- Layer 1 失败的 episode 的 `processing_error` 结构中无 `duplicate_detection_algorithm` 字段，前端展示不应出错。

### 8.3 风险驱动测试优先级

- P0（必须先通过）
  - 审核决策导致 episode/upload 状态错误流转。
  - 回填重复写入导致 review 脏数据/爆量。
  - 扩大匹配范围后误判激增且无法人工纠偏。
  - Layer 1 尺寸误判导致合法 episode 被阻断且无法通过 admin 接口恢复。
  - Layer 1 跳过条件（null size / task_id=12）不产生告警，导致重复数据静默进入。
- P1（高优先）
  - string machine_id 兼容问题导致链路中断。
  - 候选 artifact 缺失导致批处理中断。
  - admin decision API 旧值（APPROVED/REJECTED）兼容性。
- P2（可并行）
  - 日志字段缺失、可观测性不足。
  - admin 列表默认筛选行为引发体验偏差。
  - Layer 1 与 Layer 2 的 `processing_error` 字段差异是否影响前端展示逻辑。

### 8.4 数据构造策略

- 构造 A（应命中 Layer 2 重复）：同 task+slot，跨 machine，视频内容高度相似。
- 构造 B（不应命中）：同 task+slot 但不同场景/时序差异大。
- 构造 C（边界样本）：分数接近阈值上/下 1 个最小步长。
- 构造 D（异常样本）：候选 artifact 缺失、metadata 缺失、坏视频文件。
- 构造 E（状态机样本）：同 upload 下包含 READY/FAILED/DERIVING 混合 episode。
- 构造 F（Layer 1 尺寸碰撞样本）：两条内容不同但 mcap_size + video_size 完全相同的 episode，验证是否产生误判。
- 构造 G（Layer 1 跳过豁免样本）：task_id=12 的 upload，或 manifest 中 size 字段为 0/null，验证 Layer 1 静默跳过。
- 构造 H（Layer 1 后 Layer 2 不触发样本）：Layer 1 已阻断的 episode，确认不进入 MCAP 验证和 vPDQ 检测。

### 8.5 可观测性与验收指标

- 日志关键字覆盖：
  - `vpdq_sync_start`
  - `vpdq_candidates_loaded`
  - `vpdq_candidate_compared`
  - `vpdq_source_sync_failed`
- 数据指标：
  - review 创建率、人工通过率、误报率（可由抽样复核估计）。
  - 每个 episode 的 candidate_count 与 compare 耗时分位数。
- 质量指标：
  - "审核后状态与预期不一致"缺陷数必须为 0。

---

## 9) E2E 测试用例清单

说明：E2E-L1-xx 为 Layer 1 专项用例，E2E-xx 为 Layer 2 及通用用例。

| 功能模块 | 用例 ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
| --- | --- | --- | --- | --- | --- |
| Layer 1 尺寸级重复检测 | E2E-L1-01 | 尺寸相同触发阻断 | 已存在一条 `DERIVED_READY` episode（mcap_size=X, video_size=Y）；新 upload 内容不同但尺寸完全一致 | 1) 上传新文件并触发 worker；2) 查询新 episode 状态与 `processing_error` | 1) episode 状态 = `DERIVED_VALIDATION_FAILED`；2) `processing_error.step = "duplicate_file_validation"`；3) `details.validation_error_code = "duplicate_files"`；4) `details.matched_episode_id` 存在；5) 无 `duplicate_detection_algorithm` 字段 |
| Layer 1 尺寸级重复检测 | E2E-L1-02 | task_id=12 豁免跳过 | 已存在 `DERIVED_READY` episode；新 upload 属于 task_id=12，尺寸完全相同 | 触发 worker 处理 | episode 不进入 `DERIVED_VALIDATION_FAILED`，正常进入 MCAP 验证流程 |
| Layer 1 尺寸级重复检测 | E2E-L1-03 | size 为 0 或 null 跳过 | manifest 中 `.mcap` size_bytes = 0 或未填写 | 触发 worker 处理 | Layer 1 静默跳过，不报 duplicate，不报错，正常推进 |
| Layer 1 尺寸级重复检测 | E2E-L1-04 | 候选仅限 DERIVED_READY | 已存在尺寸相同但状态为 `DERIVED_VALIDATION_FAILED` 的 episode | 触发 worker 处理新 manifest | Layer 1 不命中（失败状态 episode 不作候选），新 episode 正常推进 |
| Layer 1 尺寸级重复检测 | E2E-L1-05 | 重跑自身不触发误判 | 同一个 upload_id + raw_folder 的 episode 重新触发 worker | 触发 retrigger | 自身不被匹配为重复，不产生 `DERIVED_VALIDATION_FAILED` |
| Layer 1 尺寸级重复检测 | E2E-L1-06 | Layer 1 失败不进入 Layer 2 | Layer 1 命中后 episode 置为失败 | 检查 GCS 中 vPDQ artifact 是否生成；检查 `data_video_duplicate_reviews` | 无对应 vPDQ artifact；无 review 记录 |
| Layer 1 尺寸级重复检测 | E2E-L1-07 | Layer 1 失败无法通过 admin 接口恢复 | episode 因 Layer 1 置为 `DERIVED_VALIDATION_FAILED` | 通过 `GET /data/admin/video-duplicate-reviews` 查找对应 review | 无对应 review 记录（Layer 1 不创建 review），需运维侧手动修复 |
| Layer 1/2 交互 | E2E-L1-08 | Layer 2 vPDQ 不误读 Layer 1 的 processing_error | episode 已有 Layer 1 产生的 `processing_error` | 检查 NOT_DUPLICATED 接口不错误恢复 Layer 1 失败 | admin 无法通过 vPDQ review 接口恢复 Layer 1 引起的失败（两者 review_id 不交叉） |
| 重复检测与审核主链路 | E2E-01 | 重复视频自动入池 | 准备同 task+slot 的两条高度相似视频，确保可生成 vPDQ | 1) 触发 worker 处理；2) 查询 duplicate review 列表 | 1) 产生 `PENDING` review；2) `match_details` 含算法参数、score、artifact 路径 |
| 重复检测与审核主链路 | E2E-02 | 审核 DUPLICATED 回写失败状态 | 存在 `PENDING` review | 1) 调用 decision 接口提交 `DUPLICATED`；2) 查询 source episode 与 upload 聚合状态 | 1) review 变为 `APPROVED`；2) source episode 变为 `DERIVED_VALIDATION_FAILED`；3) `processing_error.details.validation_error_code = duplicate_files`；4) upload 聚合状态同步更新 |
| 重复检测与审核主链路 | E2E-03 | 审核 NOT_DUPLICATED 恢复状态 | episode 当前因该 review 被标记为 `DERIVED_VALIDATION_FAILED` | 1) 提交 `NOT_DUPLICATED`；2) 查询 episode 与 upload | 1) review 变为 `REJECTED`；2) episode 恢复 `DERIVED_READY` 并清理对应 duplicate 错误；3) upload 聚合状态重新计算正确 |
| 重复检测与审核主链路 | E2E-08 | 默认筛选 ALL 行为 | 存在多状态 review（PENDING/APPROVED/REJECTED） | 不传 `status` 查询列表 | 返回全量状态数据（默认 ALL） |
| 回填与同步稳定性 | E2E-04 | backfill 幂等性 | 指定同一批 upload_ids/episode_ids | 连续执行 `POST /admin/backfill-vpdq-artifacts`（非 dry_run）3 次 | 1) 不产生重复 review 脏数据（unique pair 生效）；2) `sync_results` 统计稳定，无异常膨胀 |
| 回填与同步稳定性 | E2E-06 | 候选 artifact 缺失降级 | 删除某候选 artifact | 触发 episode 同步 | 1) 该候选被跳过并记录日志；2) 整体同步继续执行，返回成功或部分成功 |
| 回填与同步稳定性 | E2E-07 | review helper 缺失降级 | 模拟 `video_duplicate_review_helper` 不可用 | 触发 worker | 1) artifact 可写入；2) review 不写入并出现 warning；3) 主流程完成 |
| 回填与同步稳定性 | E2E-15 | 大批量性能冒烟 | 准备较大候选集（如同 task+slot 下 500+ 视频元数据） | 执行 backfill + sync | 在可接受时间内完成；无连接池耗尽、无大面积超时 |
| 兼容性与判定边界 | E2E-05 | 兼容 string machine_id | machine_id 为字符串的 episode 数据存在 | 触发 worker + candidate compare + review 查询 | 1) 无 int 转换异常；2) API 返回 machine_id 字段正确（字符串） |
| 兼容性与判定边界 | E2E-11 | 阈值边界行为 | 构造 score 接近阈值上下边界数据 | 触发 compare | 阈值边界判定稳定，不出现随机抖动 |
| 下载与筛选能力 | E2E-09 | failed_only 下载链路 | 同 upload 下有 DERIVED_READY 与 DERIVED_VALIDATION_FAILED 混合数据 | 调用下载分组接口 `failed_only=true` | 1) 仅返回失败数据样本；2) payload 包含 `processing_error` 且字段结构正确 |
| 下载与筛选能力 | E2E-10 | include_test_uploads 开关 | 准备 test task 与非 test task 上传数据 | 分别调用 `include_test_uploads=false` 与 `include_test_uploads=true` | false 时过滤 test 数据；true 时包含 test 数据 |
| API 健壮性与安全 | E2E-12 | 分页一致性 | review 总数 > 2 页 | 连续请求多页数据 | `count/total_count/has_more/next_offset` 一致 |
| API 健壮性与安全 | E2E-13 | 非法输入防御 | 无 | decision 传非法值，limit/offset 传非法格式 | 返回 400 且错误信息可读 |
| API 健壮性与安全 | E2E-14 | 权限校验 | 无 | 非 admin token 调用 admin 接口 | 返回 401/403（按系统定义），且不泄露内部细节 |

---

## 10) 测试执行与交付建议

- 执行顺序：先执行 **Layer 1 专项（E2E-L1-xx）**，确认阻断型检测机制正确；再执行"重复检测与审核主链路（E2E-01~08）"，再"回填与同步稳定性"，最后执行兼容性、下载筛选、API 健壮性模块。
- 自动化优先：E2E-L1-01/L1-02/E2E-01/02/03/04/05 建议沉淀为 CI 冒烟流水线。
- 数据回收：每轮执行后清理测试 review 与测试 artifact，避免污染后续统计。
- 缺陷分级：状态机错误、幂等性错误归为 blocker；Layer 1 误判（合法 episode 被错误阻断）归为 blocker。
- **Layer 1 恢复路径确认**：在测试计划中明确 Layer 1 导致失败的 episode 目前无 admin 接口可恢复，需与开发确认运维手动修复 SOP（或规划新接口支持）。

---

## 附录：提交时间线分析

> 以下为各提交在 duplicate file check 主线中的逻辑作用，供追溯参考。

### A1. `babec84...`（前置基础能力）

commit message: `fixing verify payment + added duplicate upload helper + removed 5 apis restriction`

- 新增 `app_prismax_data_worker/mcap_sha256_helper.py`
  - 提供文件级 SHA-256 计算能力（分块读取、进度日志、吞吐统计）。
  - ⚠️ **角色定位**：该文件是**独立命令行工具（standalone CLI）**，**未接入上传/重复检测主流程**。生产环境的重复检测不依赖 SHA256，Layer 1 使用尺寸比对，Layer 2 使用 vPDQ 感知 hash。MD5/CRC32C 哈希虽然在 `data_api_episode_file_metadata` 中存储，但同样**未用于重复检测判定**，仅作文件完整性记录。

- 新增 `app_prismax_data_worker/vpdq_compare_helper.py`
  - 提供视频 vPDQ hash 与对比工具链（hash 生成、Hamming 距离/覆盖率计算、时间连续段判定）。
  - 是后续自动重复审核的技术底座。

- **定位：能力预研/工具化阶段**，后续 `df3...` 及之后的 worker + admin 审核闭环，实际上是把这个阶段的 hash/compare 能力产品化和平台化。

---

### A2. `df3b253...`（主线起点：重复审核体系上线）

commit message: `added duplication check + remove 25hz`

- 新建表：`data_video_duplicate_reviews`（存储 source/matched episode 与 metadata、score、status、review 信息、match_details）。
- worker 侧新增：vPDQ artifact 生成与上传、候选检索与相似度判定、可疑项写入 duplicate review 记录。
- data pipeline 新增 admin 接口：查询重复审核列表、提交审核决策（初版 APPROVED/REJECTED/IGNORED）。

**第一次把"检测算法"与"人工审核入口"接通**，形成可运营的数据质量流程起点。

---

### A3. `e8caa19...`（构建环境兜底）

commit message: `trying to build`

- Dockerfile 增加 `libavcodec-dev`、`libavformat-dev` 等 FFmpeg 相关依赖。
- 确保 vPDQ/视频处理链路在容器内可稳定构建与运行。

---

### A4. `fb9f6a4...`（worker 降级可用）

commit message: `fixing worker`

- 修复 `_sync_episode_vpdq_reviews` 的中断行为：review helper import 失败时，从"全有或全无"改为允许 artifact 继续写入，仅 review 写入禁用并打 warning。
- 提升链路鲁棒性。

---

### A5. `ec95245...`（string machine_id 兼容 + backfill API）

commit message: `Fix vPDQ artifact sync for string machine IDs`

- 多处 `machine_id` 输出从 `int` 转 `str`，避免字符串 ID 导致异常。
- 新增 `/admin/backfill-vpdq-artifacts`：支持按 upload/episode 回填 vPDQ artifact，并触发 episode 级同步。
- 增加同步过程日志（metadata/candidate/score 级别）。

修复类型兼容问题，并提供线上补算补录能力。

---

### A6. `553413c...`（扩大匹配范围）

commit message: `Broaden vPDQ duplicate matching scope`

- 候选筛选去掉 `machine_id` 限制（保留 task + slot 维度）。
- artifact 路径去掉 `machine` 目录层级。
- review 表 `machine_id` 改为 `TEXT`，scope 索引也去 machine 维度。

从"同 machine 内比较"扩展为"同 task 同 slot 比较"，明显提高重复命中覆盖。

---

### A7. `a306109...`（failed_only 下载 + worker 异常隔离）

commit message: `added failed only for admin data download + worker bug fixed for duplication detection`

- admin 下载接口支持 `failed_only`、`include_test_uploads`，返回 episode 的 `processing_error`。
- 新增 failed raw manifest 生成链路（针对 `DERIVED_VALIDATION_FAILED`）。
- worker vPDQ 同步改为更细粒度异常隔离：source/candidate 单点失败不影响整批执行。

补齐失败数据运营能力，同时提升检测链路容错。

---

### A8. `3d5aace...`（审核结果驱动业务状态闭环）

commit message: `fixing duplication`

- 重复审核列表默认状态从 `PENDING` 改成 `ALL`。
- 决策语义改造：外部输入 `DUPLICATED / NOT_DUPLICATED`，内部映射到 review 状态 `APPROVED / REJECTED`。
- 状态回写逻辑（关键）：
  - 判定重复（APPROVED）：source episode → `DERIVED_VALIDATION_FAILED`，写入 `processing_error`（`validation_error_code = duplicate_files`）。
  - 判定不重复（REJECTED）：若当前失败正是该 review 导致，则恢复 `DERIVED_READY` 并清理该错误。
- 同步 upload 聚合状态（`DERIVED_READY / DERIVED_PARTIALLY_READY / DERIVED_VALIDATION_FAILED / UPLOADED` 等）。
- backfill 脚本支持 `--sync-reviews`，可边回填边补审核记录。

把"人工审核"从只改 review 表，升级为真正驱动上游数据状态。
