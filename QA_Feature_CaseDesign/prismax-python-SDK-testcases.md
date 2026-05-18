# PrismaX Python SDK 测试用例设计

> 文档版本：2026-05-14
> 测试框架：pytest（单元/集成）+ 手动执行（E2E）
> 优先级说明：P0 = 阻塞级，P1 = 核心功能，P2 = 边界/异常，P3 = 增强/性能

---

## 一、E2E 测试条目（重点）

### E2E-AUTH：认证流程

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-AUTH-01 | 首次登录并持久化 Token | 未存储任何 Token，`$XDG_CONFIG_HOME` 可写 | `prismax-cli login` → 输入有效 API Token | 1. 提示输入 Token<br>2. 保存至 `~/.config/prismax/credentials.json`<br>3. 文件权限为 `0600`<br>4. 提示登录成功 | P0 |
| E2E-AUTH-02 | 重复登录覆盖旧 Token | 已存在旧 Token | `prismax-cli login` → 输入新 Token | 旧 Token 被覆盖，文件权限保持 `0600` | P1 |
| E2E-AUTH-03 | 登出清除 Token | 已登录 | `prismax-cli logout` | 1. `credentials.json` 被删除或清空<br>2. 再次运行需认证命令时提示未登录 | P1 |
| E2E-AUTH-04 | 使用环境变量 Token 下载 | 未存储文件 Token | `PX_TOKEN=<token> prismax-cli download <pkg_id> --root ./out` | 成功使用环境变量中的 Token 完成认证并开始下载 | P1 |
| E2E-AUTH-05 | Token 优先级：CLI 参数 > 文件 > 环境变量 | 同时存在文件 Token 和环境变量 Token | `prismax-cli --api-key <cli_token> download <pkg_id> --root ./out` | 使用 CLI 参数中的 Token，忽略其他来源 | P2 |
| E2E-AUTH-06 | Token 无效时下载报错 | 无有效 Token | `prismax-cli download <pkg_id> --root ./out`（使用错误 Token） | 退出码非 0，打印有意义的认证失败错误信息（无 traceback） | P1 |
| E2E-AUTH-07 | 无 Token 时触发 MissingTokenError | 无任何 Token 来源 | `prismax-cli download <pkg_id> --root ./out` | 退出码非 0，提示需要 `prismax-cli login` 或设置 `PX_TOKEN` | P0 |

---

### E2E-DL：数据集下载

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-DL-01 | 通过 package_id 完整下载 | 有效 Token，网络可达，磁盘空间充足 | `prismax-cli download pkg_xxx --root ./dataset` | 1. 所有 `.mcap` 文件下载完成<br>2. 每个 episode 的摄像头 `.mp4` 文件下载完成<br>3. `record_config.yaml` 存在<br>4. 无 `.part` 临时文件残留<br>5. 进度信息正常打印 | P0 |
| E2E-DL-02 | 通过本地 manifest.json 下载 | 有效的 `manifest.json`（含 `samples` 字段） | `prismax-cli download manifest.json --root ./dataset` | 按 manifest 下载所有文件，结构与 E2E-DL-01 一致 | P1 |
| E2E-DL-03 | 断点续传：中途中断后恢复 | 下载进行中 | 下载过程中 `Ctrl+C` 中断，再次执行相同命令 | 1. 中断后无损坏文件（`.part` 被清理）<br>2. 重启后跳过已完整文件<br>3. 只下载剩余部分，最终与全量下载结果一致 | P0 |
| E2E-DL-04 | MD5 完整性校验失败时重新下载 | 服务端返回与 `x-goog-hash` 不符的文件（模拟或使用损坏文件） | 执行下载命令 | 检测到 MD5 不匹配，删除损坏文件并重试；不产生静默数据错误 | P1 |
| E2E-DL-05 | 目标目录已存在时幂等下载 | 已完整下载过的目录 | 再次执行相同下载命令 | 所有文件已存在且完整，跳过下载；速度明显快于首次（约 < 5s 完成） | P1 |
| E2E-DL-06 | 网络中断后重试 | 下载过程中模拟网络断开 | 网络恢复后重新执行命令 | 能从断点处继续，最终文件完整 | P2 |
| E2E-DL-07 | 磁盘空间不足时报错 | 目标分区剩余空间不足 | 执行下载命令 | 退出码非 0，提示磁盘空间不足；无损坏的半截文件残留 | P2 |

