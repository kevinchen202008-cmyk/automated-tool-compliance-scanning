"""
工具服务模块
Tool service module for managing tools
"""

import re
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.models import Tool
from src.logger import get_logger

logger = get_logger()


def validate_tool_name(tool_name: str) -> tuple[bool, Optional[str]]:
    """
    验证工具名是否有效
    
    Args:
        tool_name: 工具名称
    
    Returns:
        tuple: (是否有效, 错误信息)
    """
    if not tool_name:
        return False, "工具名不能为空"
    
    # 去除首尾空格
    tool_name = tool_name.strip()
    
    if not tool_name:
        return False, "工具名不能只包含空格"
    
    # 检查长度（1-100字符）
    if len(tool_name) > 100:
        return False, "工具名长度不能超过100个字符"
    
    # 检查字符（允许字母、数字、连字符、下划线、点、空格）
    if not re.match(r'^[a-zA-Z0-9_\-\.\s]+$', tool_name):
        return False, "工具名只能包含字母、数字、连字符、下划线、点和空格"
    
    return True, None


def get_or_create_tool(db: Session, tool_name: str, source: str = "unknown") -> Tool:
    """
    获取或创建工具记录
    
    Args:
        db: 数据库会话
        tool_name: 工具名称
        source: 工具来源（internal/external/unknown）
    
    Returns:
        Tool: 工具对象
    """
    # 验证工具名
    is_valid, error_msg = validate_tool_name(tool_name)
    if not is_valid:
        raise ValueError(error_msg)
    
    # 规范化工具名（去除首尾空格，转换为小写用于查找）
    normalized_name = tool_name.strip()
    
    # 尝试查找现有工具（不区分大小写）
    tool = db.query(Tool).filter(
        Tool.name.ilike(normalized_name)
    ).first()
    
    if tool:
        logger.info(f"找到现有工具: {tool.name} (ID: {tool.id})")
        return tool
    
    # 创建新工具
    try:
        tool = Tool(
            name=normalized_name,
            source=source,
            version=None
        )
        db.add(tool)
        db.commit()
        db.refresh(tool)
        logger.info(f"创建新工具: {tool.name} (ID: {tool.id})")
        return tool
    except IntegrityError as e:
        db.rollback()
        logger.error(f"创建工具失败: {e}")
        # 如果因为并发创建导致冲突，再次尝试查找
        tool = db.query(Tool).filter(
            Tool.name.ilike(normalized_name)
        ).first()
        if tool:
            return tool
        raise ValueError(f"创建工具失败: {e}")


def get_tool_by_id(db: Session, tool_id: int) -> Optional[Tool]:
    """
    根据ID获取工具
    
    Args:
        db: 数据库会话
        tool_id: 工具ID
    
    Returns:
        Tool: 工具对象，如果不存在返回None
    """
    return db.query(Tool).filter(Tool.id == tool_id).first()


def get_tool_by_name(db: Session, tool_name: str) -> Optional[Tool]:
    """
    根据名称获取工具
    
    Args:
        db: 数据库会话
        tool_name: 工具名称
    
    Returns:
        Tool: 工具对象，如果不存在返回None
    """
    normalized_name = tool_name.strip()
    return db.query(Tool).filter(
        Tool.name.ilike(normalized_name)
    ).first()


def parse_tool_names(input_text: str) -> list[str]:
    """
    解析多个工具名（支持换行分隔或逗号分隔）
    
    Args:
        input_text: 输入文本（可以是多行或逗号分隔）
    
    Returns:
        list[str]: 解析后的工具名列表
    """
    if not input_text:
        return []
    
    # 先按换行分割
    lines = input_text.split('\n')
    tool_names = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 如果行中包含逗号，按逗号分割
        if ',' in line:
            parts = [part.strip() for part in line.split(',')]
            tool_names.extend([p for p in parts if p])
        else:
            tool_names.append(line)
    
    # 去重并保持顺序
    seen = set()
    unique_tools = []
    for tool_name in tool_names:
        normalized = tool_name.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_tools.append(tool_name.strip())
    
    return unique_tools


def batch_create_tools(db: Session, tool_names: list[str], source: str = "unknown") -> tuple[list[Tool], int]:
    """
    批量创建或获取工具记录
    
    Args:
        db: 数据库会话
        tool_names: 工具名称列表
        source: 工具来源（internal/external/unknown）
    
    Returns:
        tuple[list[Tool], int]: (工具对象列表, 已存在的工具数量)
    """
    tools = []
    existing_count = 0
    errors = []
    
    for tool_name in tool_names:
        try:
            # 检查工具是否已存在
            existing_tool = get_tool_by_name(db, tool_name)
            if existing_tool:
                tools.append(existing_tool)
                existing_count += 1
            else:
                # 创建新工具
                tool = get_or_create_tool(db, tool_name, source)
                tools.append(tool)
        except ValueError as e:
            errors.append(f"工具 '{tool_name}': 名称无效")
            logger.warning(f"跳过无效工具名: {tool_name} - {e}")
        except Exception as e:
            errors.append(f"工具 '{tool_name}': 创建失败")
            logger.error(f"创建工具失败: {tool_name} - {e}")
    
    if errors:
        logger.warning(f"批量创建工具时出现 {len(errors)} 个错误")
    
    return tools, existing_count
