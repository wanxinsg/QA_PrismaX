# QA_PrismaX

PrismaX 自动化测试与质量保障工具集。本项目提供完整的测试框架、用例设计、工具脚本，覆盖 Tele-Op 服务、用户管理服务的 API 测试、Socket 通信测试和数据对账工具。

## 📋 项目概述

本测试项目包含以下核心模块：

- **Daily_Regression_Test** - Tele-Op 服务日常回归测试（一键运行，自动化报告）
- **QA_Env_Auto_Test** - 测试环境自动化测试（Socket.IO、队列事件验证）
- **Tmp_backend-test** - 后端通用 API 测试框架（Beta/Live/Local 环境支持）
- **Live_Test** - 生产环境测试脚本
- **Feature_CaseDesign** - 测试用例设计文档与业务流程说明
- **对账Diff** - CSV 数据对账工具

## 🗂️ 目录结构

```
QA_PrismaX/
├─ Daily_Regression_Test/          # 日常回归测试
│  ├─ tele_op_services/            # Tele-Op REST API 回归测试
│  │  ├─ case_util/                # HTTP 请求和日志工具
│  │  ├─ test_cases/               # 测试用例集
│  │  ├─ run_tests.sh              # 一键测试脚本（自动启动服务、生成报告）
│  │  ├─ Framework.md              # 测试框架设计说明
│  │  └─ test_report/              # Allure 测试报告
│  └─ Test_Framework/              # 测试用例设计文档
├─ QA_Env_Auto_Test/               # 测试环境自动化验证
│  ├─ case_util/                   # 工具库
│  ├─ test_cases/                  # Socket.IO & API 测试用例
│  ├─ run_tests_and_report.sh      # 自动化测试脚本
│  ├─ design.md                    # 设计文档
│  └─ test_report/                 # 测试报告
├─ Tmp_backend-test/               # 后端通用测试框架
│  └─ Test_Framework/              # 完整测试框架（支持多环境）
│     ├─ README.md                 # 框架说明文档
│     ├─ QUICK_START.md            # 快速上手指南
│     ├─ TEST_DESIGN.md            # 测试设计文档
│     └─ 使用指南.md               # 中文使用指南
├─ Live_Test/                      # 生产环境测试
│  └─ run_tests.sh                 # 生产测试脚本
├─ Feature_CaseDesign/             # 功能测试设计
│  ├─ CloudFlare_Cache/            # CloudFlare 缓存测试
│  ├─ image_recognitions_flow.md   # 图像识别流程
│  ├─ pointsystem.md               # 积分系统测试设计
│  ├─ System_Tele.md               # Tele-Op 系统设计
│  ├─ System_User.md               # 用户管理系统设计
│  └─ *.xmind                      # 思维导图（前端/Metamask 等）
└─ 对账Diff/                       # 数据对账工具
   └─ csv_diff/                    # CSV 差异对比脚本

```

## 🚀 快速开始

### 方式一：Tele-Op 日常回归测试（推荐）

**适用场景**：日常回归、CI/CD 集成、本地验证 Tele-Op REST API

**特点**：
- ✅ 一键运行，自动管理后端服务
- ✅ 自动生成 Allure 报告
- ✅ 支持邮件通知测试结果
- ✅ 完整的日志记录

**快速运行**：

```bash
cd QA_PrismaX/Daily_Regression_Test/tele_op_services
./run_tests.sh
```

脚本会自动：
1. 检测并创建虚拟环境 `.venv`
2. 安装测试依赖
3. 启动 Tele-Op 后端服务（如需要）
4. 运行所有测试用例
5. 生成 Allure HTML 报告
6. 发送测试摘要邮件（如配置）

**环境变量配置**（可选）：

```bash
# Tele-Op 服务配置
export TELE_HOST=localhost          # 默认 localhost
export TELE_PORT=8081               # 默认 8081
export TELE_SCHEME=http             # 默认 http
export TELE_BASE=                   # 默认空

# 测试用户认证信息
export ROBOT_ID=arm1                # 机器人 ID
export USER_ID=1073381              # 测试用户 ID
export TOKEN=HZjIrBDYYlDZ2p2hyzj6P4B9HeMKyIGl5lwp3sdorDg  # 授权 Token

# 邮件通知配置（可选）
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your_email@gmail.com
export SMTP_PASS=your_app_password
export EMAIL_FROM=your_email@gmail.com
export EMAIL_TO=team@example.com
```

**测试报告**：
- Allure 原始数据：`test_report/allure-results/`
- Allure HTML 报告：`test_report/allure-report/`
- 后端日志：`backend.log`
- 测试日志：`logs/tele_op_tests.log`

**查看报告**：