---

### E2E-CV：MCAP → LeRobot 格式转换

#### E2E-CV-A：基础转换

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-CV-01 | 默认参数全量转换 | 有效 MCAP 数据集目录（含 `.mcap` 和摄像头 `.mp4`） | `prismax-cli convert --root mcap_dir --out lerobot_out` | 输出目录结构符合 LeRobot v2.1：<br>- `meta/info.json`（含 fps=30, width=640, height=480）<br>- `meta/episodes.jsonl`（每行含 episode_index, task, length）<br>- `meta/tasks.jsonl`<br>- `meta/episodes_stats.jsonl`（含 min/max/mean/std/count）<br>- `data/chunk-NNN/episode_NNNNNN.parquet`（含所有必要列）<br>- `videos/chunk-NNN/<video_key>/episode_NNNNNN.mp4` | P0 |
| E2E-CV-02 | Parquet 数据列完整性验证 | E2E-CV-01 完成后 | 用 pandas 读取任意 parquet 文件 | 包含以下列：`action`（float32[14]）、`observation.state`（float32[14]）、`timestamp`（float32, 从0递增）、`frame_index`（int64, 从0开始）、`episode_index`（int64）、`index`（全局单调递增）、`task_index`（int64） | P0 |
| E2E-CV-03 | 视频文件格式验证 | E2E-CV-01 完成后 | 用 ffprobe 检查转换后的 MP4 | H.264 编码，yuv420p 像素格式，分辨率 640×480，帧率约 30 fps | P1 |
| E2E-CV-04 | 多摄像头数据集转换 | 含 cam_high/cam_left/cam_right 三路摄像头的 MCAP 数据集 | `prismax-cli convert --root mcap_dir --out lerobot_out` | `videos/` 下出现 3 个 video_key 目录，每个目录中 episode 数量与 `meta/episodes.jsonl` 一致 | P1 |
| E2E-CV-05 | 自定义分辨率和帧率 | 有效 MCAP 数据集 | `prismax-cli convert --root mcap_dir --out out --fps 15 --width 320 --height 240` | `meta/info.json` 中 fps=15；ffprobe 验证视频分辨率为 320×240 | P1 |
| E2E-CV-06 | `--clean` 参数清除旧输出 | 已有转换输出目录（含旧文件） | `prismax-cli convert --root mcap_dir --out lerobot_out --clean` | 先清除旧目录，再从头转换；输出与全新转换结果一致 | P1 |

#### E2E-CV-B：增量与断点恢复

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-CV-07 | 转换中断后断点续传 | 转换进行中 | `Ctrl+C` 中断，再次执行相同转换命令 | 1. 中断后无损坏/截断文件（`.part` 被清理）<br>2. 重启后已完整的 episode 直接跳过<br>3. 只重新处理未完成的 episode | P0 |
| E2E-CV-08 | 全量转换后再次执行为 no-op | 转换已完成 | 再次执行相同转换命令 | 约 0.3s 内完成（仅重生成 meta 文件），parquet 和视频不重新编码 | P1 |
| E2E-CV-09 | 仅 parquet 完整视频缺失时只补视频 | 手动删除某 episode 的视频文件 | 再次执行转换命令 | 只重新编码缺失的视频，parquet 不重写 | P2 |

#### E2E-CV-C：episode 分片（Chunking）

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-CV-10 | Fixed 模式分片基本功能 | 有长录制（> 60s）的 MCAP | `prismax-cli convert --root mcap_dir --out out --chunk 30` | 1. 每个 LeRobot episode 时长约 30s（允许尾部合并）<br>2. 所有分片无缝拼接等同原始时长<br>3. 每个分片的 frame_index 从 0 重新开始 | P1 |
| E2E-CV-11 | Adaptive 模式分片吸附至静止点 | 有明显手臂静止间隙的长录制 | `prismax-cli convert --root mcap_dir --out out --chunk 60 --chunk-mode adaptive` | 分片边界落在手臂静止区间附近，而非固定时间倍数处 | P1 |
| E2E-CV-12 | 分片后数据帧不丢失、不重复 | 分片转换完成 | 统计所有分片的 parquet 帧数之和 | 等于原始 MCAP 对应的总帧数（允许 ±fps 内误差） | P0 |
| E2E-CV-13 | 分片参数改变触发 `--clean` 提示 | 已用 `--chunk 30` 转换过 | 改用 `--chunk 60` 再次转换（不加 `--clean`） | 打印 per-episode length-mismatch 警告，提示需加 `--clean` 重跑 | P2 |

