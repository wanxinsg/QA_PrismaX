"""
用户管理服务测试用例
测试用户注册、登录、认证等功能
"""
import pytest
import allure
from config import config


@allure.feature('用户管理')
@allure.story('健康检查')
class TestHealthCheck:
    """健康检查测试"""
    
    @allure.title('测试健康检查接口')
    @allure.description('验证服务健康状态')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_health_check(self, user_management_client):
        """测试 /health 接口"""
        response = user_management_client.get('/health')
        
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        with allure.step("验证响应数据"):
            data = response.json()
            assert 'status' in data or response.text == 'OK'


@allure.feature('用户管理')
@allure.story('用户认证')
class TestAuthentication:
    """用户认证测试"""
    
    @allure.title('发送验证码')
    @allure.description('测试发送邮箱验证码功能')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="需要真实的邮箱")
    def test_send_verification_code(self, user_management_client):
        """测试 /auth/send-verification-code 接口"""
        payload = {
            'email': config.TEST_EMAIL,
            'recaptcha_token': config.RECAPTCHA_TOKEN
        }
        
        with allure.step("发送验证码请求"):
            response = user_management_client.post(
                '/auth/send-verification-code',
                json_data=payload
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 403], \
                f"非预期状态码: {response.status_code}"
            
            data = response.json()
            assert 'success' in data
            
            # 如果成功，验证返回消息
            if response.status_code == 200:
                assert data['success'] is True
    
    @allure.title('验证验证码')
    @allure.description('测试邮箱验证码验证功能')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="需要真实的验证码")
    def test_verify_code(self, user_management_client):
        """测试 /auth/verify-code 接口"""
        payload = {
            'email': config.TEST_EMAIL,
            'code': '123456',  # 实际测试需要真实的验证码
            'recaptcha_token': config.RECAPTCHA_TOKEN
        }
        
        with allure.step("验证验证码"):
            response = user_management_client.post(
                '/auth/verify-code',
                json_data=payload
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401]
            data = response.json()
            assert 'success' in data
    
    @allure.title('管理员登录')
    @allure.description('测试管理员登录功能')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的管理员钱包地址和签名")
    def test_admin_login(self, user_management_client):
        """测试 /api/admin-login 接口"""
        payload = {
            'email': 'admin@test.com',
            'password': 'test_password'
        }
        
        with allure.step("发送管理员登录请求"):
            response = user_management_client.post(
                '/api/admin-login',
                json_data=payload
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401, 403]
            data = response.json()
            assert 'success' in data
    
    @allure.title('验证Token')
    @allure.description('测试Token验证功能')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的token")
    def test_verify_token(self, user_management_client):
        """测试 /verify_token 接口"""
        payload = {
            'token': 'test_token',
            'email': config.TEST_EMAIL
        }
        
        with allure.step("验证token"):
            response = user_management_client.post(
                '/verify_token',
                json_data=payload
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401]
            data = response.json()
            assert 'success' in data


