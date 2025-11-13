"""
日志工具封装
提供统一的日志记录功能
"""
import logging
import os
from datetime import datetime
from pathlib import Path


class TestLogger:
    """测试日志类"""
    
    def __init__(self, name='test', log_dir='logs'):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
            log_dir: 日志文件目录
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 创建文件处理器 - 按日期命名日志文件
        log_file = log_path / f'test_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def debug(self, msg):
        """记录调试信息"""
        self.logger.debug(msg)
    
    def info(self, msg):
        """记录一般信息"""
        self.logger.info(msg)
    
    def warning(self, msg):
        """记录警告信息"""
        self.logger.warning(msg)
    
    def error(self, msg):
        """记录错误信息"""
        self.logger.error(msg)
    
    def critical(self, msg):
        """记录严重错误信息"""
        self.logger.critical(msg)


# 创建全局日志实例
logger = TestLogger()