```bash
# 打开已生成的报告
allure open test_report/allure-report

# 或重新生成并查看
allure serve test_report/allure-results
```

---

### 方式二：测试环境自动化验证

**适用场景**：本地调试、Socket.IO 事件验证、队列机制测试

**特点**：
- ✅ Socket.IO 实时通信测试
- ✅ 队列事件数据结构验证
- ✅ 自动探测服务就绪状态
- ✅ 支持本地快速调试

**步骤 1：启动 Tele-Op 后端服务**

```bash
cd app-prismax-rp-backend/app_prismax_tele_op_services
source .venv/bin/activate
TEST_MODE=true \
GOOGLE_CLOUD_PROJECT=thepinai \
GOOGLE_APPLICATION_CREDENTIALS=/path/to/thepinai-compute-key.json \
PORT=8081 \
python app.py
```

**步骤 2：安装测试依赖**

```bash
cd QA_PrismaX
pip install -r QA_Env_Auto_Test/requirements.txt
```

**步骤 3：配置测试环境变量**

```bash
export TELE_HOST=localhost
export TELE_PORT=8081
export ROBOT_ID=arm1
export USER_ID=1001047
export TOKEN=QhZewTLifPlcp8I01ZFwCND7F1lKOolpFlbq1fdNA0s
```

**步骤 4：运行测试**

```bash
# 方式 A：直接运行 pytest
pytest -v QA_PrismaX/QA_Env_Auto_Test \
  --alluredir=QA_PrismaX/QA_Env_Auto_Test/test_report/allure-results

# 方式 B：使用自动化脚本（推荐）
QA_PrismaX/QA_Env_Auto_Test/run_tests_and_report.sh
```

**测试覆盖**：
- Socket.IO `queue_update` 事件验证
- 队列数据结构完整性
- 用户状态（active/waiting）验证
- 位置序号正确性检查
- 会员类型验证

---

### 方式三：后端通用 API 测试框架

**适用场景**：多环境测试、完整的 API 回归、用户管理 + Tele-Op 全覆盖

**特点**：
- ✅ 支持 Beta/Live/Local 三种环境
- ✅ 完整的用户管理服务测试
- ✅ 完整的 Tele-Op 服务测试
- ✅ 冒烟测试/回归测试标记
- ✅ 并行执行支持
- ✅ 详细的测试文档

**安装依赖**：

```bash
cd QA_PrismaX/Tmp_backend-test/Test_Framework
pip install -r requirements.txt
```

**运行测试**：

```bash
# 运行全部测试（Beta 环境）
pytest

# 只运行冒烟测试
pytest -m smoke

# 只测试用户管理服务
pytest test_cases/test_user_management.py

# 只测试 Tele-Op 服务
pytest test_cases/test_tele_op.py

# 并行运行（4 进程）
pytest -n 4

# 指定环境
pytest --env=live
pytest --env=local
```

**环境配置**：

```bash
# 切换测试环境
export TEST_ENV=beta  # beta | live | local

# Beta 环境配置（示例）
export BETA_USER_MANAGEMENT_URL=https://user.prismaxserver.com
export BETA_TELE_OP_URL=https://teleop.prismaxserver.com

# Live 环境配置（示例）
export LIVE_USER_MANAGEMENT_URL=https://user.prismax.ai
export LIVE_TELE_OP_URL=https://teleop.prismax.ai

# 内部 API Token
export INTERNAL_API_TOKEN=your_internal_token
```

**生成报告**：

```bash
# 运行测试并生成报告
pytest
allure generate test_report/allure-results -o test_report/allure-report --clean

# 或直接查看
allure serve test_report/allure-results
```

**详细文档**：
- 📖 框架说明：`Tmp_backend-test/Test_Framework/README.md`
- 🚀 快速上手：`Tmp_backend-test/Test_Framework/QUICK_START.md`
- 🎨 测试设计：`Tmp_backend-test/Test_Framework/TEST_DESIGN.md`

---

## 📊 测试报告与日志

### 报告位置

| 模块 | Allure 报告 | 日志文件 |
|------|------------|----------|
| Daily_Regression_Test | `Daily_Regression_Test/tele_op_services/test_report/` | `backend.log`, `logs/tele_op_tests.log` |
| QA_Env_Auto_Test | `QA_Env_Auto_Test/test_report/` | 标准输出 |
| Tmp_backend-test | `Tmp_backend-test/Test_Framework/test_report/` | `logs/` |

### Allure 报告查看

```bash
# 启动报告服务器（自动打开浏览器）
allure serve <allure-results-directory>

# 生成静态 HTML 报告
allure generate <allure-results-directory> -o <output-directory> --clean

# 打开已生成的报告
allure open <allure-report-directory>
```

