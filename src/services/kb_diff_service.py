"""
知识库差异对比服务
Knowledge base diff service for comparing new scan results with existing KB entries
"""

import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from src.services.knowledge_base_service import get_knowledge_base_dict
from src.logger import get_logger

logger = get_logger()


def compare_kb_data(
    new_data: Dict[str, Any],
    existing_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    对比新数据和现有知识库数据的差异
    
    Args:
        new_data: 新的扫描结果数据
        existing_data: 现有的知识库数据
    
    Returns:
        Dict[str, Any]: 差异对比结果，包含：
            - has_changes: 是否有差异
            - changes: 差异详情列表
            - summary: 差异摘要
    """
    changes = []
    
    # 定义需要对比的字段
    fields_to_compare = [
        ("license_type", "许可证类型"),
        ("license_version", "许可证版本"),
        ("license_mode", "许可证模式"),
        ("company_name", "公司名称"),
        ("company_country", "公司所属国家"),
        ("company_headquarters", "公司总部"),
        ("china_office", "是否有中国服务"),
        ("commercial_license_required", "商业用户是否需购买license"),
        ("free_for_commercial", "是否允许免费商用"),
        ("commercial_restrictions", "商用限制"),
        ("user_limit", "用户数量限制"),
        ("feature_restrictions", "功能限制"),
        ("alternative_tools", "替代工具"),
        ("data_usage", "数据使用政策"),
        ("privacy_policy", "隐私政策"),
        ("service_restrictions", "服务限制"),
        ("risk_points", "合规风险点"),
        ("compliance_notes", "合规备注"),
    ]
    
    for field_key, field_label in fields_to_compare:
        old_value = existing_data.get(field_key)
        new_value = new_data.get(field_key)
        
        # 处理特殊类型
        if field_key in ["alternative_tools", "risk_points"]:
            # JSON字段（列表），转换为JSON字符串比较，避免字典比较错误
            try:
                # 确保值是列表
                old_list = old_value if isinstance(old_value, list) else (old_value if old_value else [])
                new_list = new_value if isinstance(new_value, list) else (new_value if new_value else [])
                
                # 转换为JSON字符串进行比较（排序后比较，确保顺序不影响结果）
                old_json = json.dumps(sorted(old_list, key=lambda x: json.dumps(x, sort_keys=True) if isinstance(x, dict) else str(x)), sort_keys=True, ensure_ascii=False)
                new_json = json.dumps(sorted(new_list, key=lambda x: json.dumps(x, sort_keys=True) if isinstance(x, dict) else str(x)), sort_keys=True, ensure_ascii=False)
                
                if old_json != new_json:
                    changes.append({
                        "field": field_key,
                        "field_label": field_label,
                        "old_value": old_value,
                        "new_value": new_value,
                        "change_type": "modified"
                    })
            except (TypeError, ValueError) as e:
                # 如果转换失败，使用简单的字符串比较
                logger.warning(f"比较 {field_key} 时出错: {e}，使用简单字符串比较")
                old_str = json.dumps(old_value, sort_keys=True, ensure_ascii=False) if old_value else ""
                new_str = json.dumps(new_value, sort_keys=True, ensure_ascii=False) if new_value else ""
                if old_str != new_str:
                    changes.append({
                        "field": field_key,
                        "field_label": field_label,
                        "old_value": old_value,
                        "new_value": new_value,
                        "change_type": "modified"
                    })
        elif field_key == "china_office":
            # 布尔值比较
            if old_value != new_value:
                changes.append({
                    "field": field_key,
                    "field_label": field_label,
                    "old_value": old_value,
                    "new_value": new_value,
                    "change_type": "modified"
                })
        else:
            # 字符串比较（处理None和空字符串）
            old_str = str(old_value) if old_value is not None else ""
            new_str = str(new_value) if new_value is not None else ""
            
            # 如果旧值为空但新值不为空，视为新增
            if not old_str and new_str:
                changes.append({
                    "field": field_key,
                    "field_label": field_label,
                    "old_value": old_value,
                    "new_value": new_value,
                    "change_type": "added"
                })
            # 如果旧值不为空但新值为空，视为删除（但通常不会发生）
            elif old_str and not new_str:
                changes.append({
                    "field": field_key,
                    "field_label": field_label,
                    "old_value": old_value,
                    "new_value": new_value,
                    "change_type": "removed"
                })
            # 如果两者都不为空且不同，视为修改
            elif old_str and new_str and old_str != new_str:
                changes.append({
                    "field": field_key,
                    "field_label": field_label,
                    "old_value": old_value,
                    "new_value": new_value,
                    "change_type": "modified"
                })
    
    # 生成摘要
    summary = f"发现 {len(changes)} 处差异"
    if changes:
        modified_count = sum(1 for c in changes if c["change_type"] == "modified")
        added_count = sum(1 for c in changes if c["change_type"] == "added")
        removed_count = sum(1 for c in changes if c["change_type"] == "removed")
        summary_parts = []
        if modified_count > 0:
            summary_parts.append(f"{modified_count} 处修改")
        if added_count > 0:
            summary_parts.append(f"{added_count} 处新增")
        if removed_count > 0:
            summary_parts.append(f"{removed_count} 处删除")
        summary = "，".join(summary_parts)
    
    return {
        "has_changes": len(changes) > 0,
        "changes": changes,
        "summary": summary,
        "change_count": len(changes)
    }


def prepare_kb_data_from_tos_analysis(
    tos_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    从TOS分析结果中提取知识库数据格式
    
    Args:
        tos_analysis: TOS分析结果
    
    Returns:
        Dict[str, Any]: 知识库数据格式
    """
    return {
        "license_type": tos_analysis.get("license_type"),
        "license_version": tos_analysis.get("license_version"),
        "license_mode": tos_analysis.get("license_mode"),
        "company_name": tos_analysis.get("company_name"),
        "company_country": tos_analysis.get("company_country"),
        "company_headquarters": tos_analysis.get("company_headquarters"),
        "china_office": tos_analysis.get("china_office"),
        "commercial_license_required": tos_analysis.get("commercial_license_required"),
        "free_for_commercial": tos_analysis.get("free_for_commercial"),
        "commercial_restrictions": tos_analysis.get("commercial_restrictions"),
        "user_limit": tos_analysis.get("user_limit"),
        "feature_restrictions": tos_analysis.get("feature_restrictions"),
        "alternative_tools": tos_analysis.get("alternative_tools", []),
        "data_usage": tos_analysis.get("data_usage"),
        "privacy_policy": tos_analysis.get("privacy_policy"),
        "service_restrictions": tos_analysis.get("service_restrictions"),
        "risk_points": tos_analysis.get("risk_points", []),
        "compliance_notes": tos_analysis.get("compliance_notes"),
    }


def check_and_prepare_kb_update(
    tool_name: str,
    tos_analysis: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """
    检查知识库并准备更新信息
    
    Args:
        tool_name: 工具名称
        tos_analysis: TOS分析结果
        db: 数据库会话
    
    Returns:
        Dict[str, Any]: 包含以下信息：
            - exists: 知识库中是否存在该工具
            - kb_entry: 现有知识库条目（如果存在）
            - new_data: 新数据
            - diff: 差异对比结果（如果存在）
            - should_auto_create: 是否应该自动创建（不存在时）
    """
    # 准备新数据
    new_data = prepare_kb_data_from_tos_analysis(tos_analysis)
    
    # 检查知识库中是否存在
    existing_data = get_knowledge_base_dict(db, tool_name)
    
    result = {
        "exists": existing_data is not None,
        "new_data": new_data,
        "should_auto_create": False,
        "diff": None,
        "kb_entry": existing_data
    }
    
    if existing_data:
        # 存在，进行差异对比
        diff = compare_kb_data(new_data, existing_data)
        result["diff"] = diff
        logger.info(f"知识库条目已存在: {tool_name}，发现 {diff['change_count']} 处差异")
    else:
        # 不存在，标记为应该自动创建
        result["should_auto_create"] = True
        logger.info(f"知识库条目不存在: {tool_name}，将自动创建")
    
    return result