#### E2E-CV-D：编码器选择

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-CV-14 | CPU 软编码（libx264）可正常完成 | 任意有效 MCAP | `prismax-cli convert --root mcap_dir --out out --hardware-encoder false` | 使用 libx264 完成编码，视频格式正常（H.264/yuv420p） | P1 |
| E2E-CV-15 | NVENC 不可用时 auto 模式 fallback 到 libx264 | 无 NVIDIA GPU 的机器 | `prismax-cli convert --root mcap_dir --out out --hardware-encoder auto` | 无错误报出，自动使用 libx264 完成转换 | P1 |
| E2E-CV-16 | 强制 NVENC 但不可用时报错 | 无 NVIDIA GPU 的机器 | `prismax-cli convert --root mcap_dir --out out --hardware-encoder true` | 退出码非 0，提示 "NVENC not available"，无截断文件残留 | P1 |
| E2E-CV-17 | NVENC 编码（GPU 机器）转换结果正确 | 配备 NVIDIA GPU 且 ffmpeg 支持 NVENC | `prismax-cli convert --root mcap_dir --out out --hardware-encoder true` | 编码成功，视频格式正常，速度明显快于 libx264 | P1 |

---

### E2E-VIZ：3D 可视化渲染

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-VIZ-01 | 使用内置 PiperX 模型渲染 episode 0 | LeRobot 数据集，已安装 `[visualize]` 和 `[robots]` | `prismax-cli visualize --root lerobot_out --episode 0 --robot piperx` | 生成有效 MP4 文件，用视频播放器可正常播放，能看到机械臂动作 | P1 |
| E2E-VIZ-02 | 使用自定义 URDF 渲染 | 已有 URDF 文件和配套 mesh | `prismax-cli visualize --root lerobot_out --episode 0 --urdf path/to/robot.urdf` | 同 E2E-VIZ-01，使用自定义机器人模型 | P1 |
| E2E-VIZ-03 | 渲染 action 轨迹 | LeRobot 数据集 | `prismax-cli visualize --root lerobot_out --episode 0 --robot piperx --source action` | 渲染使用 action 列（leader 轨迹），而非默认 observation.state | P2 |
| E2E-VIZ-04 | 指定输出分辨率和帧率 | LeRobot 数据集 | `prismax-cli visualize --root lerobot_out --episode 0 --robot piperx --width 1920 --height 1080 --fps 60` | 输出 MP4 分辨率为 1920×1080，帧率 60fps | P2 |
| E2E-VIZ-05 | 使用 `--stride` 快速预览 | LeRobot 数据集 | `prismax-cli visualize --root lerobot_out --episode 0 --robot piperx --stride 5` | 渲染帧数为原来的 1/5，文件大小明显减小，生成速度加快 | P2 |
| E2E-VIZ-06 | 自动生成默认输出文件名 | LeRobot 数据集 | `prismax-cli visualize --root lerobot_out --episode 3 --robot piperx`（不指定 `--out`） | 文件名以数据集名开头，含 `--3--` 片段，以 `.mp4` 结尾 | P2 |
| E2E-VIZ-07 | `[visualize]` 未安装时报明确错误 | 未安装 `[visualize]` extra | `prismax-cli visualize --root lerobot_out --episode 0 --robot piperx` | 退出码非 0，打印安装提示 `pip install 'prismax[visualize]'`，无 traceback | P1 |
| E2E-VIZ-08 | `[robots]` 未安装时报明确错误 | 已装 `[visualize]`，未装 `[robots]` | `prismax-cli visualize --root lerobot_out --episode 0 --robot piperx` | 退出码非 0，打印安装提示 `pip install 'prismax[robots]'`，无 traceback | P1 |

---

