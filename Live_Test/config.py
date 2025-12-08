"""
测试配置文件
包含测试环境、API地址、测试数据等配置
"""
import os
from enum import Enum


class Environment(Enum):
    """环境枚举"""
    LIVE = "live"
    BETA = "beta"
    LOCAL = "local"


class Config:
    """基础配置类"""
    
    # 默认环境
    ENV = os.getenv('TEST_ENV', Environment.BETA.value)
    
    # 测试超时时间
    REQUEST_TIMEOUT = 30
    
    # 数据库配置（如需要）
    DB_HOST = os.getenv('DB_HOST', '')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', '')
    DB_USER = os.getenv('DB_USER', '')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # 测试模式
    TEST_MODE = os.getenv('TEST_MODE', 'true').lower() == 'true'
    
    # 日志配置
    LOG_DIR = 'logs'
    LOG_LEVEL = 'INFO'
    
    # Allure报告配置
    ALLURE_RESULTS_DIR = 'test_report/allure-results'
    ALLURE_REPORT_DIR = 'test_report/allure-report'


class BetaConfig(Config):
    """Beta环境配置"""
    
    # User Management Service
    USER_MANAGEMENT_BASE_URL = os.getenv(
        'BETA_USER_MANAGEMENT_URL',
        'https://user.prismaxserver.com'
    )
    
    # Tele-Op Service
    TELE_OP_BASE_URL = os.getenv(
        'BETA_TELE_OP_URL',
        'https://teleop.prismaxserver.com/'
    )
    
    # 测试账号
    TEST_EMAIL = 'wanxin@soliccap.io'
    TEST_WALLET_ADDRESS = '8bsAEeztTsdBB9manAnPr2GN2vQT6dCJsZPn4U2B7Qxy'
    TEST_CHAIN = 'solana'
    
    # 测试用的 reCAPTCHA token (测试环境可能不需要真实token)
    RECAPTCHA_TOKEN = 'test_recaptcha_token'
    
    # 内部API token (用于机器人服务通知)
    INTERNAL_API_TOKEN = os.getenv(
        'INTERNAL_API_TOKEN',
        'test_internal_token'
    )


class LiveConfig(Config):
    """Live生产环境配置"""
    
    # User Management Service
    USER_MANAGEMENT_BASE_URL = os.getenv(
        'LIVE_USER_MANAGEMENT_URL',
        'https://user.prismaxserver.com'
    )
    
    # Tele-Op Service
    TELE_OP_BASE_URL = os.getenv(
        'LIVE_TELE_OP_URL',
        'https://teleop.prismaxserver.com/'
    )
    
    # 生产环境测试账号（谨慎使用）
    TEST_EMAIL = os.getenv('LIVE_TEST_EMAIL', 'wanxin@soliccap.io')
    TEST_WALLET_ADDRESS = os.getenv('LIVE_TEST_WALLET', '8bsAEeztTsdBB9manAnPr2GN2vQT6dCJsZPn4U2B7Qxy')
    TEST_CHAIN = 'solana'
    
    # reCAPTCHA token
    RECAPTCHA_TOKEN = os.getenv('RECAPTCHA_TOKEN', '')
    
    # 内部API token
    INTERNAL_API_TOKEN = os.getenv('INTERNAL_API_TOKEN', '')


class LocalConfig(Config):
    """本地开发环境配置"""
    
    # User Management Service
    USER_MANAGEMENT_BASE_URL = 'http://localhost:8080'
    
    # Tele-Op Service
    TELE_OP_BASE_URL = 'http://localhost:8081'
    
    # 测试账号
    TEST_EMAIL = 'local_test@example.com'
    TEST_WALLET_ADDRESS = 'LocalTestWallet123'
    TEST_CHAIN = 'solana'
    
    # 测试token
    RECAPTCHA_TOKEN = 'local_test_token'
    INTERNAL_API_TOKEN = 'local_internal_token'


def get_config():
    """
    根据环境变量获取配置
    
    Returns:
        配置对象
    """
    env = os.getenv('TEST_ENV', Environment.BETA.value).lower()
    
    if env == Environment.LIVE.value:
        return LiveConfig()
    elif env == Environment.LOCAL.value:
        return LocalConfig()
    else:
        return BetaConfig()


# 全局配置对象
config = get_config()

