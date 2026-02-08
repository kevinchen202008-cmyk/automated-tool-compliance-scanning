"""
数据库模块测试
Tests for database module
"""

import pytest
import os
import tempfile
from pathlib import Path
from sqlalchemy.orm import Session
from src.database import (
    get_engine,
    get_session,
    init_database,
    check_database_exists,
    get_db
)
from src.models import Tool, ComplianceReport, AlternativeTool, Base
from src.config import reload_config, AppConfig, DatabaseConfig


def test_init_database(tmp_path):
    """测试数据库初始化"""
    # 创建临时数据库路径
    db_path = tmp_path / "test.db"
    
    # 创建临时配置
    config = AppConfig(
        database=DatabaseConfig(
            type="sqlite",
            path=str(db_path)
        )
    )
    
    # 重新加载配置（使用临时路径）
    # 注意：这里需要修改全局配置，实际测试中可能需要 mock
    init_database()
    
    # 检查数据库文件是否创建
    assert db_path.exists()


def test_create_tables(tmp_path):
    """测试表创建"""
    db_path = tmp_path / "test.db"
    
    # 初始化数据库
    from src.database import get_engine
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    # 检查表是否存在
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert "tools" in tables
    assert "compliance_reports" in tables
    assert "alternative_tools" in tables


def test_tool_model():
    """测试 Tool 模型"""
    tool = Tool(
        name="Docker",
        version="24.0.0",
        source="external",
        tos_url="https://www.docker.com/legal/terms"
    )
    
    assert tool.name == "Docker"
    assert tool.version == "24.0.0"
    assert tool.source == "external"
    assert tool.tos_url == "https://www.docker.com/legal/terms"


def test_compliance_report_model():
    """测试 ComplianceReport 模型"""
    report = ComplianceReport(
        tool_id=1,
        score_overall=85.0,
        score_security=90.0,
        score_license=80.0,
        score_maintenance=85.0,
        score_performance=80.0,
        score_tos=85.0,
        is_compliant=True,
        reasons='["无已知问题"]',
        recommendations='["继续保持"]',
        references={"ISO27001": "符合"},
        tos_analysis='{"risk_level": "low"}'
    )
    
    assert report.tool_id == 1
    assert report.score_overall == 85.0
    assert report.is_compliant is True
    assert report.score_tos == 85.0


def test_alternative_tool_model():
    """测试 AlternativeTool 模型"""
    alt_tool = AlternativeTool(
        tool_id=1,
        name="Podman",
        reason="开源替代方案",
        link="https://podman.io",
        license="Apache 2.0"
    )
    
    assert alt_tool.tool_id == 1
    assert alt_tool.name == "Podman"
    assert alt_tool.license == "Apache 2.0"


def test_foreign_key_relationship(tmp_path):
    """测试外键关系"""
    db_path = tmp_path / "test.db"
    
    # 初始化数据库
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = get_session()
    db: Session = SessionLocal()
    
    try:
        # 创建工具
        tool = Tool(
            name="Test Tool",
            version="1.0.0",
            source="external"
        )
        db.add(tool)
        db.commit()
        db.refresh(tool)
        
        # 创建合规报告
        report = ComplianceReport(
            tool_id=tool.id,
            score_overall=80.0,
            score_security=85.0,
            score_license=75.0,
            score_maintenance=80.0,
            score_performance=80.0,
            is_compliant=True
        )
        db.add(report)
        db.commit()
        
        # 创建替代工具
        alt_tool = AlternativeTool(
            tool_id=tool.id,
            name="Alternative Tool",
            reason="开源替代"
        )
        db.add(alt_tool)
        db.commit()
        
        # 验证关系
        assert len(tool.compliance_reports) == 1
        assert len(tool.alternative_tools) == 1
        assert report.tool.id == tool.id
        assert alt_tool.tool.id == tool.id
        
    finally:
        db.close()
