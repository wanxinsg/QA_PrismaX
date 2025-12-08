# Prismax Backend API 测试框架

## 📋 项目概述

本测试框架用于 Prismax 后端服务的自动化测试，包括用户管理服务和机器人控制服务的 API 接口测试。

### 测试范围

1. **用户管理服务 (User Management Service)**
   - 用户认证（邮箱验证码、登录、Token验证）
   - 用户信息管理（获取、更新、钱包绑定）
   - 积分系统（每日登录、积分交易）
   - 支付系统（Stripe、加密货币支付）
   - 机器人预约
   - 管理员功能

2. **机器人控制服务 (Tele-Op Service)**
   - 机器人状态查询
   - 队列管理（加入、离开、状态查询）
   - 机器人控制（获取控制权限、连接信息）
   - 控制历史记录
   - 操控排行榜
   - 内部API（机器人服务器通知）

### 测试类型

- **单元测试**: 测试单个API端点的功能
- **集成测试**: 测试多个API端点的交互流程
- **回归测试**: 验证修改不影响现有功能
- **冒烟测试**: 快速验证核心功能

## 🏗️ 项目结构

```
Test_Framework/
├── case_util/               # 工具模块
│   ├── __init__.py
│   ├── http_request.py     # HTTP请求封装
│   └── logger.py           # 日志封装
├── test_cases/             # 测试用例
│   ├── __init__.py
│   ├── test_user_management.py  # 用户管理测试
│   └── test_tele_op.py          # 机器人控制测试
├── test_report/            # 测试报告（自动生成）
│   ├── allure-results/     # Allure原始数据
│   └── allure-report/      # Allure HTML报告
├── logs/                   # 日志文件（自动生成）
├── config.py               # 配置文件
├── conftest.py            # Pytest fixture配置
├── pytest.ini             # Pytest配置
├── requirements.txt       # 项目依赖
└── README.md             # 项目文档
```

## 🚀 快速开始

### 1. 环境准备

**系统要求:**
- Python 3.8+
- pip

**安装依赖:**

```bash
cd Live_Framework
pip install -r requirements.txt
```

### 2. 配置环境

测试框架支持三种环境：
- `beta`: Beta测试环境（默认）
- `live`: 生产环境
- `local`: 本地开发环境

**方式1: 环境变量配置**

```bash
# 设置测试环境
export TEST_ENV=beta

# 设置服务URL
export BETA_USER_MANAGEMENT_URL=https://beta-user-management.example.com
export BETA_TELE_OP_URL=https://beta-tele-op.example.com

# 设置内部API Token
export INTERNAL_API_TOKEN=your_internal_token

# 设置测试账号
export TEST_EMAIL=test@example.com
export TEST_WALLET=your_test_wallet
```

**方式2: 修改config.py文件**

直接编辑 `config.py` 文件中的相应配置类。

### 3. 运行测试

**运行所有测试:**

```bash
pytest
```

**运行指定测试文件:**

```bash
# 仅测试用户管理服务
pytest test_cases/test_user_management.py

# 仅测试机器人控制服务
pytest test_cases/test_tele_op.py
```

**运行指定测试类:**

```bash
pytest test_cases/test_user_management.py::TestHealthCheck
```

**运行指定测试用例:**

```bash
pytest test_cases/test_user_management.py::TestHealthCheck::test_health_check
```

**按标记运行:**

```bash
# 运行冒烟测试
pytest -m smoke

# 运行关键功能测试
pytest -m critical

# 跳过慢速测试
pytest -m "not slow"
```

**指定环境运行:**

```bash
pytest --env=beta
pytest --env=live
pytest --env=local
```

**并行运行（需要安装pytest-xdist）:**

```bash
# 自动检测CPU核心数
pytest -n auto

# 指定进程数
pytest -n 4
```

## 📊 测试报告

### Allure 报告

**生成Allure报告:**

```bash
# 1. 运行测试（自动生成allure-results）
pytest

# 2. 生成HTML报告
allure generate test_report/allure-results -o test_report/allure-report --clean

# 3. 打开报告
allure open test_report/allure-report
```

**或使用一行命令:**

```bash
pytest && allure serve test_report/allure-results
```

### 日志文件

测试执行日志保存在 `logs/` 目录下，按日期命名：
- `logs/test_YYYYMMDD.log` - 测试日志
- `logs/pytest.log` - Pytest框架日志

## 🔧 配置说明

### config.py

