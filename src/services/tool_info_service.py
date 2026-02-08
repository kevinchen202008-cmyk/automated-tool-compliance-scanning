"""
工具信息获取服务
Tool information retrieval service
"""

import httpx
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models import Tool
from src.logger import get_logger

logger = get_logger()


async def fetch_tool_version(tool_name: str) -> Optional[str]:
    """
    尝试获取工具版本信息
    
    Args:
        tool_name: 工具名称
    
    Returns:
        Optional[str]: 工具版本，如果无法获取返回None
    """
    # TODO: 实现实际的版本获取逻辑
    # 可以通过以下方式：
    # 1. 调用工具的公开API
    # 2. 查询包管理器（如npm, pip, docker hub等）
    # 3. 使用搜索引擎
    
    # 目前返回None，标记为unknown
    logger.debug(f"尝试获取工具版本: {tool_name}")
    return None


def update_tool_info(db: Session, tool: Tool, version: Optional[str] = None) -> Tool:
    """
    更新工具信息
    
    Args:
        db: 数据库会话
        tool: 工具对象
        version: 工具版本（可选）
    
    Returns:
        Tool: 更新后的工具对象
    """
    if version:
        tool.version = version
    else:
        tool.version = "unknown"
    
    db.commit()
    db.refresh(tool)
    logger.info(f"更新工具信息: {tool.name} (版本: {tool.version})")
    return tool


async def get_tool_info(tool: Tool, db: Session) -> Dict[str, Any]:
    """
    获取工具的完整信息
    
    Args:
        tool: 工具对象
        db: 数据库会话
    
    Returns:
        Dict[str, Any]: 工具信息字典
    """
    # 尝试获取版本信息
    version = await fetch_tool_version(tool.name)
    
    # 更新工具信息
    updated_tool = update_tool_info(db, tool, version)
    
    return {
        "tool_id": updated_tool.id,
        "name": updated_tool.name,
        "version": updated_tool.version,
        "source": updated_tool.source,
        "tos_url": updated_tool.tos_url,
        "tos_info": updated_tool.tos_info
    }
