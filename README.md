# QA_PrismaX

Prismax 后端 API 的自动化测试与工具集合。当前包含：
- **RegressionTest/tele_op_services**：Tele-Op 服务 REST 回归测试（主入口，含一键脚本、报告、邮件）
- **backend-test/Test_Framework**：后端通用 API 测试框架（User Management + Tele-Op，全量/冒烟/回归）
- **QA_Test**：本地 Tele-Op Socket/队列事件轻量化测试（便于本地联调）
- **对账Diff/csv_diff**：CSV 对账工具
- **CaseDesign**：测试设计与业务流程说明

## 目录结构

```
QA_PrismaX/
├─ RegressionTest/
│  └─ tele_op_services/         # Tele-Op REST 接口回归测试（含 run_tests.sh + Allure 报告）
├─ backend-test/
│  └─ Test_Framework/           # 后端通用 API 测试框架（README/QUICK_START/TEST_DESIGN 等）
├─ QA_Test/                     # 本地 Tele-Op 队列/Socket 事件验证
│  ├─ case_util/                # HTTP/日志封装
│  ├─ test_cases/               # 示例：queue_update 等用例
│  ├─ run_tests_and_report.sh   # 启动/探测本地 Tele-Op 并跑测+报告
│  └─ test_report/
├─ backend-test/
│  └─ Test_Framework/           # 通用后端测试框架（用户管理 + Tele-Op）
├─ CaseDesign/
│  ├─ image_recognitions_flow.md
│  ├─ pointsystem.md
│  └─ teleop_flow.mmd
├─ 对账Diff/
│  └─ csv_diff/                 # CSV 对账工具脚本与样例
└─ README.md
```

## 快速开始

### 方式 A：Tele-Op 服务 REST 回归（RegressionTest/tele_op_services，推荐）
**主入口**，适用于 Tele-Op 后端 REST API 的日常/回归测试（内置一键脚本，可自动拉起本地 Tele-Op 服务、生成 Allure 报告并发摘要邮件）。

1) 进入测试目录并准备虚拟环境（脚本会自动创建 `.venv` 并安装依赖）：

```bash
cd QA_PrismaX/RegressionTest/tele_op_services
./run_tests.sh
```

2) 可选环境变量（不设置时使用脚本中的默认值）：

```bash
export TELE_HOST=localhost
export TELE_PORT=8081
export TELE_SCHEME=http
export TELE_BASE=

export ROBOT_ID=arm1
export USER_ID=1073381
export TOKEN=HZjIrBDYYlDZ2p2hyzj6P4B9HeMKyIGl5lwp3sdorDg

# 如需邮件摘要，请配置 SMTP_*/EMAIL_* 变量，详见 run_tests.sh 内联说明
export SMTP_USER=...
export SMTP_PASS=...
export EMAIL_TO=...
```

3) 报告输出：
- Allure 原始数据：`RegressionTest/tele_op_services/test_report/allure-results/`
- Allure HTML 报告：`RegressionTest/tele_op_services/test_report/allure-report/`

---

### 方式 B：本地 Tele-Op Socket 队列验证（QA_Test）
适用于本地调试 Tele-Op Socket.IO / 队列 `queue_update` 事件的数据结构与断言逻辑。

1) 启动本地 Tele-Op 服务（示例，从仓库根目录）：

```bash
cd app-prismax-rp-backend/app_prismax_tele_op_services && \
  source .venv/bin/activate && \
  TEST_MODE=true GOOGLE_CLOUD_PROJECT=thepinai \
  GOOGLE_APPLICATION_CREDENTIALS=thepinai-compute-key.json \
  PORT=8081 python app.py
```

2) 安装 QA_Test 依赖：

```bash
cd QA_PrismaX
pip install -r QA_Test/requirements.txt
```

3) 设置 Tele-Op 连接与授权环境变量（需与后端 DB 用户授权一致）：

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

4) 运行测试与生成报告：

```bash
# 直接运行 pytest
pytest -q QA_PrismaX/QA_Test --alluredir=QA_PrismaX/QA_Test/test_report/allure-results

# 或使用脚本（自动探测 Socket.IO 端点、执行并打开报告）
QA_PrismaX/QA_Test/run_tests_and_report.sh
```