### E2E-VIEWER-LOCAL：本地 GUI 查看器

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-VWR-L-01 | 打开本地数据集 | 有效 LeRobot v2.1 数据集，已安装 `[viewer]` | `prismax-viewer /path/to/lerobot_out` | 1. 主窗口正常打开<br>2. 左侧 Episode 列表加载，显示序号/长度/任务名<br>3. 视频区显示 episode 0 第一帧<br>4. 图表区显示 observation.state 曲线 | P0 |
| E2E-VWR-L-02 | 自动跳转至指定 episode | 有效数据集 | `prismax-viewer --episode 5 /path/to/lerobot_out` | 打开后直接选中并加载第 6 个 episode（0-indexed） | P1 |
| E2E-VWR-L-03 | 播放/暂停控制 | 已打开数据集 | 点击 Play 按钮 → 等待 2s → 点击 Pause | 1. 播放时帧计数器递增，视频和图表同步推进<br>2. 暂停后帧计数器停止，画面冻结 | P0 |
| E2E-VWR-L-04 | 进度条拖动 seek | 播放中或暂停状态 | 拖动进度条到中间位置 | 视频跳转至对应帧，图表游标同步移动，三路视频无漂移 | P0 |
| E2E-VWR-L-05 | 多路摄像头同步播放 | 含 3 路摄像头的数据集 | 播放任意 episode | 三路视频同帧显示，时间戳一致，无明显延迟差 | P0 |
| E2E-VWR-L-06 | 切换 episode | 已打开数据集 | 点击 Episode 列表中的不同行 | 加载对应 episode，视频、图表、Transport Bar 同步更新 | P1 |
| E2E-VWR-L-07 | 键盘方向键切换 episode | 已打开数据集，Episode 列表获得焦点 | 按上下方向键 | 逐条切换 episode，同 E2E-VWR-L-06 | P2 |
| E2E-VWR-L-08 | Action overlay 开关 | 已打开 episode | 勾选 "Show action overlay" 复选框 | 图表上出现 action 虚线轨迹；取消勾选后消失 | P1 |
| E2E-VWR-L-09 | 图表缩放与 Reset Zoom | 已打开 episode | 在图表区滚轮缩放 → 点击 Reset Zoom | 1. 两个子图 x 轴联动缩放<br>2. Reset Zoom 后恢复全 episode 视图，y 轴自动范围 | P1 |
| E2E-VWR-L-10 | 播放速度调节 | 播放中 | 将速度从 1× 调至 2×，再调至 0.25× | 视频/图表更新频率随速度变化，帧序列保持正确不乱序 | P2 |
| E2E-VWR-L-11 | 播放完毕后停在末帧 | 已打开 episode | 播放至结尾 | 停在最后一帧，Play 按钮恢复可用状态 | P2 |
| E2E-VWR-L-12 | `[viewer]` 未安装时报错 | 未安装 `[viewer]` extra | `prismax-viewer /path/to/dataset` | 退出码非 0，打印安装提示 `pip install 'prismax[viewer]'`，无 traceback | P1 |

---

### E2E-VIEWER-HTTP：HTTP Server 模式查看器

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-VWR-HTTP-01 | 启动 `prismax-viewer-serve` 并连接 Viewer | 有效 LeRobot 数据集 | 1. `prismax-viewer-serve --root dataset --port 8080 --token mytoken`<br>2. `PRISMAX_VIEWER_TOKEN=mytoken prismax-viewer http://127.0.0.1:8080/` | Viewer 正常打开并加载远端数据集，功能与本地一致 | P1 |
| E2E-VWR-HTTP-02 | Bearer Token 鉴权拒绝未授权请求 | Server 已启动 | 直接访问 `http://127.0.0.1:8080/manifest`（无 Token） | 返回 HTTP 401 | P1 |
| E2E-VWR-HTTP-03 | 路径穿越攻击防护 | Server 已启动 | 请求 `/file?path=../../../etc/passwd` | 返回 HTTP 400 | P1 |
| E2E-VWR-HTTP-04 | Range 断点续传支持 | Server 已启动 | 使用 `Range: bytes=0-9` 头请求文件 | 返回 206 Partial Content，内容为文件前 10 字节 | P2 |
| E2E-VWR-HTTP-05 | ETag 缓存协商（304 Not Modified） | Server 已启动 | 第一次请求获取 ETag，第二次带 `If-None-Match` 头 | 第二次返回 304，body 为空 | P2 |
| E2E-VWR-HTTP-06 | `--idle-timeout` 自动退出 | Server 已启动，设置 `--idle-timeout 30` | 30s 内无任何请求 | Server 进程自动退出 | P2 |
| E2E-VWR-HTTP-07 | `--token-file` 方式传入 Token | Server 和 Viewer 均支持文件方式 | `prismax-viewer --token-file /run/secrets/viewer_token http://...` | Token 正确读取，Viewer 正常连接 | P2 |

