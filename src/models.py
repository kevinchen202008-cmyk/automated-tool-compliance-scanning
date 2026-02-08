"""
数据模型定义
Database models definition
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, 
    ForeignKey, DateTime, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class Tool(Base):
    """工具表"""
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True, comment="工具名称")
    version = Column(String(100), nullable=True, comment="工具版本")
    source = Column(String(50), nullable=False, default="unknown", comment="工具来源: internal/external/unknown")
    tos_info = Column(Text, nullable=True, comment="TOS 信息和分析结果（JSON格式）")
    tos_url = Column(String(500), nullable=True, comment="TOS 文档链接")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    compliance_reports = relationship("ComplianceReport", back_populates="tool", cascade="all, delete-orphan")
    alternative_tools = relationship("AlternativeTool", back_populates="tool", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', version='{self.version}')>"


class ComplianceReport(Base):
    """合规报告表"""
    __tablename__ = "compliance_reports"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True, comment="工具ID")
    # 评分字段改为可空，支持简化模式（仅TOS分析和替代方案，不进行多维度评估）
    score_overall = Column(Float, nullable=True, comment="综合合规评分（简化模式下为NULL）")
    score_security = Column(Float, nullable=True, comment="安全性评分（简化模式下为NULL）")
    score_license = Column(Float, nullable=True, comment="许可证合规评分（简化模式下为NULL）")
    score_maintenance = Column(Float, nullable=True, comment="维护性评分（简化模式下为NULL）")
    score_performance = Column(Float, nullable=True, comment="性能/稳定性评分（简化模式下为NULL）")
    score_tos = Column(Float, nullable=True, comment="TOS 合规性评分（简化模式下为NULL）")
    is_compliant = Column(Boolean, nullable=True, comment="是否合规（简化模式下为NULL）")
    reasons = Column(Text, nullable=True, comment="不合规原因列表（JSON格式）")
    recommendations = Column(Text, nullable=True, comment="合规建议（JSON格式）")
    references = Column(JSON, nullable=True, comment="合规性参考（JSON格式）")
    tos_analysis = Column(Text, nullable=True, comment="TOS 分析结果（JSON格式）")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    tool = relationship("Tool", back_populates="compliance_reports")
    
    def __repr__(self):
        return f"<ComplianceReport(id={self.id}, tool_id={self.tool_id}, score_overall={self.score_overall}, is_compliant={self.is_compliant})>"


class AlternativeTool(Base):
    """开源替代工具表"""
    __tablename__ = "alternative_tools"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True, comment="原工具ID")
    name = Column(String(255), nullable=False, comment="替代工具名称")
    reason = Column(Text, nullable=True, comment="推荐理由")
    link = Column(String(500), nullable=True, comment="工具链接")
    license = Column(String(100), nullable=True, comment="许可证类型")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关系
    tool = relationship("Tool", back_populates="alternative_tools")
    
    def __repr__(self):
        return f"<AlternativeTool(id={self.id}, tool_id={self.tool_id}, name='{self.name}')>"


class ToolKnowledgeBase(Base):
    """工具知识库表（用户可更新）"""
    __tablename__ = "tool_knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tool_name = Column(String(255), nullable=False, unique=True, index=True, comment="工具名称（唯一）")
    license_type = Column(String(100), nullable=True, comment="许可证类型")
    license_version = Column(String(50), nullable=True, comment="许可证版本")
    license_mode = Column(String(50), nullable=True, comment="许可证模式（开源/商业/混合）")
    company_name = Column(String(255), nullable=True, comment="公司名称（开源工具为null）")
    company_country = Column(String(100), nullable=True, comment="公司所属国家")
    company_headquarters = Column(String(255), nullable=True, comment="公司总部")
    china_office = Column(Boolean, nullable=True, comment="是否有中国分公司或服务")
    commercial_license_required = Column(Boolean, nullable=True, comment="商业用户是否必须购买license")
    free_for_commercial = Column(Boolean, nullable=True, comment="是否允许免费商业使用")
    commercial_restrictions = Column(Text, nullable=True, comment="商用用户使用的具体限制说明")
    user_limit = Column(String(255), nullable=True, comment="用户数量限制")
    feature_restrictions = Column(Text, nullable=True, comment="功能限制说明")
    alternative_tools = Column(JSON, nullable=True, comment="替代工具列表（JSON格式）")
    data_usage = Column(Text, nullable=True, comment="数据使用政策说明")
    privacy_policy = Column(Text, nullable=True, comment="隐私政策说明")
    service_restrictions = Column(Text, nullable=True, comment="服务限制说明")
    risk_points = Column(JSON, nullable=True, comment="合规风险点列表（JSON格式）")
    compliance_notes = Column(Text, nullable=True, comment="合规性备注")
    source = Column(String(50), nullable=False, default="user", comment="数据来源: system/user/ai")
    updated_by = Column(String(100), nullable=True, comment="最后更新人")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<ToolKnowledgeBase(id={self.id}, tool_name='{self.tool_name}', source='{self.source}')>"