---

## 🔧 配置说明

### Daily_Regression_Test 配置

- **config.py**：定义 `EnvConfig` 类，从环境变量读取配置
- **conftest.py**：Pytest fixtures，提供 HTTP 客户端
- **pytest.ini**：Pytest 配置（日志、Allure、标记）

### QA_Env_Auto_Test 配置

- **config.py**：支持 `TELE_*` 环境变量配置
- **conftest.py**：提供 Socket.IO 客户端 fixture
- **design.md**：测试设计文档

### Tmp_backend-test 配置

- **config.py**：多环境配置类（BetaConfig/LiveConfig/LocalConfig）
- 支持环境变量覆盖默认配置
- 完整的认证和授权机制

---

## 🛠️ 工具与脚本

### CSV 对账工具

**位置**：`对账Diff/csv_diff/`

**功能**：
- 对比 Solscan 链上数据与数据库数据
- 生成差异报告 CSV
- 支持 Hash 值比对
- 支持列级别对比

**使用示例**：

```bash
cd 对账Diff/csv_diff
python compare_hashes.py  # Hash 对比
python compare_columns.py  # 列对比
```

### 自动化脚本总览

| 脚本 | 功能 | 位置 |
|------|------|------|
| `run_tests.sh` | Tele-Op 日常回归一键测试 | `Daily_Regression_Test/tele_op_services/` |
| `run_tests_and_report.sh` | 测试环境自动化测试 | `QA_Env_Auto_Test/` |
| `run_tests.sh` | 生产环境测试 | `Live_Test/` |

---

## 📖 测试设计文档

### 功能测试设计

| 文档 | 说明 | 位置 |
|------|------|------|
| `System_Tele.md` | Tele-Op 系统测试设计 | `Feature_CaseDesign/` |
| `System_User.md` | 用户管理系统测试设计 | `Feature_CaseDesign/` |
| `image_recognitions_flow.md` | 图像识别流程说明 | `Feature_CaseDesign/` |
| `pointsystem.md` | 积分系统测试设计 | `Feature_CaseDesign/` |
| `CloudFlare_Cache/` | CloudFlare 缓存测试 | `Feature_CaseDesign/CloudFlare_Cache/` |

### 思维导图

- `FE_PrisMax.xmind` - 前端功能全景图
- `Metamask.xmind` - Metamask 集成测试
- `Prismax App (Frontend).xmind` - 前端应用测试设计

---

## 🐛 常见问题

### Q1: Allure 命令未找到

**解决方案**：

```bash
# macOS
brew install allure

# Linux
sudo apt-add-repository ppa:qameta/allure
sudo apt-get update
sudo apt-get install allure

# npm
npm install -g allure-commandline
```

### Q2: Tele-Op 服务启动失败

**检查清单**：
- ✅ 虚拟环境已激活
- ✅ 环境变量正确设置（`GOOGLE_CLOUD_PROJECT`, `GOOGLE_APPLICATION_CREDENTIALS`）
- ✅ 端口 8081 未被占用
- ✅ GCP 密钥文件路径正确

**查看日志**：

```bash
tail -f Daily_Regression_Test/tele_op_services/backend.log
```

### Q3: 测试用户认证失败

**原因**：`USER_ID` 和 `TOKEN` 必须与后端数据库中的用户记录一致

**解决方案**：
- 确认测试用户已在数据库中创建
- 确认 Token 未过期
- 检查环境变量是否正确导出

### Q4: Socket.IO 连接超时

**解决方案**：

```bash
# 确认后端服务运行中
curl http://localhost:8081/robots/status

# 检查 Socket.IO 端点
curl http://localhost:8081/socket.io/

# 使用自动等待脚本
QA_Env_Auto_Test/run_tests_and_report.sh
```

### Q5: 报告生成失败

**原因**：`allure-results` 目录为空或不存在

**解决方案**：

```bash
# 确认测试已运行并生成数据
ls -la test_report/allure-results/

# 重新运行测试
pytest --alluredir=test_report/allure-results
```

---

## 📚 参考资料

- [Pytest 官方文档](https://docs.pytest.org/)
- [Allure 报告框架](https://docs.qameta.io/allure/)
- [Python Requests 文档](https://requests.readthedocs.io/)
- [Python-SocketIO 文档](https://python-socketio.readthedocs.io/)

---

## 👥 团队与维护

**QA Team - PrismaX**

如有问题或建议，请联系 QA 团队或提交 Issue。

---

## 📝 版本历史

- **v2.0** - 重构目录结构，统一测试框架
- **v1.5** - 新增 Socket.IO 测试支持
- **v1.0** - 初始版本，基础 REST API 测试

---

**最后更新**：2025-12-29