# QA Review Dashboard — Developer Handoff

Admin portal page (fifth tab: **QA Review**). The HTML file is a self-contained visual prototype — all data is mocked inline. This doc describes what to build against real backend data.

## Page structure

Three stacked regions inside the admin shell:

1. **Summary cards** (3) — top-level counts + hours
2. **QA session status** — two independent bar charts
3. **Review status of uploads** — filterable table with a row-detail modal

Design tokens (dark theme, CSS vars, accent colors, radii) are defined in `:root` and reused throughout. New work should pull from these rather than introducing new values. Tier colors are fixed: Explorer = blue, Amplifier = amber, Innovator = purple.

---

## 1. Summary cards

Three cards, each showing an **upload count** (primary) and a **total hours** figure (secondary), plus a subline.

| Card | Count | Hours | Subline |
|---|---|---|---|
| Total uploads | all uploads | sum of upload hours | — |
| Review complete | count done | hours done | % of uploads · % of hours |
| Under review | count in progress | hours in progress | % of uploads · % of hours |

Notes for backend:
- Complete + Under review should reconcile to Total for both counts and hours.
- Confirm the meaning of "hours" — currently interpreted as **captured demonstration hours contained in the uploads**, not reviewer time spent. The label should reflect whichever is correct.
- Percentages are computed two ways (by upload count and by hours); they will diverge with real data.

---

## 2. QA session status — two charts

Side by side, **each with its own independent time-span toggle** (D / W / M):

- **D** = last 7 days
- **W** = last 8 weeks
- **M** = last 6 months

The two charts do not share state — a user can view sessions by week and reviewers by month simultaneously. (Year was intentionally removed for now.)

**Chart A — Sessions reviewed:** single-series bar chart, count of QA review sessions completed per bucket.

**Chart B — Reviewers participating:** stacked bar chart, count of distinct reviewers per bucket, **segmented by membership tier** (Explorer / Amplifier / Innovator). Legend shown above the plot.

Backend: expose an aggregation endpoint keyed by granularity (`day` | `week` | `month`) returning labeled buckets. Sessions and reviewer-by-tier are the same time buckets, so ideally one endpoint serves both. The three spans should be aggregation windows over the same underlying data, not separate stores, so totals stay consistent across views.

---

## 3. Review status of uploads

### Table columns
`Upload ID` · `Uploaded time` (mm-dd-yy) · `Machine type` · `Round` · `Final QA score` · `Review progress` · `Status`

- **Final QA score** — shown only when review is complete; otherwise `—`. Color thresholds: green ≥ 85, amber 75–84, red < 75.
- **Review progress** — progress bar + `n/target` (target currently 90). Bar turns green at completion. Confirm whether the denominator is a target number of episode-reviews or distinct episodes — this changes the fraction math.
- **Status** — two states only: *Review complete*, *Under review*. **Queued does not exist yet** — do not add it.

### Filters (all combine with each other + search)
- **Search** — by Upload ID
- **Machine type** — Piper, TOK2, YAM, Ego station, Humanoid (drive from real machine registry)
- **Review round** — Round 1 / 2 / 3 (three rounds total)
- **Status** — Review complete / Under review
- **Export CSV** — exports the current filtered view

Result count ("N uploads") updates live as filters change.

Round semantics to confirm: currently each upload belongs to a single round. If uploads move *through* rounds (1→2→3), decide whether the filter means "currently in round N" or should show cross-round history.

### Row detail modal (click any row)
Opens a modal for that upload. Header shows: Upload ID, machine type, uploaded time, status, review count, final QA score.

Body lists each **reviewed episode**. Under each episode:
- episode name + reviewer count + average score
- a table of individual reviewers: **User ID**, **tier** (colored dot), **verdict** (Pass/Fail), **QA score** (same color thresholds)

Backend needs: per upload → episodes reviewed → per episode → list of `{userId, tier, verdict, score}`. Verdict is currently derived from score (≥70 = pass) — if the backend stores an explicit pass/fail vote separate from the numeric score, surface that instead. Empty state ("No episodes reviewed yet") renders when an upload has zero reviews.

Modal closes via X, backdrop click, or Escape.

---

## Mock data to replace

Everything in the `<script>` block is placeholder: `chartData` (day/week/month buckets), the `mkRow` generator (upload rows), and `buildEpisodes` (seeded fake reviewers). Swap these for real API calls. The seeded RNG in `buildEpisodes` exists only to keep the mock stable across opens; drop it once wired to real data.

## Placeholder / dev-only elements
- The other four admin tabs (General Admin, VLA Admin, Data Download, Video Duplicates) are visual only here; they route to existing pages in the real app. Only QA Review is active.

---

---

# QA 审核看板 — 开发交接文档

管理后台页面（第五个标签页：**QA Review**）。HTML 文件是一个独立的视觉原型，所有数据均为内联 mock 数据。本文档描述如何基于真实后端数据进行开发。

## 页面结构

在管理后台框架内，页面由三个垂直排列的区域组成：

1. **汇总卡片**（3 张）— 顶层计数 + 时长
2. **QA 会话状态** — 两个独立的柱状图
3. **上传内容的审核状态** — 可筛选的表格，支持行详情弹窗

