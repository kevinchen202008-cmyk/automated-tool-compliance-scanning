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
    """
    敏感信息过滤器 — 用作 loguru 的 filter 参数。

    注意：loguru 的 filter 在消息格式化之前调用，修改 record["message"]
    不影响最终输出。因此这里通过 patcher 方式（在 __call__ 中修改
    record 的内部表示）并结合 ``sensitive_format`` 来实现脱敏。
    """

    def __call__(self, record):
        """在 filter 阶段标记已检查，实际脱敏由 sensitive_format 完成。"""
        return True


def sensitive_format(record):
    """
    loguru format 函数：在格式化输出时对 message 做脱敏。
    用法：logger.add(sink, format=sensitive_format)
    """
    # 先对 message 脱敏
    record["extra"]["_masked_msg"] = mask_sensitive_info(record["message"])
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{extra[_masked_msg]}</level>\n{exception}"
    )


def sensitive_format_json(record):
    """JSON 格式脱敏。"""
    record["extra"]["_masked_msg"] = mask_sensitive_info(record["message"])
    return (
        '{{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
        '"level": "{level}", '
        '"module": "{module}", '
        '"function": "{function}", '
        '"line": {line}, '
        '"message": "{extra[_masked_msg]}"}}\n'
    )


def sensitive_format_plain(record):
    """纯 {message} 格式脱敏（用于测试等简单场景）。"""
    record["extra"]["_masked_msg"] = mask_sensitive_info(record["message"])
    return "{extra[_masked_msg]}\n"


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
    
    # 选择脱敏 format 函数
    if log_config.format == "json":
        fmt_func = sensitive_format_json
    else:
        fmt_func = sensitive_format

    # 添加控制台输出（仅 ERROR 级别以上）
    logger.add(
        sys.stderr,
        format=fmt_func,
        level="ERROR",
        colorize=True if log_config.format == "text" else False,
    )

    # 添加文件输出（带轮转）
    logger.add(
        log_config.file,
        format=fmt_func,
        level=log_config.level,
        rotation=f"{log_config.max_size} MB",
        retention=log_config.backup_count,
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
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