@allure.feature('用户管理')
@allure.story('用户信息')
class TestUserInfo:
    """用户信息测试"""
    
    @allure.title('获取用户信息')
    @allure.description('通过邮箱或钱包地址获取用户信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_users_by_wallet(self, user_management_client):
        """测试 /api/get-users 接口 - 通过钱包地址"""
        params = {
            'wallet_address': config.TEST_WALLET_ADDRESS,
            'chain': config.TEST_CHAIN,
            'recaptcha_token': config.RECAPTCHA_TOKEN
        }
        
        with allure.step("获取用户信息"):
            response = user_management_client.get(
                '/api/get-users',
                params=params
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401, 403]
            data = response.json()
            assert 'success' in data
    
    @allure.title('获取用户信息 - 通过邮箱')
    @allure.description('使用邮箱和token获取用户信息')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="需要真实的token")
    def test_get_users_by_email(self, user_management_client):
        """测试 /api/get-users 接口 - 通过邮箱"""
        params = {
            'email': config.TEST_EMAIL,
            'recaptcha_token': config.RECAPTCHA_TOKEN
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("获取用户信息"):
            response = user_management_client.get(
                '/api/get-users',
                params=params,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401]
            data = response.json()
            assert 'success' in data
    
    @allure.title('更新用户信息')
    @allure.description('测试更新用户信息功能')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的token")
    def test_update_user_info(self, user_management_client):
        """测试 /api/update-user-info 接口"""
        payload = {
            'email': config.TEST_EMAIL,
            'user_name': 'Test User',
            'telegram_id': '@testuser',
            'twitter_id': '@testuser'
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("更新用户信息"):
            response = user_management_client.post(
                '/api/update-user-info',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401]
            data = response.json()
            assert 'success' in data
    
    @allure.title('断开钱包连接')
    @allure.description('测试断开钱包与邮箱的绑定')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的token")
    def test_disconnect_wallet(self, user_management_client):
        """测试 /api/disconnect-wallet-from-email 接口"""
        payload = {
            'email': config.TEST_EMAIL,
            'chain': config.TEST_CHAIN
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("断开钱包连接"):
            response = user_management_client.post(
                '/api/disconnect-wallet-from-email',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401]
            data = response.json()
            assert 'success' in data


@allure.feature('用户管理')
@allure.story('积分系统')
class TestPointsSystem:
    """积分系统测试"""
    
    @allure.title('每日登录积分')
    @allure.description('测试每日登录获取积分功能')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的token")
    def test_daily_login_points(self, user_management_client):
        """测试 /api/daily-login-points 接口"""
        payload = {
            'email': config.TEST_EMAIL
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("获取每日登录积分"):
            response = user_management_client.post(
                '/api/daily-login-points',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401]
            data = response.json()
            assert 'success' in data
    
    @allure.title('获取积分交易记录')
    @allure.description('获取用户的积分交易历史')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的token")
    def test_get_point_transactions(self, user_management_client):
        """测试 /api/get-point-transactions 接口"""
        params = {
            'email': config.TEST_EMAIL,
            'token': 'test_token'
        }
        
        with allure.step("获取积分交易记录"):
            response = user_management_client.get(
                '/api/get-point-transactions',
                params=params
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401]
            data = response.json()
            assert 'success' in data


@allure.feature('用户管理')
@allure.story('支付系统')
class TestPaymentSystem:
    """支付系统测试"""
    
    @allure.title('创建Stripe支付会话')
    @allure.description('测试创建Stripe支付会话')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的token和数据")
    def test_create_stripe_checkout(self, user_management_client):
        """测试 /api/create-stripe-checkout-session 接口"""
        payload = {
            'email': config.TEST_EMAIL,
            'price_id': 'test_price_id',
            'quantity': 1
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("创建Stripe支付会话"):
            response = user_management_client.post(
                '/api/create-stripe-checkout-session',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401]
            data = response.json()
            assert 'success' in data
    
    @allure.title('记录加密货币支付')
    @allure.description('测试记录加密货币支付')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的交易数据")
    def test_record_crypto_payment(self, user_management_client):
        """测试 /api/record-crypto-payment 接口"""
        payload = {
            'email': config.TEST_EMAIL,
            'wallet_address': config.TEST_WALLET_ADDRESS,
            'tx_signature': 'test_tx_signature',
            'chain': config.TEST_CHAIN,
            'tier': 'amplifier'
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("记录加密货币支付"):
            response = user_management_client.post(
                '/api/record-crypto-payment',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401]
            data = response.json()
            assert 'success' in data


@allure.feature('用户管理')
@allure.story('机器人预约')
class TestRobotReservation:
    """机器人预约测试"""
    
    @allure.title('预约机器人')
    @allure.description('测试预约机器人功能')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的token和数据")
    def test_reserve_robot(self, user_management_client):
        """测试 /api/reserve-robot 接口"""
        payload = {
            'email': config.TEST_EMAIL,
            'robot_id': 'arm1',
            'reserve_date': '2025-10-10',
            'reserve_time': '14:00'
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("预约机器人"):
            response = user_management_client.post(
                '/api/reserve-robot',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401]
            data = response.json()
            assert 'success' in data
    
    @allure.title('获取机器人预约信息')
    @allure.description('获取用户的机器人预约信息')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的邮箱")
    def test_get_reserve_robot_info(self, user_management_client):
        """测试 /api/get-reserve-robot-info 接口"""
        params = {
            'email': config.TEST_EMAIL
        }
        
        with allure.step("获取预约信息"):
            response = user_management_client.get(
                '/api/get-reserve-robot-info',
                params=params
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400]


@allure.feature('用户管理')
@allure.story('管理功能')
class TestAdminFeatures:
    """管理员功能测试"""
    
    @allure.title('获取管理员白名单')
    @allure.description('获取管理员白名单列表')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_admin_whitelist(self, user_management_client):
        """测试 /api/get-admin-whitelist 接口"""
        with allure.step("获取管理员白名单"):
            response = user_management_client.get('/api/get-admin-whitelist')
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401]
    
    @allure.title('设置直播暂停状态')
    @allure.description('设置机器人直播的暂停状态')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要管理员权限")
    def test_set_live_paused(self, user_management_client):
        """测试 /api/set-live-paused 接口"""
        payload = {
            'robot_id': 'arm1',
            'live_paused': True
        }
        
        headers = {
            'Authorization': 'Bearer admin_token'
        }
        
        with allure.step("设置直播暂停状态"):
            response = user_management_client.post(
                '/api/set-live-paused',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401, 403]


@allure.feature('用户管理')
@allure.story('其他功能')
class TestMiscFeatures:
    """其他功能测试"""
    
    @allure.title('获取区块链配置地址')
    @allure.description('获取区块链支付配置地址')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_blockchain_config(self, user_management_client):
        """测试 /get_blockchain_config_address 接口"""
        with allure.step("获取区块链配置"):
            response = user_management_client.get('/get_blockchain_config_address')
        
        with allure.step("验证响应"):
            assert response.status_code == 200
    
    @allure.title('获取用户统计信息')
    @allure.description('获取用户的统计数据')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的邮箱")
    def test_user_stats(self, user_management_client):
        """测试 /api/user-stats 接口"""
        params = {
            'email': config.TEST_EMAIL
        }
        
        with allure.step("获取用户统计"):
            response = user_management_client.get(
                '/api/user-stats',
                params=params
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400]
    
    @allure.title('检查问卷状态')
    @allure.description('检查用户的问卷完成状态')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.skip(reason="需要真实的邮箱")
    def test_quiz_check_status(self, user_management_client):
        """测试 /api/quiz/check-status 接口"""
        params = {
            'email': config.TEST_EMAIL
        }
        
        with allure.step("检查问卷状态"):
            response = user_management_client.get(
                '/api/quiz/check-status',
                params=params
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400]