设计 Token（深色主题、CSS 变量、强调色、圆角等）定义在 `:root` 中并全局复用。新开发内容应沿用这些变量，不引入新值。各级别颜色固定：Explorer = 蓝色，Amplifier = 琥珀色，Innovator = 紫色。

---

## 1. 汇总卡片

三张卡片，每张显示一个**上传数量**（主要指标）和**总时长**（次要指标），以及一行副标题。

| 卡片 | 计数 | 时长 | 副标题 |
|---|---|---|---|
| 总上传量 | 所有上传 | 上传时长总和 | — |
| 审核完成 | 已完成数量 | 已完成时长 | 占上传量的 % · 占时长的 % |
| 审核中 | 进行中数量 | 进行中时长 | 占上传量的 % · 占时长的 % |

后端注意事项：
- "审核完成"与"审核中"的数量和时长之和应等于总计。
- 确认"时长"的含义 — 当前理解为**上传内容中包含的演示录制时长**，而非审核人员花费的时间。标签文案应与实际含义一致。
- 百分比按两种方式计算（按上传数量和按时长），使用真实数据后两者可能存在差异。

---

## 2. QA 会话状态 — 两个图表

并排展示，**每个图表有独立的时间跨度切换**（D / W / M）：

- **D** = 最近 7 天
- **W** = 最近 8 周
- **M** = 最近 6 个月

两个图表状态互不影响 — 用户可以同时查看"按周的会话数"和"按月的审核人数"。（"年"维度已暂时移除。）

**图表 A — 已审核会话数：** 单系列柱状图，展示每个时间桶内完成的 QA 审核会话数量。

**图表 B — 参与审核人数：** 堆叠柱状图，展示每个时间桶内的不重复审核人数，**按会员等级分段**（Explorer / Amplifier / Innovator）。图例显示在图表上方。

后端要求：提供一个以粒度（`day` | `week` | `month`）为参数的聚合接口，返回带标签的时间桶数据。会话数与分级审核人数使用相同的时间桶，理想情况下由同一接口提供。三种时间跨度应对同一底层数据进行聚合，而非分开存储，以保证跨视图数据一致。

---

## 3. 上传内容的审核状态

### 表格列
`Upload ID` · `上传时间`（mm-dd-yy）· `机器类型` · `轮次` · `最终 QA 评分` · `审核进度` · `状态`

- **最终 QA 评分** — 仅在审核完成后显示；否则显示 `—`。颜色阈值：绿色 ≥ 85，琥珀色 75–84，红色 < 75。
- **审核进度** — 进度条 + `n/目标值`（目标值当前为 90）。完成时进度条变为绿色。请确认分母是目标 episode 审核次数还是不重复 episode 数 — 这会影响分数计算逻辑。
- **状态** — 仅两种：*审核完成*、*审核中*。**"排队中"状态暂不存在** — 请勿添加。

### 筛选条件（可相互组合，并支持搜索）
- **搜索** — 按 Upload ID 搜索
- **机器类型** — Piper、TOK2、YAM、Ego station、Humanoid（从真实机器注册表中获取）
- **审核轮次** — 第 1 / 2 / 3 轮（共三轮）
- **状态** — 审核完成 / 审核中
- **导出 CSV** — 导出当前筛选视图

结果数量（"N 条上传"）随筛选条件变化实时更新。

轮次语义待确认：当前每条上传归属于单一轮次。若上传内容会经历多个轮次（1→2→3），需确定筛选含义是"当前处于第 N 轮"还是显示跨轮次历史记录。

### 行详情弹窗（点击任意行）
为该上传打开弹窗。弹窗头部显示：Upload ID、机器类型、上传时间、状态、审核数量、最终 QA 评分。

弹窗主体列出每个**已审核 episode**。每个 episode 下方包含：
- episode 名称 + 审核人数 + 平均评分
- 各审核人明细表格：**用户 ID**、**等级**（彩色圆点）、**判定结果**（Pass/Fail）、**QA 评分**（相同颜色阈值）

后端需提供：按上传 → 已审核 episode → 每个 episode → `{userId, tier, verdict, score}` 列表的层级数据。判定结果当前由评分推导（≥70 = 通过） — 若后端存储了独立于数值评分的 pass/fail 字段，应优先使用该字段。当某条上传无任何审核记录时，显示空状态（"暂无已审核 episode"）。

弹窗可通过点击 X、点击遮罩层或按 Escape 键关闭。

---

## 需替换的 Mock 数据

`<script>` 块中的所有内容均为占位数据：`chartData`（day/week/month 时间桶）、`mkRow` 生成器（上传行数据）以及 `buildEpisodes`（带种子的虚假审核人数据）。请将这些替换为真实 API 调用。`buildEpisodes` 中的种子随机数生成器仅用于保证 mock 数据在多次打开时保持一致，接入真实数据后可移除。

## 占位 / 仅开发环境元素
- 其他四个管理标签页（General Admin、VLA Admin、Data Download、Video Duplicates）在此仅为视觉展示；在真实应用中，它们会跳转至对应的已有页面。当前仅 QA Review 标签页处于激活状态。
