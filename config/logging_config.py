"""
日志配置模块
"""
import logging
import sys
from datetime import datetime
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }

    def format(self, record):
        # 添加颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"

        # 格式化消息
        formatted = super().format(record)
        return formatted


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    console_output: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    设置日志配置

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，None 表示不写入文件
        console_output: 是否输出到控制台
        max_file_size: 日志文件最大大小（字节）
        backup_count: 备份文件数量
    """
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 日志格式
    detailed_format = (
        "%(asctime)s | %(levelname)-8s | %(name)-20s | "
        "%(funcName)-15s:%(lineno)-4d | %(message)s"
    )

    simple_format = "%(asctime)s | %(levelname)-8s | %(message)s"

    date_format = "%Y-%m-%d %H:%M:%S"

    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))

        # 使用彩色格式化器
        console_formatter = ColoredFormatter(simple_format, date_format)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        from logging.handlers import RotatingFileHandler

        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别

        # 使用详细格式化器
        file_formatter = logging.Formatter(detailed_format, date_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # 设置第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    # 配置完成
    root_logger.info("🔧 日志系统初始化完成")
    root_logger.info(f"📊 日志级别: {level}")
    if log_file:
        root_logger.info(f"📁 日志文件: {log_file}")
    root_logger.info(f"🖥️  控制台输出: {'开启' if console_output else '关闭'}")


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)


# 默认配置
def configure_default_logging():
    """配置默认日志设置"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE")

    setup_logging(
        level=log_level,
        log_file=log_file,
        console_output=True
    )


# 环境变量配置
import os

# 自动配置（如果设置了环境变量）
if os.getenv("AUTO_CONFIGURE_LOGGING", "true").lower() == "true":
    configure_default_logging()