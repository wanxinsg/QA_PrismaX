"""
Pytest配置文件
定义全局fixtures和钩子函数
"""
import pytest
import allure
from case_util.http_request import HttpRequest
from case_util.logger import logger
from config import config


@pytest.fixture(scope='session')
def user_management_client():
    """
    用户管理服务HTTP客户端fixture
    
    作用域: session - 整个测试会话中只创建一次
    """
    logger.info(f"创建用户管理服务客户端: {config.USER_MANAGEMENT_BASE_URL}")
    client = HttpRequest(
        base_url=config.USER_MANAGEMENT_BASE_URL,
        timeout=config.REQUEST_TIMEOUT
    )
    yield client
    client.close()
    logger.info("关闭用户管理服务客户端")


@pytest.fixture(scope='session')
def tele_op_client():
    """
    机器人控制服务HTTP客户端fixture
    
    作用域: session - 整个测试会话中只创建一次
    """
    logger.info(f"创建机器人控制服务客户端: {config.TELE_OP_BASE_URL}")
    client = HttpRequest(
        base_url=config.TELE_OP_BASE_URL,
        timeout=config.REQUEST_TIMEOUT
    )
    yield client
    client.close()
    logger.info("关闭机器人控制服务客户端")


@pytest.fixture(scope='function')
def test_user(user_management_client):
    """
    测试用户fixture
    创建测试用户并在测试结束后清理
    
    Returns:
        dict: 包含用户信息的字典
    """
    # 这里可以添加创建测试用户的逻辑
    user_data = {
        'email': config.TEST_EMAIL,
        'wallet_address': config.TEST_WALLET_ADDRESS,
        'chain': config.TEST_CHAIN,
        'token': None  # 在实际测试中会被设置
    }
    
    logger.info(f"创建测试用户: {user_data['email']}")
    yield user_data
    
    # 清理逻辑（如需要）
    logger.info(f"清理测试用户: {user_data['email']}")


@pytest.fixture(scope='function')
def auth_token(user_management_client, test_user):
    """
    获取认证token的fixture
    
    Returns:
        str: 认证token
    """
    # 这里可以添加获取认证token的逻辑
    # 示例：通过登录接口获取token
    token = "test_auth_token"  # 实际应该从登录接口获取
    
    logger.info("获取认证token")
    yield token


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest钩子：收集测试结果
    用于在测试失败时截取更多信息
    """
    outcome = yield
    report = outcome.get_result()
    
    if report.when == 'call':
        # 为allure报告添加测试结果
        if report.failed:
            logger.error(f"测试失败: {item.name}")
        elif report.passed:
            logger.info(f"测试通过: {item.name}")


def pytest_configure(config):
    """Pytest初始化配置"""
    # 导入应用配置（避免与pytest的config对象命名冲突）
    from config import config as app_config
    logger.info("=" * 80)
    logger.info(f"开始测试 - 环境: {app_config.ENV}")
    logger.info(f"用户管理服务: {app_config.USER_MANAGEMENT_BASE_URL}")
    logger.info(f"机器人控制服务: {app_config.TELE_OP_BASE_URL}")
    logger.info("=" * 80)


def pytest_unconfigure(config):
    """Pytest结束配置"""
    logger.info("=" * 80)
    logger.info("测试结束")
    logger.info("=" * 80)


# Pytest命令行参数
def pytest_addoption(parser):
    """添加自定义命令行参数"""
    parser.addoption(
        "--env",
        action="store",
        default="beta",
        help="测试环境: beta, live, local"
    )
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        help="浏览器类型（如果需要UI测试）"
    )


@pytest.fixture(scope='session')
def env(request):
    """环境参数fixture"""
    return request.config.getoption("--env")

