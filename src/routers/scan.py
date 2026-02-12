"""
扫描与报告 API 路由
Scan & report API routes
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
from src.database import get_db
from src.logger import get_logger
from src.models import Tool, ComplianceReport
from src.schemas import (
    ScanRequest,
    ScanResponse,
    ScanTaskStatusResponse,
    ComplianceScanRequest,
)
from src.services.scan_service import get_scan_service
from src.services.tool_service import batch_create_tools
from src.services.report_service import get_report_service

logger = get_logger()
router = APIRouter(tags=["scan"])


# ==================== 扫描 ====================


@router.post("/api/v1/scan/start", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(
    scan_request: ScanRequest,
    db: Session = Depends(get_db),
):
    """启动合规扫描任务"""
    try:
        scan_service = get_scan_service()
        tools = db.query(Tool).filter(Tool.id.in_(scan_request.tool_ids)).all()
        if len(tools) != len(scan_request.tool_ids):
            found_ids = {tool.id for tool in tools}
            missing_ids = set(scan_request.tool_ids) - found_ids
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"工具不存在: {missing_ids}")
        tasks = scan_service.create_scan_tasks(scan_request.tool_ids, db)
        scan_service.start()
        logger.info(f"扫描任务已启动: {len(tasks)} 个任务")
        tasks_info = [
            {"tool_id": t.tool_id, "tool_name": t.tool_name, "status": t.status.value, "report_id": None}
            for t in tasks
        ]
        return ScanResponse(message="扫描任务已启动", task_count=len(tasks), tool_ids=scan_request.tool_ids, tasks=tasks_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动扫描失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"启动扫描失败: {str(e)}")


@router.post("/api/v1/compliance/scan", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def compliance_scan(
    request: ComplianceScanRequest,
    db: Session = Depends(get_db),
):
    """一体化合规扫描接口（工具名称列表）"""
    try:
        tool_names = [t.strip() for t in (request.tools or []) if t and t.strip()]
        if not tool_names:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tools 列表不能为空")
        tools, existing_count = batch_create_tools(db, tool_names)
        tool_ids = [tool.id for tool in tools]
        scan_service = get_scan_service()
        tasks = scan_service.create_scan_tasks(tool_ids, db)
        scan_service.start()
        tasks_info = [
            {"tool_id": t.tool_id, "tool_name": t.tool_name, "status": t.status.value, "report_id": None}
            for t in tasks
        ]
        return ScanResponse(
            message=f"扫描任务已启动（共 {len(tasks)} 个工具，其中已存在 {existing_count} 个）",
            task_count=len(tasks),
            tool_ids=tool_ids,
            tasks=tasks_info,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"一体化合规扫描失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"一体化合规扫描失败: {str(e)}")


@router.get("/api/v1/scan/status/{tool_id}", response_model=ScanTaskStatusResponse)
async def get_scan_status(tool_id: int, db: Session = Depends(get_db)):
    """获取扫描任务状态"""
    try:
        scan_service = get_scan_service()
        task = scan_service.get_task_status(tool_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"扫描任务不存在: tool_id={tool_id}")
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"工具不存在: ID {tool_id}")
        return ScanTaskStatusResponse(
            tool_id=tool_id,
            tool_name=tool.name,
            status=task.status.value,
            progress=getattr(task, "progress", None),
            current_step=getattr(task, "current_step", None),
            result=task.result,
            error=getattr(task, "error", None) or getattr(task, "error_message", None),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取扫描状态失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取扫描状态失败: {str(e)}")


# ==================== 报告 ====================


@router.get("/api/v1/reports/{report_id}", response_model=Dict[str, Any])
async def get_report(report_id: int, db: Session = Depends(get_db)):
    """获取合规报告"""
    try:
        report = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"报告不存在: ID {report_id}")
        tool = db.query(Tool).filter(Tool.id == report.tool_id).first()
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"工具不存在: ID {report.tool_id}")
        report_service = get_report_service()
        return report_service.generate_json_report(tool, report, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取报告失败: {str(e)}")


@router.get("/api/v1/reports/{report_id}/export")
async def export_report(report_id: int, db: Session = Depends(get_db)):
    """导出合规报告为 JSON 文件"""
    try:
        report = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"报告不存在: ID {report_id}")
        tool = db.query(Tool).filter(Tool.id == report.tool_id).first()
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"工具不存在: ID {report.tool_id}")
        report_service = get_report_service()
        filepath = report_service.save_json_report(tool, report, db)
        return FileResponse(path=str(filepath), filename=filepath.name, media_type="application/json")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出报告失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"导出报告失败: {str(e)}")


@router.get("/api/v1/reports/{report_id}/kb-diff", response_model=Dict[str, Any])
async def get_kb_diff_for_report(report_id: int, db: Session = Depends(get_db)):
    """获取报告的知识库差异对比信息"""
    try:
        report = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"报告不存在: ID {report_id}")
        tool = db.query(Tool).filter(Tool.id == report.tool_id).first()
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工具不存在")
        tos_analysis = json.loads(report.tos_analysis) if report.tos_analysis else {}
        if not tos_analysis:
            return {"available": False, "reason": "报告中没有TOS分析数据"}
        from src.services.kb_diff_service import check_and_prepare_kb_update

        kb_update_info = check_and_prepare_kb_update(tool.name, tos_analysis, db)
        return {
            "tool_name": tool.name,
            "exists": kb_update_info["exists"],
            "has_changes": kb_update_info["diff"]["has_changes"] if kb_update_info["diff"] else False,
            "diff": kb_update_info["diff"],
            "new_data": kb_update_info["new_data"],
            "existing_data": kb_update_info["kb_entry"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库差异对比失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取知识库差异对比失败: {str(e)}")
