"""
日志系统模块
Logging system module
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional
from loguru import logger
from src.config import get_config


# 敏感信息模式（用于过滤）
SENSITIVE_PATTERNS = [
    r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\']+)',
    r'apikey["\']?\s*[:=]\s*["\']?([^"\']+)',
    r'password["\']?\s*[:=]\s*["\']?([^"\']+)',
    r'token["\']?\s*[:=]\s*["\']?([^"\']+)',
    r'secret["\']?\s*[:=]\s*["\']?([^"\']+)',
]


def mask_sensitive_info(message: str) -> str:
    """
    屏蔽日志中的敏感信息
    
    Args:
        message: 原始日志消息
    
    Returns:
        str: 屏蔽敏感信息后的消息
    """
    masked_message = message
    
    for pattern in SENSITIVE_PATTERNS:
        # 替换敏感信息为 "***"
        masked_message = re.sub(
            pattern,
            lambda m: m.group(0).replace(m.group(1), "***"),
            masked_message,
            flags=re.IGNORECASE
        )
    
    return masked_message


class SensitiveFilter:
    """敏感信息过滤器"""
    
    def __call__(self, record):
        """过滤日志记录中的敏感信息"""
        if hasattr(record, "message"):
            record["message"] = mask_sensitive_info(str(record["message"]))
        return True


def setup_logger(config_path: Optional[str] = None) -> None:
    """
    设置日志系统
    
    Args:
        config_path: 配置文件路径（可选）
    """
    config = get_config()
    log_config = config.logging
    
    # 移除默认的 logger
    logger.remove()
    
    # 确保日志目录存在
    log_file_path = Path(log_config.file)
    log_dir = log_file_path.parent
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    if log_config.format == "json":
        # 使用loguru的JSON序列化功能
        log_format = (
            '{{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"module": "{module}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}"}}'
        )
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # 添加控制台输出（仅 ERROR 级别以上）
    logger.add(
        sys.stderr,
        format=log_format,
        level="ERROR",
        filter=SensitiveFilter(),
        colorize=True if log_config.format == "text" else False
    )
    
    # 添加文件输出（带轮转）
    # loguru的retention参数使用整数表示保留的文件数量
    logger.add(
        log_config.file,
        format=log_format,
        level=log_config.level,
        rotation=f"{log_config.max_size} MB",  # 文件大小达到 max_size MB 时轮转
        retention=log_config.backup_count,  # 保留 backup_count 个备份文件
        compression="zip",  # 压缩旧日志文件
        encoding="utf-8",
        filter=SensitiveFilter(),  # 应用敏感信息过滤器
        backtrace=True,  # 显示完整的错误堆栈
        diagnose=True,  # 显示变量值（仅在开发环境）
    )
    
    logger.info("日志系统初始化成功")
    logger.info(f"日志级别: {log_config.level}")
    logger.info(f"日志格式: {log_config.format}")
    logger.info(f"日志文件: {log_config.file}")
    logger.info(f"最大文件大小: {log_config.max_size} MB")
    logger.info(f"保留备份数: {log_config.backup_count}")


def get_logger():
    """
    获取 logger 实例
    
    Returns:
        logger: loguru logger 实例
    """
    return logger


# 初始化日志系统（模块加载时）
try:
    setup_logger()
except Exception as e:
    # 如果配置加载失败，使用默认配置
    print(f"日志系统初始化警告: {e}")
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
