# Test_Env

测试框架说明（无需额外服务端框架，仅作为客户端测试工具）：

- 用例通过 `requests` 与 `python-socketio` 访问后端 REST/Socket 接口
- 支持生成 Allure 报告
- 结构清晰，可扩展维护

## 目录结构

```
Test_Env/
├─ case_util/
│  ├─ __init__.py
│  ├─ http_request.py
│  └─ logger.py
├─ test_cases/
│  ├─ test_tele_op.py
│  └─ test_user_management_.py
├─ config.py
├─ conftest.py
├─ pytest.ini
├─ requirements.txt
└─ test_report/
   └─ allure-results/   # pytest 执行时写入
```

## 环境准备

1) 启动 Tele-Op 本地服务（示例）：

```bash
cd /Users/wanxin/PycharmProjects/Prismax/app-prismax-rp-backend/app_prismax_tele_op_services \
  && source .venv/bin/activate \
  && TEST_MODE=true GOOGLE_CLOUD_PROJECT=thepinai GOOGLE_APPLICATION_CREDENTIALS=/Users/wanxin/PycharmProjects/Prismax/thepinai-compute-key.json \
  PORT=8081 python app.py
```

2) 安装测试依赖：

```bash
pip install -r QA_PrismaX/QA_Test/requirements.txt
```

3) 配置环境变量（必须提供用户授权信息，需与后端 DB 一致）：

```bash
export TELE_HOST=localhost
export TELE_PORT=8081
export ROBOT_ID=arm1
export USER_ID=1001047
export TOKEN=QhZewTLifPlcp8I01ZFwCND7F1lKOolpFlbq1fdNA0s
```

可选项：

```bash
export TELE_SCHEME=http
export TELE_BASE=
```

## 运行测试与生成 Allure 报告

```bash
pytest -q QA_PrismaX/QA_Test --alluredir=QA_PrismaX/QA_Test/test_report/allure-results
```

生成可视化报告：

```bash
allure serve QA_PrismaX/QA_Test/test_report/allure-results
```

## 覆盖范围

- Tele-Op 队列（Socket.IO 的 `queue_update` 事件）：
  - 返回数据结构完整
  - `position` 从 1 开始递增且不重复
  - 第一个用户 `status=active`，其余为 `waiting`
  - 每个用户包含 `member_class`，且仅允许 `Innovator Member`/`Amplifier Member`

- 用户管理用例文件提供占位，后续可按需补充。