配置文件包含三个环境的配置：

```python
# Beta环境
class BetaConfig(Config):
    USER_MANAGEMENT_BASE_URL = 'https://beta-user-management.example.com'
    TELE_OP_BASE_URL = 'https://beta-tele-op.example.com'
    # ...

# Live环境
class LiveConfig(Config):
    USER_MANAGEMENT_BASE_URL = 'https://user-management.prismax.ai'
    TELE_OP_BASE_URL = 'https://tele-op.prismax.ai'
    # ...

# Local环境
class LocalConfig(Config):
    USER_MANAGEMENT_BASE_URL = 'http://localhost:8080'
    TELE_OP_BASE_URL = 'http://localhost:8081'
    # ...
```

### pytest.ini

Pytest配置包括：
- 测试发现规则
- 日志配置
- Allure报告配置
- 测试标记定义

## 📝 编写测试用例

### 测试用例模板

```python
import pytest
import allure
from config import config


@allure.feature('功能模块')
@allure.story('具体功能')
class TestExample:
    """测试类说明"""
    
    @allure.title('测试标题')
    @allure.description('详细描述')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_example(self, user_management_client):
        """测试方法"""
        
        with allure.step("步骤1: 准备测试数据"):
            payload = {'key': 'value'}
        
        with allure.step("步骤2: 发送请求"):
            response = user_management_client.post(
                '/api/endpoint',
                json_data=payload
            )
        
        with allure.step("步骤3: 验证响应"):
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
```

### 使用Fixtures

框架提供了以下fixtures：

```python
def test_with_fixtures(
    user_management_client,  # 用户管理服务客户端
    tele_op_client,          # 机器人控制服务客户端
    test_user,               # 测试用户数据
    auth_token               # 认证token
):
    # 测试代码
    pass
```

## 🎯 最佳实践

### 1. 测试独立性
- 每个测试用例应该独立运行
- 不依赖其他测试的执行顺序
- 测试前设置必要的前置条件
- 测试后清理测试数据

### 2. 断言清晰
```python
# 好的断言
assert response.status_code == 200, f"期望200，实际{response.status_code}"

# 不好的断言
assert response.status_code == 200
```

### 3. 使用Allure Steps
```python
with allure.step("清晰的步骤描述"):
    # 执行操作
    pass
```

### 4. 合理使用标记
```python
@pytest.mark.smoke      # 冒烟测试
@pytest.mark.critical   # 关键功能
@pytest.mark.slow       # 慢速测试
@pytest.mark.skip(reason="原因")  # 跳过测试
```

### 5. 参数化测试
```python
@pytest.mark.parametrize("input,expected", [
    ("value1", "result1"),
    ("value2", "result2"),
])
def test_with_params(input, expected):
    assert process(input) == expected
```

## 🐛 调试技巧

### 1. 详细日志
```bash
pytest -s -v --log-cli-level=DEBUG
```

### 2. 只运行失败的测试
```bash
pytest --lf  # last failed
pytest --ff  # failed first
```

### 3. 进入调试模式
```bash
pytest --pdb
```

### 4. 查看打印输出
```bash
pytest -s
```

## 📈 持续集成

### CI/CD 配置示例

```yaml
# .gitlab-ci.yml / .github/workflows/test.yml
test:
  script:
    - pip install -r requirements.txt
    - export TEST_ENV=beta
    - pytest
    - allure generate test_report/allure-results -o test_report/allure-report
  artifacts:
    paths:
      - test_report/
    when: always
```

## 🔍 常见问题

### Q1: 如何跳过某些测试？
```python
@pytest.mark.skip(reason="原因")
def test_example():
    pass
```

### Q2: 如何处理需要认证的接口？
使用 `auth_token` fixture 或在测试中设置：
```python
client.set_auth_token('your_token')
```

### Q3: 如何测试需要真实数据的接口？
- 使用测试环境的测试账号
- 使用mock数据
- 添加 `@pytest.mark.skip` 标记说明原因

### Q4: 如何查看详细的请求日志？
检查 `logs/test_YYYYMMDD.log` 文件，其中包含所有HTTP请求和响应的详细信息。

## 📚 参考资料

- [Pytest官方文档](https://docs.pytest.org/)
- [Allure报告文档](https://docs.qameta.io/allure/)
- [Requests库文档](https://requests.readthedocs.io/)

## 👥 维护者

QA Team - Prismax

## 📄 许可证

内部项目 - 保密

