
测试框架要求
1.基于Python内置http.server模块，无需额外框架
2.完整的RESTful API接口测试
3.详细的日志记录
4.易于扩展和维护
5.提供清晰的文档和示例代码
6.支持allure报告生成

测试文件结构大致如下
Test_Env/
├─ case_util/
│  ├─ __init__.py
│  ├─ http_request.py     # 封装HTTP请求
│  └─ logger.py           # 日志封装
├─ test_cases/
│  └─ test_tele_op.py  # 机器控制测试用例
│  └─ test_user_management_.py  # 用户管理测试用例
├─ config.py              # 配置（环境包括live环境和beta环境）
├─ conftest.py            # pytest夹具
├─ pytest.ini
├─ test_report/
├─ requirements.txt
└─ README.md


环境准备：
启动本地环境
cd /Users/wanxin/PycharmProjects/Prismax/app-prismax-rp-backend/app_prismax_tele_op_services && source .venv/bin/activate && TEST_MODE=true GOOGLE_CLOUD_PROJECT=thepinai GOOGLE_APPLICATION_CREDENTIALS=/Users/wanxin/PycharmProjects/Prismax/thepinai-compute-key.json PORT=8081 python app.py

queue_check.py已经写了个脚本去获取queue_update，需要用pytest写测试脚本，验证
1.queue Update正常返回了数据
2.queue update返回的数据里面，position是从1开始往后递增，没有重复
3.queue update返回的数据里面，第一个user为active状态，其余为waiting状态
4.queue update返回的数据里面，每个user都显示了member_class,并且仅有Innovator Member和Amplifier Member


生成一个allure报告
