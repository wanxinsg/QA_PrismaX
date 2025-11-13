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

测试文件结构大致如下
Test_Framework/
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