"""
工具信息库管理 API 路由
Knowledge base (tool info store) API routes
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from src.database import get_db
from src.logger import get_logger
from src.models import ComplianceReport, Tool

logger = get_logger()
router = APIRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])


@router.get("", response_model=Dict[str, Any])
async def list_knowledge_base_entries(
    limit: int = Query(1000, ge=1, le=10000, description="返回数量限制"),
    order_by: str = Query("tool_name", description="排序字段: tool_name/updated_at"),
    db: Session = Depends(get_db),
):
    """列出所有知识库条目"""
    try:
        from src.services.knowledge_base_service import list_all_knowledge_base_entries, knowledge_base_entry_to_dict

        entries = list_all_knowledge_base_entries(db, limit, order_by)
        return {
            "total": len(entries),
            "entries": [{"tool_name": e.tool_name, "data": knowledge_base_entry_to_dict(e)} for e in entries],
        }
    except Exception as e:
        logger.error(f"列出知识库条目失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="列出知识库条目失败，请查看服务端日志")


@router.get("/{tool_name}", response_model=Dict[str, Any])
async def get_knowledge_base_entry(tool_name: str, db: Session = Depends(get_db)):
    """获取工具信息库条目"""
    try:
        from src.services.knowledge_base_service import get_knowledge_base_dict

        kb_data = get_knowledge_base_dict(db, tool_name)
        if not kb_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"工具信息库中不存在工具: {tool_name}")
        return {"tool_name": tool_name, "data": kb_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具信息库条目失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取工具信息库条目失败，请查看服务端日志")


@router.get("/{tool_name}/detail", response_model=Dict[str, Any])
async def get_kb_detail_for_display(tool_name: str, db: Session = Depends(get_db)):
    """获取知识库条目的详细信息（用于前端展示）"""
    try:
        from src.services.knowledge_base_service import get_knowledge_base_dict

        kb_data = get_knowledge_base_dict(db, tool_name)
        if not kb_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"知识库中不存在工具: {tool_name}")
        license_info = {"license_type": kb_data.get("license_type"), "license_version": kb_data.get("license_version"), "license_mode": kb_data.get("license_mode")}
        company_info = {"company_name": kb_data.get("company_name"), "company_country": kb_data.get("company_country"), "company_headquarters": kb_data.get("company_headquarters"), "china_office": kb_data.get("china_office")}
        commercial_restrictions = {
            "commercial_license_required": kb_data.get("commercial_license_required"),
            "free_for_commercial": kb_data.get("free_for_commercial"),
            "restrictions": kb_data.get("commercial_restrictions"),
            "user_limit": kb_data.get("user_limit"),
            "feature_restrictions": kb_data.get("feature_restrictions"),
        }
        alternative_tools = kb_data.get("alternative_tools", [])
        if not isinstance(alternative_tools, list):
            alternative_tools = []
        return {
            "tool_name": tool_name,
            "license_info": license_info,
            "company_info": company_info,
            "commercial_restrictions": commercial_restrictions,
            "alternative_tools": alternative_tools[:2],
            "source": kb_data.get("source"),
            "updated_at": kb_data.get("updated_at"),
            "updated_by": kb_data.get("updated_by"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库详情失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取知识库详情失败，请查看服务端日志")


@router.put("/{tool_name}", response_model=Dict[str, Any])
async def update_knowledge_base_entry(tool_name: str, data: Dict[str, Any], db: Session = Depends(get_db)):
    """创建或更新工具知识库条目"""
    try:
        from src.services.knowledge_base_service import create_or_update_knowledge_base, knowledge_base_entry_to_dict

        entry = create_or_update_knowledge_base(db=db, tool_name=tool_name, data=data, source="user", updated_by="user")
        return {"tool_name": tool_name, "data": knowledge_base_entry_to_dict(entry), "message": "知识库条目已更新"}
    except Exception as e:
        logger.error(f"更新知识库条目失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新知识库条目失败，请查看服务端日志")


@router.delete("/{tool_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base_entry_route(tool_name: str, db: Session = Depends(get_db)):
    """删除工具知识库条目"""
    try:
        from src.services.knowledge_base_service import delete_knowledge_base_entry

        success = delete_knowledge_base_entry(db, tool_name)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"知识库中不存在工具: {tool_name}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库条目失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除知识库条目失败，请查看服务端日志")


@router.post("/{tool_name}/create-from-report", response_model=Dict[str, Any])
async def create_kb_from_report(
    tool_name: str,
    report_id: int = Query(..., description="报告ID"),
    db: Session = Depends(get_db),
):
    """从报告结果创建新的知识库记录（用户确认后）"""
    try:
        from src.services.knowledge_base_service import create_or_update_knowledge_base, knowledge_base_entry_to_dict
        from src.services.knowledge_base_service import get_knowledge_base_entry as _get_kb_entry
        from src.services.kb_diff_service import prepare_kb_data_from_tos_analysis

        existing_entry = _get_kb_entry(db, tool_name)
        if existing_entry:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"工具信息库中已存在工具: {tool_name}，请使用更新接口")
        report = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"报告不存在: ID {report_id}")
        tos_analysis = json.loads(report.tos_analysis) if report.tos_analysis else {}
        if not tos_analysis:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="报告中没有TOS分析数据")
        kb_data = prepare_kb_data_from_tos_analysis(tos_analysis)
        entry = create_or_update_knowledge_base(db=db, tool_name=tool_name, data=kb_data, source="ai", updated_by="user")
        logger.info(f"用户确认创建工具信息库条目: {tool_name} (报告ID: {report_id})")
        return {"message": "工具信息库记录创建成功", "tool_name": tool_name, "data": knowledge_base_entry_to_dict(entry)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从报告创建知识库失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="从报告创建知识库失败，请查看服务端日志")


@router.post("/{tool_name}/update-from-report", response_model=Dict[str, Any])
async def update_kb_from_report(
    tool_name: str,
    report_id: int = Query(..., description="报告ID"),
    db: Session = Depends(get_db),
):
    """从报告结果更新工具信息库"""
    try:
        from src.services.knowledge_base_service import create_or_update_knowledge_base, knowledge_base_entry_to_dict
        from src.services.kb_diff_service import prepare_kb_data_from_tos_analysis

        report = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"报告不存在: ID {report_id}")
        tos_analysis = json.loads(report.tos_analysis) if report.tos_analysis else {}
        if not tos_analysis:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="报告中没有TOS分析数据")
        kb_data = prepare_kb_data_from_tos_analysis(tos_analysis)
        entry = create_or_update_knowledge_base(db=db, tool_name=tool_name, data=kb_data, source="ai", updated_by="user")
        logger.info(f"从报告更新知识库: {tool_name} (报告ID: {report_id})")
        return {"message": "知识库更新成功", "tool_name": tool_name, "data": knowledge_base_entry_to_dict(entry)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从报告更新知识库失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="从报告更新知识库失败，请查看服务端日志")