---

### E2E-VIEWER-SSH：SSH 远程查看器

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-VWR-SSH-01 | 密钥认证 SSH 远程打开数据集 | 目标机器 SSH 密钥已配置，远端有 Python ≥ 3.10，有 LeRobot 数据集 | `prismax-viewer --ssh user@host --root /data/lerobot_dataset` | 1. 终端依次显示：Probe → Stage → Launch → Forward → Connect 进度<br>2. GUI 窗口打开<br>3. 数据集加载正常 | P0 |
| E2E-VWR-SSH-02 | 密码认证 SSH 远程打开数据集 | 目标机器仅支持密码认证 | `prismax-viewer --ssh user@host --root /data/dataset`（无密钥） | 终端提示输入密码（无回显），最多 3 次重试机会，成功后 GUI 正常打开 | P1 |
| E2E-VWR-SSH-03 | 首次连接自动 stage 服务端 zipapp | 远端 `~/.prismax-server/` 目录不存在 | 同 E2E-VWR-SSH-01 | zipapp（~200KB）被上传到远端，server 启动并监听 loopback | P1 |
| E2E-VWR-SSH-04 | 二次连接复用已有 zipapp（快速启动） | 已完成过一次 E2E-VWR-SSH-01 | 再次执行相同连接命令 | Stage 步骤耗时明显缩短（跳过上传），直接启动服务 | P1 |
| E2E-VWR-SSH-05 | 远端数据集元数据缓存至本地 | 已完成 E2E-VWR-SSH-01 | 检查本地缓存目录 `~/.local/share/prismax/viewer/` | 存在对应 `<host_id>/<dataset_id>/meta/` 目录，包含 `info.json` 等文件 | P1 |
| E2E-VWR-SSH-06 | 断网后从本地缓存离线打开 | E2E-VWR-SSH-05 完成，且已缓存完整 episode | 断开网络，再次执行连接命令（或用 `--cache-dir` 直接打开缓存路径） | 利用本地缓存正常播放；不触发网络请求 | P2 |
| E2E-VWR-SSH-07 | 自定义 SSH 端口 | 目标机器 SSH 在非标准端口 | `prismax-viewer --ssh user@host --port 2222 --root /data/dataset` | SSH 通过 2222 端口建立连接，功能正常 | P2 |
| E2E-VWR-SSH-08 | 附加 SSH 参数（identity file） | 有特定 identity file | `prismax-viewer --ssh user@host --root /data/dataset --ssh-option IdentityFile=~/.ssh/special_key` | 使用指定 identity file 认证 | P2 |
| E2E-VWR-SSH-09 | SSH 密码文件读取 | 有密码文件 | `prismax-viewer --ssh user@host --root /data/dataset --ssh-password-file /run/secrets/pw` | 从文件读取密码，认证成功，密码不出现在进程列表中 | P2 |
| E2E-VWR-SSH-10 | Server 10 分钟无操作自动退出 | SSH 远程连接已建立，server 使用默认 idle-timeout | 10 分钟不操作 Viewer | 远端 server 进程自动退出；Viewer 界面显示连接断开提示 | P3 |
| E2E-VWR-SSH-11 | SSH 认证失败 3 次后给出明确提示 | 密码错误 | 连续输入 3 次错误密码 | 提示认证失败，退出码非 0，无 traceback | P1 |
| E2E-VWR-SSH-12 | 缓存超过 50 GiB 状态栏告警 | 本地缓存目录合计 > 50 GiB | 打开任意 SSH 远程数据集 | 状态栏 CachePanel 变为琥珀色并显示 ⚠ 图标 | P3 |

---

### E2E-FULL：全链路集成测试

