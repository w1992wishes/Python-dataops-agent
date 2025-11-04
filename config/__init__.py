"""
Config模块 - 配置管理
"""
from .logging_config import setup_logging, get_logger

__all__ = [
    'setup_logging',
    'get_logger'
]