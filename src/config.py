"""
配置管理模块
Configuration management module
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml
from pydantic import BaseModel, Field, validator
from typing import Optional as TypingOptional
from pydantic_settings import BaseSettings


class ServiceConfig(BaseModel):
    """服务配置"""
    name: str = "tool-compliance-scanning-agent"
    version: str = "1.0.0"
    port: int = 8080
    host: str = "0.0.0.0"
    debug: bool = False


class GLMConfig(BaseModel):
    """GLM AI 配置"""
    api_base: str = "https://open.bigmodel.cn/api/paas/v4"
    api_key: str = ""
    model: str = "glm-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30


class OpenAIConfig(BaseModel):
    """OpenAI 配置"""
    api_base: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30


class AzureConfig(BaseModel):
    """Azure OpenAI 配置"""
    api_base: str = ""
    api_key: str = ""
    api_version: str = "2024-02-15-preview"
    deployment_name: str = ""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30


class LocalModelConfig(BaseModel):
    """本地模型配置"""
    api_base: str = "http://localhost:11434/v1"
    api_key: str = ""
    model: str = "llama2"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60


class AIConfig(BaseModel):
    """AI 大模型配置"""
    provider: str = "glm"  # glm, openai, azure, local
    default_model: str = "glm-4"
    glm: Optional[GLMConfig] = None
    openai: Optional[OpenAIConfig] = None
    azure: Optional[AzureConfig] = None
    local: Optional[LocalModelConfig] = None

    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['glm', 'openai', 'azure', 'local']
        if v not in allowed:
            raise ValueError(f'provider must be one of {allowed}')
        return v


class ComplianceScoringConfig(BaseModel):
    """合规评分权重配置"""
    security: float = 0.4
    license: float = 0.3
    maintenance: float = 0.2
    performance: float = 0.1
    tos: float = 0.0  # TOS 合规性权重（可选）

    @validator('*')
    def validate_weights(cls, v):
        if v < 0 or v > 1:
            raise ValueError('weights must be between 0 and 1')
        return v


class ComplianceConfig(BaseModel):
    """合规规则引擎配置"""
    standards: List[str] = ["ISO27001", "SOC2", "GDPR", "等保2.0", "企业内控标准"]
    scoring: ComplianceScoringConfig = Field(default_factory=ComplianceScoringConfig)
    rules_path: str = "./rules"
    alternatives_db: str = "./data/alternatives.json"
    # 是否启用多维度合规评估（暂时禁用以提升性能）
    enable_multi_dimension_assessment: bool = False


class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: str = "sqlite"  # sqlite, mysql
    path: str = "./data/compliance.db"
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None

    @validator('type')
    def validate_type(cls, v):
        allowed = ['sqlite', 'mysql']
        if v not in allowed:
            raise ValueError(f'database type must be one of {allowed}')
        return v


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    format: str = "json"  # json, text
    file: str = "./logs/app.log"
    max_size: int = 10  # MB
    backup_count: int = 5

    @validator('level')
    def validate_level(cls, v):
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        if v.upper() not in allowed:
            raise ValueError(f'log level must be one of {allowed}')
        return v.upper()

    @validator('format')
    def validate_format(cls, v):
        allowed = ['json', 'text']
        if v not in allowed:
            raise ValueError(f'log format must be one of {allowed}')
        return v


class WSLConfig(BaseModel):
    """WSL 环境配置"""
    base_path: str = "/mnt/d/Projects/tool compliance scanning agent"


class CloudConfig(BaseModel):
    """云平台配置"""
    region: str = ""
    instance_type: str = ""
    storage_type: str = ""


class DeploymentConfig(BaseModel):
    """部署配置"""
    environment: str = "local_wsl"  # local_wsl, cloud_aliyun, cloud_tencent, cloud_huawei
    wsl: Optional[WSLConfig] = None
    cloud: Optional[CloudConfig] = None


class CORSConfig(BaseModel):
    """CORS 配置"""
    enabled: bool = True
    allowed_origins: List[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]


class SecurityConfig(BaseModel):
    """安全配置"""
    enable_auth: bool = False
    api_key: Optional[str] = None
    session_timeout: int = 3600  # 秒


class WebConfig(BaseModel):
    """Web 服务配置"""
    access_mode: str = "browser_only"  # browser_only, api_enabled
    cors: CORSConfig = Field(default_factory=CORSConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    @validator('access_mode')
    def validate_access_mode(cls, v):
        allowed = ['browser_only', 'api_enabled']
        if v not in allowed:
            raise ValueError(f'access_mode must be one of {allowed}')
        return v


class RetryConfig(BaseModel):
    """重试配置"""
    max_attempts: int = 3
    backoff_factor: int = 2


class ScanningConfig(BaseModel):
    """扫描任务配置"""
    max_concurrent: int = 5
    timeout: int = 300  # 秒
    retry: RetryConfig = Field(default_factory=RetryConfig)


class ReportingConfig(BaseModel):
    """报告生成配置"""
    formats: List[str] = ["json", "html", "pdf"]
    output_path: str = "./reports"
    retention_days: int = 90


class AppConfig(BaseModel):
    """应用配置主类"""
    service: ServiceConfig = Field(default_factory=ServiceConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    scanning: ScanningConfig = Field(default_factory=ScanningConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，如果为 None，则尝试从以下位置查找：
            1. config/config.yaml
            2. 环境变量 CONFIG_PATH
            3. 使用默认配置
    
    Returns:
        AppConfig: 应用配置对象
    
    Raises:
        FileNotFoundError: 如果指定的配置文件不存在
        ValueError: 如果配置文件格式错误或验证失败
    """
    # 确定配置文件路径
    if config_path is None:
        # 尝试从环境变量获取
        config_path = os.getenv("CONFIG_PATH")
        
        # 如果环境变量也没有，尝试默认路径
        if config_path is None:
            default_paths = [
                "config/config.yaml",
                "config.yaml",
                "../config/config.yaml"
            ]
            for path in default_paths:
                if os.path.exists(path):
                    config_path = path
                    break
    
    # 如果找到了配置文件，加载它
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 使用 Pydantic 验证和解析配置
            config = AppConfig(**config_data)
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {str(e)}")
        except Exception as e:
            raise ValueError(f"配置验证失败: {str(e)}")
    else:
        # 使用默认配置
        if config_path:
            print(f"警告: 配置文件 {config_path} 不存在，使用默认配置")
        else:
            print("警告: 未找到配置文件，使用默认配置")
        return AppConfig()


# 全局配置实例
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    获取全局配置实例（单例模式）
    
    Returns:
        AppConfig: 应用配置对象
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> AppConfig:
    """
    重新加载配置
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        AppConfig: 应用配置对象
    """
    global _config
    _config = load_config(config_path)
    return _config