| 编号 | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|------|----------|----------|----------|----------|--------|
| E2E-FULL-01 | **完整链路：登录→下载→转换→渲染→查看** | 无任何缓存，有效 API Token，有 GPU（可选） | 1. `prismax-cli login`<br>2. `prismax-cli download pkg_xxx --root dataset`<br>3. `prismax-cli convert --root dataset/task_name --out lerobot_out --clean`<br>4. `prismax-cli visualize --root lerobot_out --episode 0 --robot piperx --out ep0.mp4`<br>5. `prismax-viewer lerobot_out` | 每步无错误退出<br>最终：ep0.mp4 可正常播放，Viewer 正常加载所有 episode | P0 |
| E2E-FULL-02 | **链路：下载→分片转换→查看** | 有效数据集，含长录制 | 1. 下载数据集<br>2. `prismax-cli convert --root dataset --out lerobot_out --chunk 30 --chunk-mode adaptive`<br>3. `prismax-viewer lerobot_out` | 转换后 episode 数量多于原始 MCAP 数量；Viewer 中所有分片 episode 正常可播放 | P1 |
| E2E-FULL-03 | **链路：转换→SSH 远程查看** | 转换完成，有可 SSH 访问的远端机器 | 1. 转换完成后将数据集 rsync 至远端<br>2. `prismax-viewer --ssh user@host --root /remote/lerobot_out` | SSH 远端数据集正常加载，视频播放流畅 | P1 |

---

## 二、模块级测试条目

### UT-AUTH：认证模块

| 编号 | 测试标题 | 测试类型 | 优先级 |
|------|----------|----------|--------|
| UT-AUTH-01 | 凭证文件路径遵循 XDG_CONFIG_HOME | 单元 | P1 |
| UT-AUTH-02 | store_token 写入并自动去除首尾空格 | 单元 | P1 |
| UT-AUTH-03 | 存储 Token 后文件权限为 0600 | 单元 | P0 |
| UT-AUTH-04 | store_token 空字符串抛出 ValueError | 单元 | P1 |
| UT-AUTH-05 | 重复 store_token 覆盖旧值 | 单元 | P1 |
| UT-AUTH-06 | clear_stored_token 幂等（文件不存在时返回 False） | 单元 | P2 |
| UT-AUTH-07 | Token 优先级：参数 > 文件 > 环境变量 | 单元 | P0 |
| UT-AUTH-08 | 空字符串参数不遮盖文件/环境变量 | 单元 | P1 |
| UT-AUTH-09 | 无任何 Token 来源时抛出 MissingTokenError | 单元 | P0 |
| UT-AUTH-10 | 损坏 JSON 文件优雅降级（stderr 告警，返回 None） | 单元 | P1 |
| UT-AUTH-11 | 空 token 字段被忽略 | 单元 | P1 |

### UT-CONVERT：转换算法

| 编号 | 测试标题 | 测试类型 | 优先级 |
|------|----------|----------|--------|
| UT-CV-01 | chunk_seconds=None 时返回单一全量范围 | 单元 | P0 |
| UT-CV-02 | 零帧时分片计划为空 | 单元 | P1 |
| UT-CV-03 | 短于 N 秒的 episode 返回单一分片 | 单元 | P1 |
| UT-CV-04 | [N, 4N) 范围内均匀分 2-4 片（无 stub） | 单元 | P0 |
| UT-CV-05 | ≥ 4N 的 episode 走 fixed-size 路径 | 单元 | P1 |
| UT-CV-06 | 尾部 < 10s stub 合并至前一片 | 单元 | P0 |
| UT-CV-07 | 尾部恰好等于 10s 时保留（不合并） | 单元 | P1 |
| UT-CV-08 | 1-250s 任意长度分片无间隙/不重叠不变量 | 属性 | P0 |
| UT-CV-09 | adaptive 模式切点吸附至静止段中点 | 单元 | P1 |
| UT-CV-10 | adaptive 无静止点时 fallback 至 ideal 位置 | 单元 | P1 |
| UT-CV-11 | adaptive 同一静止段不被两个切点重用 | 单元 | P1 |
| UT-CV-12 | adaptive 最小切块长度保护（回归：6328.mcap 场景） | 单元 | P0 |
| UT-CV-13 | _build_frame_table：chunk slice 后 frame_index 从 0 重置 | 单元 | P0 |
| UT-CV-14 | _build_frame_table：timestamp 从 0 重置但信号切片正确 | 单元 | P0 |
| UT-CV-15 | _build_frame_table：越界 range 自动 clamp | 单元 | P1 |
| UT-CV-16 | _build_frame_table：空 range 返回 shape[1]=14 的空数组 | 单元 | P1 |

### UT-STILLNESS：静止段检测

