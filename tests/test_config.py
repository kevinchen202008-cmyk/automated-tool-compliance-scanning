"""
配置管理模块测试
Tests for configuration management
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from src.config import (
    load_config,
    get_config,
    reload_config,
    AppConfig,
    ServiceConfig,
    AIConfig,
    ComplianceConfig,
    DatabaseConfig,
    LoggingConfig,
    DeploymentConfig,
    WebConfig,
    ScanningConfig,
    ReportingConfig
)


def test_default_config():
    """测试默认配置"""
    config = AppConfig()
    
    assert config.service.name == "tool-compliance-scanning-agent"
    assert config.service.port == 8080
    assert config.ai.provider == "glm"
    assert config.database.type == "sqlite"
    assert config.logging.level == "INFO"


def test_load_config_from_file():
    """测试从文件加载配置"""
    # 创建临时配置文件
    config_data = {
        "service": {
            "name": "test-service",
            "port": 9000,
            "host": "127.0.0.1"
        },
        "ai": {
            "provider": "glm",
            "glm": {
                "api_key": "test-key"
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        assert config.service.name == "test-service"
        assert config.service.port == 9000
        assert config.service.host == "127.0.0.1"
    finally:
        os.unlink(temp_path)


def test_load_config_not_found():
    """测试配置文件不存在时使用默认配置"""
    config = load_config("non_existent_config.yaml")
    assert isinstance(config, AppConfig)
    assert config.service.name == "tool-compliance-scanning-agent"


def test_config_validation():
    """测试配置验证"""
    # 测试无效的 provider
    with pytest.raises(ValueError):
        AIConfig(provider="invalid_provider")
    
    # 测试无效的数据库类型
    with pytest.raises(ValueError):
        DatabaseConfig(type="invalid_type")
    
    # 测试无效的日志级别
    with pytest.raises(ValueError):
        LoggingConfig(level="INVALID")


def test_get_config_singleton():
    """测试配置单例模式"""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2


def test_reload_config():
    """测试重新加载配置"""
    # 创建临时配置文件
    config_data = {
        "service": {
            "port": 9000
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = reload_config(temp_path)
        assert config.service.port == 9000
    finally:
        os.unlink(temp_path)


def test_config_all_sections():
    """测试所有配置块都能正确加载"""
    config = AppConfig()
    
    # 验证所有配置块都存在
    assert isinstance(config.service, ServiceConfig)
    assert isinstance(config.ai, AIConfig)
    assert isinstance(config.compliance, ComplianceConfig)
    assert isinstance(config.database, DatabaseConfig)
    assert isinstance(config.logging, LoggingConfig)
    assert isinstance(config.deployment, DeploymentConfig)
    assert isinstance(config.web, WebConfig)
    assert isinstance(config.scanning, ScanningConfig)
    assert isinstance(config.reporting, ReportingConfig)
