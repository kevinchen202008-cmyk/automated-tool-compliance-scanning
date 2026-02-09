"""
工具信息库服务：管理工具信息库数据的增删改查
Tool information store service: Manage tool information store data CRUD operations
"""

import json
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from src.models import ToolKnowledgeBase
from src.logger import get_logger

logger = get_logger()


def get_knowledge_base_entry(db: Session, tool_name: str) -> Optional[ToolKnowledgeBase]:
    """
    从数据库获取工具信息库条目
    
    Args:
        db: 数据库会话
        tool_name: 工具名称
    
    Returns:
        Optional[ToolKnowledgeBase]: 知识库条目，如果不存在返回None
    """
    # 精确匹配
    entry = db.query(ToolKnowledgeBase).filter(
        ToolKnowledgeBase.tool_name == tool_name
    ).first()
    
    if entry:
        return entry
    
    # 模糊匹配（不区分大小写）
    entry = db.query(ToolKnowledgeBase).filter(
        ToolKnowledgeBase.tool_name.ilike(tool_name)
    ).first()
    
    return entry


def knowledge_base_entry_to_dict(entry: ToolKnowledgeBase) -> Dict[str, Any]:
    """
    将工具信息库条目转换为字典格式
    
    Args:
        entry: 知识库条目
    
    Returns:
        Dict[str, Any]: 字典格式的知识库数据
    """
    return {
        "license_type": entry.license_type,
        "license_version": entry.license_version,
        "license_mode": entry.license_mode,
        "company_name": entry.company_name,
        "company_country": entry.company_country,
        "company_headquarters": entry.company_headquarters,
        "china_office": entry.china_office,
        "commercial_license_required": entry.commercial_license_required,
        "free_for_commercial": entry.free_for_commercial,
        "commercial_restrictions": entry.commercial_restrictions,
        "user_limit": entry.user_limit,
        "feature_restrictions": entry.feature_restrictions,
        "alternative_tools": entry.alternative_tools if isinstance(entry.alternative_tools, list) else json.loads(entry.alternative_tools) if entry.alternative_tools else [],
        "data_usage": entry.data_usage,
        "privacy_policy": entry.privacy_policy,
        "service_restrictions": entry.service_restrictions,
        "risk_points": entry.risk_points if isinstance(entry.risk_points, list) else json.loads(entry.risk_points) if entry.risk_points else [],
        "compliance_notes": entry.compliance_notes,
        "source": entry.source,
        "updated_by": entry.updated_by,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None
    }


def create_or_update_knowledge_base(
    db: Session,
    tool_name: str,
    data: Dict[str, Any],
    source: str = "user",
    updated_by: Optional[str] = None
) -> ToolKnowledgeBase:
    """
    创建或更新工具信息库条目
    
    Args:
        db: 数据库会话
        tool_name: 工具名称
        data: 知识库数据
        source: 数据来源（system/user/ai）
        updated_by: 更新人
    
    Returns:
        ToolKnowledgeBase: 创建或更新的知识库条目
    """
    entry = get_knowledge_base_entry(db, tool_name)
    
    if entry:
        # 更新现有条目
        entry.license_type = data.get("license_type")
        entry.license_version = data.get("license_version")
        entry.license_mode = data.get("license_mode")
        entry.company_name = data.get("company_name")
        entry.company_country = data.get("company_country")
        entry.company_headquarters = data.get("company_headquarters")
        entry.china_office = data.get("china_office")
        entry.commercial_license_required = data.get("commercial_license_required")
        entry.free_for_commercial = data.get("free_for_commercial")
        entry.commercial_restrictions = data.get("commercial_restrictions")
        entry.user_limit = data.get("user_limit")
        entry.feature_restrictions = data.get("feature_restrictions")
        entry.alternative_tools = data.get("alternative_tools", [])
        entry.data_usage = data.get("data_usage")
        entry.privacy_policy = data.get("privacy_policy")
        entry.service_restrictions = data.get("service_restrictions")
        entry.risk_points = data.get("risk_points", [])
        entry.compliance_notes = data.get("compliance_notes")
        entry.source = source
        entry.updated_by = updated_by
        logger.info(f"更新工具信息库条目: {tool_name} (来源: {source})")
    else:
        # 创建新条目
        entry = ToolKnowledgeBase(
            tool_name=tool_name,
            license_type=data.get("license_type"),
            license_version=data.get("license_version"),
            license_mode=data.get("license_mode"),
            company_name=data.get("company_name"),
            company_country=data.get("company_country"),
            company_headquarters=data.get("company_headquarters"),
            china_office=data.get("china_office"),
            commercial_license_required=data.get("commercial_license_required"),
            free_for_commercial=data.get("free_for_commercial"),
            commercial_restrictions=data.get("commercial_restrictions"),
            user_limit=data.get("user_limit"),
            feature_restrictions=data.get("feature_restrictions"),
            alternative_tools=data.get("alternative_tools", []),
            data_usage=data.get("data_usage"),
            privacy_policy=data.get("privacy_policy"),
            service_restrictions=data.get("service_restrictions"),
            risk_points=data.get("risk_points", []),
            compliance_notes=data.get("compliance_notes"),
            source=source,
            updated_by=updated_by
        )
        db.add(entry)
        logger.info(f"创建工具信息库条目: {tool_name} (来源: {source})")
    
    db.commit()
    db.refresh(entry)
    return entry


def get_knowledge_base_dict(db: Session, tool_name: str) -> Optional[Dict[str, Any]]:
    """
    从数据库获取工具信息库数据（字典格式）
    
    Args:
        db: 数据库会话
        tool_name: 工具名称
    
    Returns:
        Optional[Dict[str, Any]]: 知识库数据，如果不存在返回None
    """
    entry = get_knowledge_base_entry(db, tool_name)
    if entry:
        return knowledge_base_entry_to_dict(entry)
    return None


def list_all_knowledge_base_entries(db: Session, limit: int = 100, order_by: str = "tool_name") -> List[ToolKnowledgeBase]:
    """
    列出所有工具信息库条目
    
    Args:
        db: 数据库会话
        limit: 返回数量限制
        order_by: 排序字段（默认按工具名称）
    
    Returns:
        List[ToolKnowledgeBase]: 知识库条目列表（按字母顺序）
    """
    query = db.query(ToolKnowledgeBase)
    
    if order_by == "tool_name":
        query = query.order_by(ToolKnowledgeBase.tool_name.asc())
    elif order_by == "updated_at":
        query = query.order_by(ToolKnowledgeBase.updated_at.desc())
    
    return query.limit(limit).all()


def delete_knowledge_base_entry(db: Session, tool_name: str) -> bool:
    """
    删除工具信息库条目
    
    Args:
        db: 数据库会话
        tool_name: 工具名称
    
    Returns:
        bool: 是否删除成功
    """
    entry = get_knowledge_base_entry(db, tool_name)
    if entry:
        db.delete(entry)
        db.commit()
        logger.info(f"删除知识库条目: {tool_name}")
        return True
    return False