| 编号 | 测试标题 | 测试类型 | 优先级 |
|------|----------|----------|--------|
| UT-ST-01 | 匀速运动信号速度计算准确 | 单元 | P0 |
| UT-ST-02 | 夹爪列默认被排除在速度计算外 | 单元 | P1 |
| UT-ST-03 | 常数输入速度为 0 | 单元 | P1 |
| UT-ST-04 | 跨多关节取 max | 单元 | P1 |
| UT-ST-05 | 空帧/单帧输入不崩溃 | 单元 | P1 |
| UT-ST-06 | 静止段基本检测：两个 valley 均被找到 | 单元 | P0 |
| UT-ST-07 | 最小持续时长过滤短暂静止 | 单元 | P1 |
| UT-ST-08 | 无静止段时返回空列表 | 单元 | P1 |
| UT-ST-09 | 自动阈值：过快/过慢速度被 clamp 至 floor/ceil | 单元 | P1 |

### UT-SERVER：Viewer HTTP Server

| 编号 | 测试标题 | 测试类型 | 优先级 |
|------|----------|----------|--------|
| UT-SRV-01 | /healthz 无需 Token 返回 200 + ok:true | 集成 | P0 |
| UT-SRV-02 | 无 Token 访问 /manifest 返回 401 | 集成 | P0 |
| UT-SRV-03 | 错误 Token 访问返回 401 | 集成 | P0 |
| UT-SRV-04 | /manifest 返回正确的 fps/episodes 数量/video_keys | 集成 | P0 |
| UT-SRV-05 | /file 支持 Range 请求（206 Partial Content） | 集成 | P1 |
| UT-SRV-06 | /file 支持 ETag + If-None-Match（304 Not Modified） | 集成 | P1 |
| UT-SRV-07 | /file 路径穿越攻击返回 400 | 集成 | P0 |
| UT-SRV-08 | /list 路径穿越攻击返回 400 | 集成 | P0 |
| UT-SRV-09 | /digest 返回正确 sha256 和 size | 集成 | P1 |
| UT-SRV-10 | /digest 文件不存在返回 404 | 集成 | P1 |
| UT-SRV-11 | 未知端点返回 404 | 集成 | P2 |
| UT-SRV-12 | log-dir 模式下 stderr Handler 被移除（管道死锁回归） | 单元 | P0 |

---

## 三、测试盲区 / 待补充测试（QA 建议新增）

| 编号 | 缺失场景 | 建议测试方式 | 风险等级 |
|------|----------|-------------|----------|
| GAP-01 | MCAP 格式合规性：转换输出是否完全符合 LeRobot v2.1 schema | 用 LeRobot 官方 validator 或 schema 校验脚本 | 高 |
| GAP-02 | 关节数据时间对齐精度：50Hz 关节状态重采样至 30fps 误差 | 用已知时间戳的合成 MCAP 验证 parquet 中 timestamp 偏差 | 高 |
| GAP-03 | 大数据集转换稳定性（100+ episodes，数十 GB） | 长时间运行测试，监控内存占用和磁盘使用 | 高 |
| GAP-04 | SIGINT 安全中断不产生损坏文件（自动化） | 在测试中发送 SIGINT，检查 `.part` 文件清理 | 高 |
| GAP-05 | macOS 核心功能兼容性（download + convert） | 在 macOS 上手动执行 E2E-FULL-01 | 中 |
| GAP-06 | Viewer 帧精度：seek 后三路视频帧一致性 | 截图对比 seek 前后帧号与视频内容 | 中 |
| GAP-07 | 缓存目录超 50GiB 告警显示（自动化） | mock 缓存目录大小触发阈值判断 | 低 |
| GAP-08 | HuggingFace 上传后可被 lerobot 加载 | 上传后用 `lerobot` 库 load_dataset 验证格式完整性 | 高 |
| GAP-09 | SSH 跳板机（ProxyJump）场景 | 有跳板机的环境中执行 E2E-VWR-SSH-01 | 中 |
| GAP-10 | 并发多 Viewer 连接同一 Server | 同时打开多个 `prismax-viewer` 指向同一 server URL | 低 |

---

## 附：测试执行说明

### 场景一：本地开发（venv）

适用于本地开发、调试和手动跑测试。

#### 1. 环境准备

