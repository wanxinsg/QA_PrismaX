"""
机器人控制服务测试用例
测试机器人状态、队列管理、控制等功能
"""
import pytest
import allure
from config import config


@allure.feature('机器人控制')
@allure.story('机器人状态')
class TestRobotStatus:
    """机器人状态测试"""
    
    @allure.title('获取所有机器人状态')
    @allure.description('获取所有机器人的当前状态和队列信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_robots_status(self, tele_op_client):
        """测试 /robots/status 接口"""
        with allure.step("获取机器人状态"):
            response = tele_op_client.get('/robots/status')
        
        with allure.step("验证响应状态码"):
            assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        with allure.step("验证响应数据结构"):
            data = response.json()
            assert 'robots' in data, "响应中缺少robots字段"
            assert isinstance(data['robots'], list), "robots应该是列表类型"
            
            # 如果有机器人数据，验证数据结构
            if len(data['robots']) > 0:
                robot = data['robots'][0]
                assert 'robot_id' in robot
                assert 'is_available' in robot
                assert 'queue_length' in robot
                assert 'youtube_stream_id' in robot
                assert 'live_paused' in robot
    
    @allure.title('获取直播暂停状态')
    @allure.description('获取所有机器人的直播暂停状态')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_live_paused_status(self, tele_op_client):
        """测试 /get_live_paused_status 接口"""
        with allure.step("获取直播暂停状态"):
            response = tele_op_client.get('/get_live_paused_status')
        
        with allure.step("验证响应"):
            assert response.status_code == 200
            data = response.json()
            assert 'robots' in data
            assert isinstance(data['robots'], list)


@allure.feature('机器人控制')
@allure.story('队列管理')
class TestQueueManagement:
    """队列管理测试"""
    
    @allure.title('查询队列状态')
    @allure.description('查询用户在指定机器人队列中的状态')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="需要真实的用户ID和token")
    def test_queue_status(self, tele_op_client):
        """测试 /queue/status 接口"""
        payload = {
            'userId': 'test_user_id',
            'robotId': 'arm1'
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("查询队列状态"):
            response = tele_op_client.post(
                '/queue/status',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401]
            
            if response.status_code == 200:
                data = response.json()
                assert 'queue' in data
                assert 'robotAvailable' in data
                assert 'yourTurn' in data
                assert isinstance(data['queue'], list)
    
    @allure.title('加入队列')
    @allure.description('用户加入机器人控制队列')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="需要真实的用户ID和token")
    def test_join_queue(self, tele_op_client):
        """测试 /queue/join 接口"""
        payload = {
            'userId': 'test_user_id',
            'robotId': 'arm1'
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("加入队列"):
            response = tele_op_client.post(
                '/queue/join',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401, 403, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert 'position' in data
                assert isinstance(data['position'], int)
    
    @allure.title('离开队列')
    @allure.description('用户离开机器人控制队列')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的用户ID和token")
    def test_leave_queue(self, tele_op_client):
        """测试 /queue/leave 接口"""
        payload = {
            'userId': 'test_user_id',
            'robotId': 'arm1',
            'inactive': False
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("离开队列"):
            response = tele_op_client.post(
                '/queue/leave',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401]
            
            if response.status_code == 200:
                data = response.json()
                assert 'message' in data


@allure.feature('机器人控制')
@allure.story('机器人使用')
class TestRobotControl:
    """机器人控制测试"""
    
    @allure.title('使用机器人')
    @allure.description('获取机器人控制权限和连接信息')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="需要真实的用户ID和token，且用户需要在活跃队列中")
    def test_use_robot(self, tele_op_client):
        """测试 /use_robot 接口"""
        payload = {
            'userId': 'test_user_id',
            'robotId': 'arm1'
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("请求使用机器人"):
            response = tele_op_client.post(
                '/use_robot',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401, 403, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert 'encrypted_url' in data
                assert 'control_token' in data
                assert 'expires' in data
                assert 'isFirstTime' in data
    
    @allure.title('获取URL解密密钥')
    @allure.description('获取用于解密机器人连接URL的密钥')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的用户ID和token")
    def test_session_url_decrypt_key(self, tele_op_client):
        """测试 /session_url_decrypt_key 接口"""
        payload = {
            'userId': 'test_user_id'
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("获取解密密钥"):
            response = tele_op_client.post(
                '/session_url_decrypt_key',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401, 403, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert 'key_b64' in data
                assert 'exp' in data


@allure.feature('机器人控制')
@allure.story('控制历史')
class TestControlHistory:
    """控制历史测试"""
    
    @allure.title('获取用户控制历史')
    @allure.description('获取用户的机器人控制历史记录')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的用户ID和token")
    def test_get_control_history(self, tele_op_client):
        """测试 /user/control_history 接口"""
        payload = {
            'userId': 'test_user_id'
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("获取控制历史"):
            response = tele_op_client.post(
                '/user/control_history',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401]
            
            if response.status_code == 200:
                data = response.json()
                assert 'sessions' in data
                assert 'total_controlled_hours' in data
                assert 'total_reward_points' in data
                assert isinstance(data['sessions'], list)
    
    @allure.title('获取会话完成状态')
    @allure.description('获取特定控制会话的完成状态和结果')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的用户ID、token和控制token")
    def test_fetch_session_complete_status(self, tele_op_client):
        """测试 /fetch_tele_op_session_complete_status 接口"""
        payload = {
            'userId': 'test_user_id',
            'controlToken': 'test_control_token'
        }
        
        headers = {
            'Authorization': 'Bearer test_token'
        }
        
        with allure.step("获取会话完成状态"):
            response = tele_op_client.post(
                '/fetch_tele_op_session_complete_status',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401, 404]
            
            if response.status_code == 200:
                data = response.json()
                # 可能返回 {"status": "not_finished"} 或完整的会话数据
                assert 'status' in data or 'user_id' in data


@allure.feature('机器人控制')
@allure.story('排行榜')
class TestLeaderboard:
    """排行榜测试"""
    
    @allure.title('获取操控排行榜')
    @allure.description('获取机器人操控时长排行榜')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_leaderboard(self, tele_op_client):
        """测试 /tele_op/leaderboard 接口"""
        with allure.step("获取排行榜"):
            response = tele_op_client.get('/tele_op/leaderboard')
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert 'leaderboard' in data
                assert isinstance(data['leaderboard'], list)
                
                # 验证排行榜数据结构
                if len(data['leaderboard']) > 0:
                    entry = data['leaderboard'][0]
                    assert 'user_id' in entry
                    assert 'total_points' in entry
                    assert 'rank' in entry
                    assert 'controlled_hours' in entry
    
    @allure.title('更新排行榜')
    @allure.description('触发排行榜数据更新（内部API）')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.skip(reason="需要真实的内部API token")
    def test_update_leaderboard(self, tele_op_client):
        """测试 /tele_op/leaderboard/update 接口"""
        headers = {
            'Authorization': f'Bearer {config.INTERNAL_API_TOKEN}'
        }
        
        with allure.step("更新排行榜"):
            response = tele_op_client.post(
                '/tele_op/leaderboard/update',
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 401, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert 'status' in data
                assert data['status'] == 'ok'


@allure.feature('机器人控制')
@allure.story('内部API')
class TestInternalAPIs:
    """内部API测试（机器人服务器调用）"""
    
    @allure.title('机器人断开连接通知')
    @allure.description('机器人服务器通知用户断开连接')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的内部API token和机器人ID")
    def test_robot_disconnect(self, tele_op_client):
        """测试 /robot/disconnect 接口"""
        payload = {
            'robotId': 'arm1'
        }
        
        headers = {
            'Authorization': f'Bearer {config.INTERNAL_API_TOKEN}'
        }
        
        with allure.step("发送断开连接通知"):
            response = tele_op_client.post(
                '/robot/disconnect',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert 'status' in data
    
    @allure.title('机器人释放')
    @allure.description('释放机器人，使其变为可用状态')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的内部API token和机器人ID")
    def test_robot_free(self, tele_op_client):
        """测试 /robot/free 接口"""
        payload = {
            'robotId': 'arm1'
        }
        
        headers = {
            'Authorization': f'Bearer {config.INTERNAL_API_TOKEN}'
        }
        
        with allure.step("释放机器人"):
            response = tele_op_client.post(
                '/robot/free',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert 'status' in data
                assert data['status'] == 'ok'
    
    @allure.title('视觉识别 - 玩偶对比')
    @allure.description('提交玩偶抓取前后的图片进行对比识别')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="需要真实的图片数据")
    def test_vision_dolls_compare(self, tele_op_client):
        """测试 /vision/dolls_compare 接口"""
        payload = {
            'robotId': 'arm1',
            'controlToken': 'test_control_token',
            'views': {
                'cam1': {
                    'start': ['base64_image_data_1'],
                    'end': ['base64_image_data_2']
                }
            }
        }
        
        headers = {
            'Authorization': f'Bearer {config.INTERNAL_API_TOKEN}'
        }
        
        with allure.step("提交视觉识别请求"):
            response = tele_op_client.post(
                '/vision/dolls_compare',
                json_data=payload,
                headers=headers
            )
        
        with allure.step("验证响应"):
            assert response.status_code in [200, 400, 401, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert 'success' in data


@allure.feature('机器人控制')
@allure.story('集成测试')
class TestIntegration:
    """集成测试 - 测试完整的用户流程"""
    
    @allure.title('完整队列流程测试')
    @allure.description('测试从查看状态、加入队列到离开队列的完整流程')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skip(reason="需要真实环境和完整的用户数据")
    def test_full_queue_flow(self, tele_op_client):
        """测试完整的队列流程"""
        robot_id = 'arm1'
        user_id = 'test_user_id'
        token = 'test_token'
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # 步骤1: 获取机器人状态
        with allure.step("1. 获取机器人状态"):
            response = tele_op_client.get('/robots/status')
            assert response.status_code == 200
            robots_data = response.json()
            assert 'robots' in robots_data
        
        # 步骤2: 加入队列
        with allure.step("2. 加入队列"):
            payload = {'userId': user_id, 'robotId': robot_id}
            response = tele_op_client.post('/queue/join', json_data=payload, headers=headers)
            assert response.status_code == 200
            join_data = response.json()
            assert 'position' in join_data
        
        # 步骤3: 查询队列状态
        with allure.step("3. 查询队列状态"):
            payload = {'userId': user_id, 'robotId': robot_id}
            response = tele_op_client.post('/queue/status', json_data=payload, headers=headers)
            assert response.status_code == 200
            status_data = response.json()
            assert 'queue' in status_data
        
        # 步骤4: 离开队列
        with allure.step("4. 离开队列"):
            payload = {'userId': user_id, 'robotId': robot_id, 'inactive': False}
            response = tele_op_client.post('/queue/leave', json_data=payload, headers=headers)
            assert response.status_code == 200