---

### 方式 C：后端通用 API 回归（backend-test/Test_Framework）
适用于对 **Beta/Live/Local 环境** 的用户管理 + Tele-Op 后端 API 进行冒烟/回归/并行执行与 Allure 报告。

1) 安装依赖（在项目根目录执行）：

```bash
cd QA_PrismaX/backend-test/Test_Framework
pip install -r requirements.txt
```

2) 使用便捷脚本运行（见目录下 `QUICK_START.md` 详情）：

```bash
# 首次安装依赖
./run_tests.sh --install

# 默认（beta 环境）运行全部回归
./run_tests.sh

# 只跑冒烟
./run_tests.sh -t smoke

# 仅用户管理服务 / 仅 Tele-Op 服务
./run_tests.sh -s user
./run_tests.sh -s tele

# 并行运行 & 生成报告
./run_tests.sh -p 4 -r
```

3) 关键环境变量（可选）：

```bash
# 切换环境：beta（默认）/ live / local
export TEST_ENV=beta

# Beta 环境服务地址示例
export BETA_USER_MANAGEMENT_URL=https://user.prismaxserver.com
export BETA_TELE_OP_URL=https://teleop.prismaxserver.com/

# 内部通知接口 Token
export INTERNAL_API_TOKEN=your_internal_token
```

4) 查看 Allure 报告：

```bash
# 已有 allure-results 时
allure serve test_report/allure-results
```

> 更详细的用例设计、标记规范和最佳实践请参见  
> `backend-test/Test_Framework/README.md`、`QUICK_START.md`、`TEST_DESIGN.md`。

---

## 报告与日志总览

- **backend-test/Test_Framework**
  - Allure：`test_report/allure-results`、`test_report/allure-report`
  - 日志：`logs/`（详细 HTTP 请求/响应与 Pytest 日志）
- **QA_Test**
  - Allure：`QA_Test/test_report/allure-results`
- **RegressionTest/tele_op_services**
  - Allure：`RegressionTest/tele_op_services/test_report/allure-results` + `allure-report`
  - Tele-Op 后端日志：`RegressionTest/tele_op_services/backend.log`

## 配置要点速览

- **backend-test/Test_Framework**
  - 通过 `TEST_ENV=beta|live|local` 切换环境；
  - `config.py` 内置 `BetaConfig/LiveConfig/LocalConfig`，可用 `BETA_*`、`LIVE_*` 环境变量覆盖默认地址。
- **QA_Test**
  - 使用 `TELE_*` 与 `ROBOT_ID/USER_ID/TOKEN` 控制本地 Tele-Op 连接与认证；
  - `config.py` 提供 `EnvConfig.base_url` 组合访问地址。
- **RegressionTest/tele_op_services**
  - 通过 `TELE_*`、`ROBOT_ID/USER_ID/TOKEN` 指定目标 Tele-Op 实例；
  - 脚本内置自动重启本地 Tele-Op 服务和 Allure 报告托管逻辑。

## 常见问题

- **未安装 Allure CLI**
  - 请先安装：`brew install allure` 或 `npm i -g allure-commandline`。
- **本地端口占用/后端未就绪**
  - 对于 `QA_Test`：使用 `QA_Test/run_tests_and_report.sh` 会自动等待 Socket.IO 端点就绪；
  - 对于 `RegressionTest/tele_op_services`：`run_tests.sh` 会自动重启 Tele-Op 后端并等待 `robots/status` 可访问。
- **Python 版本**
  - 建议 Python 3.8+。

## 文档与设计说明

- 后端通用测试框架：
  - `backend-test/Test_Framework/README.md`
  - `backend-test/Test_Framework/QUICK_START.md`
  - `backend-test/Test_Framework/TEST_DESIGN.md`
- Tele-Op 回归设计：
  - `RegressionTest/tele_op_services/Framework.md`
- 业务/流程设计：
  - `CaseDesign/image_recognitions_flow.md`
  - `CaseDesign/pointsystem.md`
  - `CaseDesign/teleop_flow.mmd`
- 对账工具：
  - `对账Diff/csv_diff/`

—— QA Team · Prismax