```bash
# 进入仓库根目录
cd /path/to/prismax-python

# 创建 venv（首次）
python3 -m venv .venv

# 激活 venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 验证使用的是 venv 内的 Python
which python                     # 应输出 .../prismax-python/.venv/bin/python

# 安装依赖（必须先装 prismax-robots，再装 prismax）
python -m pip install -e ./prismax-robots
python -m pip install -e './prismax[dev]'

# 若需要跑 viewer 相关测试，加上 viewer extra
python -m pip install -e './prismax[viewer,dev]'

# 验证安装成功
python -c "import prismax; print('OK:', prismax.__file__)"
```

> ⚠️ **常见陷阱**：直接执行 `pytest` 可能调用系统 Python 的 pytest（即使 venv 已激活），导致 `ModuleNotFoundError: No module named 'prismax'`。
> 务必使用 `python -m pytest`，确保使用 venv 内的解释器。

#### 2. 运行自动化测试

```bash
# 激活 venv（若尚未激活）
source .venv/bin/activate

# 运行所有单元/集成测试
python -m pytest prismax/tests -q

# 只运行转换相关测试
python -m pytest prismax/tests -k "convert or stillness" -v

# 只运行 Server/Auth 相关测试
python -m pytest prismax/tests -k "server or auth" -v

# 只运行静止段检测测试
python -m pytest prismax/tests -k "stillness" -v

# 只运行 viewer 相关测试
python -m pytest prismax/tests -k "viewer" -v

# 运行全部并显示通过/跳过/失败摘要
python -m pytest prismax/tests -v --tb=short
```

> 注意：`test_viewer_server.py` 和 `test_viewer_cache_fetcher.py` 依赖 `lerobot_sample/` 目录，目录不存在时自动 skip，不影响其他测试通过。

#### 3. 手动/E2E 测试

```bash
# 激活 venv（若尚未激活）
source .venv/bin/activate

# 冒烟测试：Viewer GUI（需要有效数据集，需安装 viewer extra）
python prismax/tests/smoke_viewer.py /path/to/lerobot_sample

# SSH 远程 Viewer 冒烟测试
python prismax/tests/smoke_remote_viewer.py user@host /remote/dataset

# CLI 命令（venv 激活后 prismax-cli 可直接使用，或用 python -m 方式）
prismax-cli download pkg_xxx --root ./dataset
prismax-cli convert --root ./dataset/task --out ./lerobot_out --clean
prismax-cli visualize --root ./lerobot_out --episode 0 --robot piperx
# 等价的 python -m 写法（更安全，不依赖激活状态）
python -m prismax.cli download pkg_xxx --root ./dataset
```

---

### 场景二：CI 自动化（无 venv，全局安装）

适用于 GitHub Actions、Jenkins 等 CI 环境，使用系统 Python 或 CI 提供的 Python 环境，无需激活 venv。

#### 1. 环境准备

```bash
# 安装依赖（先装 prismax-robots，再装 prismax）
pip install -e ./prismax-robots
pip install -e './prismax[all,dev]'
```

#### 2. 运行自动化测试

```bash
# 运行所有单元/集成测试
pytest prismax/tests -q

# 只运行转换相关测试
pytest prismax/tests -k "convert or stillness" -v

# 只运行 Server/Auth 相关测试
pytest prismax/tests -k "server or auth" -v

# 只运行静止段检测测试
pytest prismax/tests -k "stillness" -v

# 只运行 viewer 相关测试
pytest prismax/tests -k "viewer" -v

# 运行全部并输出 JUnit XML 报告（CI 平台通用格式）
pytest prismax/tests -v --tb=short --junit-xml=test-results.xml
```

> CI 环境中 `pip` 和 `pytest` 均指向同一 Python，不存在 venv 混用问题，可直接使用命令。

### 测试数据准备

| 数据类型 | 用途 | 获取方式 |
|----------|------|----------|
| 小型 MCAP 数据集（2-5 episodes，< 1GB） | 基础 E2E 转换/渲染 | `prismax-cli download` 获取公开 demo 包 |
| 长录制 MCAP（单 episode > 120s） | 分片逻辑验证 | 从 PrismaX 平台选取长录制包 |
| `lerobot_sample/`（40 episodes，已转换） | Viewer Server 集成测试 | 随仓库预置或单独准备 |
| SSH 可达的 Linux 机器 | SSH 远程 Viewer E2E | 测试环境服务器 |
| 带 NVIDIA GPU 的机器 | NVENC 编码路径 | 专用 GPU 测试节点 |
