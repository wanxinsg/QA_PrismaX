# QA_PrismaX

Prismax 后端 API 的自动化测试与工具集合。包含两套测试目录：
- `Live_Test`：面向 Beta/Live/Local 环境的接口测试框架（含一键脚本、报告、并行等）
- `QA_Test`：面向本地 Tele-Op Socket/队列事件的轻量化测试（便于本地联调）

## 目录结构

```
QA_PrismaX/
├─ Live_Test/                  # 推荐使用的通用测试框架
│  ├─ test_cases/              # 用户管理/Tele-Op 等测试用例
│  ├─ run_tests.sh             # 一键运行与报告脚本（支持参数）
│  ├─ requirements.txt         # 依赖
│  ├─ pytest.ini               # Pytest 配置与 Allure 输出
│  └─ test_report/             # 测试报告输出目录
├─ QA_Test/                    # 本地 Tele-Op 队列/Socket 事件验证
│  ├─ test_cases/              # 示例：队列事件、用户管理占位
│  ├─ run_tests_and_report.sh  # 启动/探测本地 Tele-Op 并跑测+报告
│  ├─ requirements.txt
│  ├─ pytest.ini
│  └─ test_report/
├─ 对账Diff/
│  └─ csv_diff/                # CSV 对账工具脚本与样例
├─ image_recognitions_flow.md  # 图像识别流程说明
├─ pointsystem.md              # 积分系统说明/测试要点
└─ README.md
```

## 快速开始

### 方式 A：使用 Live_Test（推荐）
适用于对 Beta/Live/Local 环境进行接口回归、冒烟、并行执行、Allure 报告等。

1) 安装依赖

```bash
pip install -r QA_PrismaX/Live_Test/requirements.txt
```

2) 常用命令（在 `QA_PrismaX/Live_Test` 下执行）

```bash
# 首次安装依赖
./run_tests.sh --install

# Beta 环境冒烟测试并生成报告
./run_tests.sh -e beta -t smoke -s all -r

# 仅用户管理服务，4 进程并行
./run_tests.sh -e beta -s user -p 4

# 仅 Tele-Op 服务，运行带标记的关键用例
./run_tests.sh -s tele -m critical
```

3) 环境变量（可选）
- `TEST_ENV`：`beta`（默认）/`live`/`local`
- 按需设置服务地址（示例）：

```bash
export BETA_USER_MANAGEMENT_URL=https://user.prismaxserver.com
export BETA_TELE_OP_URL=https://teleop.prismaxserver.com/
# 如需内部通知接口
export INTERNAL_API_TOKEN=your_internal_token
```

4) 查看 Allure 报告

```bash
# 运行后自动在 test_report/allure-results 输出
# 需要安装 Allure CLI：brew install allure 或 npm i -g allure-commandline
allure serve test_report/allure-results
```

### 方式 B：使用 QA_Test（本地 Tele-Op 验证）
适用于本地调试 Tele-Op Socket/队列 `queue_update` 事件的断言与数据结构验证。

1) 启动本地 Tele-Op 服务（示例）

```bash
cd /Users/wanxin/PycharmProjects/Prismax/app-prismax-rp-backend/app_prismax_tele_op_services && \
  source .venv/bin/activate && \
  TEST_MODE=true GOOGLE_CLOUD_PROJECT=thepinai \
  GOOGLE_APPLICATION_CREDENTIALS=/Users/wanxin/PycharmProjects/Prismax/thepinai-compute-key.json \
  PORT=8081 python app.py
```

2) 安装依赖

```bash
pip install -r QA_PrismaX/QA_Test/requirements.txt
```

3) 设置环境变量（需与后端 DB 用户授权一致）

```bash
export TELE_HOST=localhost
export TELE_PORT=8081
export ROBOT_ID=arm1
export USER_ID=1001047
export TOKEN=QhZewTLifPlcp8I01ZFwCND7F1lKOolpFlbq1fdNA0s
# 可选
export TELE_SCHEME=http
export TELE_BASE=
```

4) 运行测试与报告

```bash
# 直接运行
pytest -q QA_PrismaX/QA_Test --alluredir=QA_PrismaX/QA_Test/test_report/allure-results
# 或使用脚本（自动探测后端、执行并打开报告）
QA_PrismaX/QA_Test/run_tests_and_report.sh
```

## 报告与日志
- Allure 原始数据输出目录：
  - `Live_Test/test_report/allure-results`
  - `QA_Test/test_report/allure-results`
- 生成/打开报告：
  - `allure serve <结果目录>` 或 `allure generate ... && allure open ...`
- Live_Test 的 `pytest.ini` 已开启详细日志与持续时间统计；日志输出位于 `Live_Test/logs/`。

## 配置要点
- Live_Test：通过 `TEST_ENV=beta|live|local` 切换环境，`config.py` 内置 `BetaConfig/LiveConfig/LocalConfig`，可用 `BETA_*`、`LIVE_*` 环境变量覆盖默认地址。
- QA_Test：通过 `TELE_*` 与 `ROBOT_ID/USER_ID/TOKEN` 控制本地 Tele-Op 连接与认证；`config.py` 提供 `EnvConfig.base_url` 组合访问地址。

## 常见问题
- 未安装 Allure CLI：请先安装 `brew install allure` 或 `npm i -g allure-commandline`。
- 本地端口占用/后端未就绪：使用 `QA_Test/run_tests_and_report.sh` 会自动等待 Socket.IO 端点就绪。
- Python 版本：建议 Python 3.8+。

## 相关文档与工具
- `image_recognitions_flow.md`：图像识别流程说明
- `pointsystem.md`：积分系统设计与测试要点
- `对账Diff/csv_diff/`：CSV 对账差异工具（按需手动执行）

—— QA Team · Prismax*** End Patch codejson௹assistant.Matcher to=functions.apply_patch  гарassistant.outputs to=functions.apply_patch 코드assistant мәһassistantических to=functions.apply_patch Error codeassistant to=functions.apply_patch পেলassistant to=functions.apply_patch Error: Patch failed at hunks: *** Update File: /Users/wanxin/PycharmProjects/Prismax/QA_PrismaX/README.md