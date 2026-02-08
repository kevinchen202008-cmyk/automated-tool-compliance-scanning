"""
日志系统模块测试
Tests for logging system
"""

import pytest
import os
import tempfile
from pathlib import Path
from loguru import logger
from src.logger import (
    setup_logger,
    get_logger,
    mask_sensitive_info,
    SensitiveFilter
)


def test_mask_sensitive_info():
    """测试敏感信息屏蔽功能"""
    # 测试 API Key
    message1 = 'api_key: "sk-1234567890abcdef"'
    masked1 = mask_sensitive_info(message1)
    assert "sk-1234567890abcdef" not in masked1
    assert "***" in masked1
    
    # 测试 password
    message2 = 'password: "mypassword123"'
    masked2 = mask_sensitive_info(message2)
    assert "mypassword123" not in masked2
    assert "***" in masked2
    
    # 测试 token
    message3 = 'token="abc123xyz"'
    masked3 = mask_sensitive_info(message3)
    assert "abc123xyz" not in masked3
    assert "***" in masked3
    
    # 测试普通消息（不应被修改）
    message4 = "这是一条普通日志消息"
    masked4 = mask_sensitive_info(message4)
    assert masked4 == message4


def test_sensitive_filter():
    """测试敏感信息过滤器"""
    filter_obj = SensitiveFilter()
    
    # 创建模拟的日志记录
    class MockRecord:
        def __init__(self, message):
            self.message = message
    
    record1 = MockRecord('api_key: "secret123"')
    result1 = filter_obj(record1)
    assert result1 is True
    assert "secret123" not in str(record1.message)
    
    record2 = MockRecord("普通消息")
    result2 = filter_obj(record2)
    assert result2 is True
    assert record2.message == "普通消息"


def test_logger_initialization(tmp_path):
    """测试日志系统初始化"""
    # 创建临时日志文件路径
    log_file = tmp_path / "test.log"
    
    # 临时修改环境变量或配置，使用临时路径
    # 注意：这里需要确保 setup_logger 能使用临时路径
    # 由于 setup_logger 从 config 读取，我们需要先设置好配置
    
    # 获取 logger 实例
    logger_instance = get_logger()
    assert logger_instance is not None


def test_logger_output(tmp_path, monkeypatch):
    """测试日志输出功能"""
    # 创建临时日志文件
    log_file = tmp_path / "test_output.log"
    
    # 移除所有现有的 handlers
    logger.remove()
    
    # 添加临时文件 handler
    logger.add(
        str(log_file),
        format="{time} | {level} | {message}",
        level="DEBUG"
    )
    
    # 测试不同级别的日志
    logger.debug("这是一条 DEBUG 日志")
    logger.info("这是一条 INFO 日志")
    logger.warning("这是一条 WARNING 日志")
    logger.error("这是一条 ERROR 日志")
    
    # 确保日志文件被创建
    assert log_file.exists()
    
    # 读取日志文件内容
    log_content = log_file.read_text(encoding="utf-8")
    
    # 验证日志内容
    assert "DEBUG" in log_content
    assert "INFO" in log_content
    assert "WARNING" in log_content
    assert "ERROR" in log_content
    assert "这是一条 DEBUG 日志" in log_content
    assert "这是一条 INFO 日志" in log_content


def test_logger_sensitive_info_filtering(tmp_path):
    """测试日志中的敏感信息过滤"""
    # 创建临时日志文件
    log_file = tmp_path / "test_sensitive.log"
    
    # 移除所有现有的 handlers
    logger.remove()
    
    # 添加带敏感信息过滤器的 handler
    logger.add(
        str(log_file),
        format="{message}",
        level="DEBUG",
        filter=SensitiveFilter()
    )
    
    # 记录包含敏感信息的日志
    logger.info('api_key: "sk-1234567890"')
    logger.info('password: "mypassword"')
    logger.info("普通消息，不包含敏感信息")
    
    # 读取日志文件
    log_content = log_file.read_text(encoding="utf-8")
    
    # 验证敏感信息被屏蔽
    assert "sk-1234567890" not in log_content
    assert "mypassword" not in log_content
    assert "***" in log_content
    assert "普通消息，不包含敏感信息" in log_content


def test_get_logger():
    """测试获取 logger 实例"""
    logger_instance = get_logger()
    assert logger_instance is not None
    # 验证可以调用 logger 方法
    logger_instance.info("测试日志")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
