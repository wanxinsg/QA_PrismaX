分析/Users/wanxin/PycharmProjects/Prismax/app-prismax-rp-backend下面的代码，生成一份完整的Backend测试设计文档，
内容包括但不限于：项目概述，测试框架设计，测试用例，测试报告等。

测试框架要求
1.基于Python内置http.server模块，无需额外框架
2.完整的RESTful API接口测试
3.详细的日志记录
4.易于扩展和维护
6.包含单元测试和集成测试
7.提供清晰的文档和示例代码
8.支持allure报告生成
## 目录结构

```
tele_op_services
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
2) 检查tele_op_services下的venv, 启动测试虚拟环境，如有测试依赖，则安装测试依赖

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
## 覆盖范围
Tele-Op 后端Rest api回归测试


ID	Service	Test Case Name	API Endpoint	Method	Input Parameters	Expected Output	Expected Status Code
TO-001	Tele-Op	Get Robots Status	/robots/status	GET	None	{
  "robots": [
    {
      "robot_id": "arm1",
      "is_available": true,
      "queue_length": 5,
      "youtube_stream_id": "stream123",
      "live_paused": false
    }
  ]
}	200

| ID  | Service  | Test Case Name  |  API Endpoint |Method   |  Input Parameters | Expected Output  | Expected Status Code |
|---|---|---|---|---|---|---|----------------------|
| TO-001  |   Tele-Op| Get Robots Status  | /robots/status  | GET  | None  | { "robots": [{"robot_id": "arm1", "is_available": true,"queue_length": 5,"youtube_stream_id": "stream123","live_paused": false}]}  | 200                  |


