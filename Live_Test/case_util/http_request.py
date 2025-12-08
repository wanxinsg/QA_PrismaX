"""
HTTP请求封装
提供统一的RESTful API接口请求方法
"""
import json
import requests
from typing import Optional, Dict, Any
from .logger import logger


class HttpRequest:
    """HTTP请求封装类"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化HTTP请求客户端
        
        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _log_request(self, method: str, url: str, **kwargs):
        """记录请求日志"""
        log_msg = f"Request: {method} {url}"
        if kwargs.get('json'):
            log_msg += f"\nBody: {json.dumps(kwargs['json'], indent=2)}"
        if kwargs.get('params'):
            log_msg += f"\nParams: {kwargs['params']}"
        if kwargs.get('headers'):
            log_msg += f"\nHeaders: {kwargs['headers']}"
        logger.info(log_msg)
    
    def _log_response(self, response: requests.Response):
        """记录响应日志"""
        log_msg = f"Response: {response.status_code}"
        try:
            log_msg += f"\nBody: {json.dumps(response.json(), indent=2, ensure_ascii=False)}"
        except:
            log_msg += f"\nBody: {response.text}"
        logger.info(log_msg)
    
    def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        **kwargs
    ) -> requests.Response:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE等)
            endpoint: API端点路径
            headers: 请求头
            params: URL查询参数
            json_data: JSON请求体
            data: 表单数据
            **kwargs: 其他requests参数
        
        Returns:
            requests.Response对象
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # 合并headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        # 准备请求参数
        request_kwargs = {
            'headers': request_headers,
            'timeout': kwargs.get('timeout', self.timeout)
        }
        
        if params:
            request_kwargs['params'] = params
        if json_data:
            request_kwargs['json'] = json_data
        if data:
            request_kwargs['data'] = data
        
        # 记录请求日志
        self._log_request(method, url, **request_kwargs)
        
        try:
            response = self.session.request(method, url, **request_kwargs)
            
            # 记录响应日志
            self._log_response(response)
            
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """发送GET请求"""
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """发送POST请求"""
        return self.request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """发送PUT请求"""
        return self.request('PUT', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """发送DELETE请求"""
        return self.request('DELETE', endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        """发送PATCH请求"""
        return self.request('PATCH', endpoint, **kwargs)
    
    def set_auth_token(self, token: str, token_type: str = 'Bearer'):
        """
        设置认证token
        
        Args:
            token: 认证token
            token_type: token类型，默认为Bearer
        """
        self.default_headers['Authorization'] = f'{token_type} {token}'
        logger.info(f"Auth token set: {token_type} {token[:10]}...")
    
    def clear_auth_token(self):
        """清除认证token"""
        if 'Authorization' in self.default_headers:
            del self.default_headers['Authorization']
            logger.info("Auth token cleared")
    
    def close(self):
        """关闭session"""
        self.session.close()

