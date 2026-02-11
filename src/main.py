"""
工具合规扫描 Agent 服务 - 主入口
Main entry point for Tool Compliance Scanning Agent Service
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query, Header
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import json
import os
from src.config import get_config, load_config
from src.database import init_database, check_database_exists, get_db
from src.logger import setup_logger, get_logger
from src.services.tool_service import (
    get_or_create_tool,
    parse_tool_names,
    batch_create_tools
)
from src.services.scan_service import (
    get_scan_service,
    ScanTaskStatus
)
from sqlalchemy.orm import Session
from src.models import Tool, ComplianceReport
from src.services.report_service import get_report_service

# 初始化日志系统
setup_logger()
logger = get_logger()

# 加载配置
load_config()
config = get_config()


async def api_auth_guard(x_api_key: Optional[str] = Header(None)):
    """
    简单的 API Key 鉴权预留
    - 当 config.web.security.enable_auth = false 时不生效
    - 当启用时，优先从 config.web.security.api_key 或环境变量 API_KEY 读取期望值
    """
    cfg = get_config()
    sec = cfg.web.security
    if not sec.enable_auth:
        return
    expected = sec.api_key or os.getenv("API_KEY")
    if not expected:
        # 启用了鉴权但未配置密钥，视为配置错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 鉴权已启用但未配置 api_key"
        )
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

# 创建FastAPI应用
app = FastAPI(
    title="工具合规扫描 Agent 服务",
    description="基于 AI 的工具合规扫描服务，支持工具合规性评估和报告生成",
    version="0.1.0",
)

# 挂载静态文件目录
try:
    from pathlib import Path
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
except Exception as e:
    logger.warning(f"无法挂载静态文件目录: {e}")

# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    try:
        if not check_database_exists():
            logger.info("数据库不存在，开始初始化...")
            init_database()
            logger.info("数据库初始化完成")
        else:
            logger.info("数据库已存在，跳过初始化")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


# ==================== 基础路由 ====================

@app.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "service": "工具合规扫描 Agent 服务",
        "version": "0.1.0",
        "status": "running",
        "description": "Tool Compliance Scanning Agent Service"
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "tool-compliance-scanning-agent"
        }
    )


@app.get("/ui")
async def ui():
    """Web UI界面（无需授权，直接访问）"""
    from pathlib import Path
    ui_file = Path(__file__).resolve().parent / "static" / "index.html"
    try:
        if ui_file.exists():
            return FileResponse(path=str(ui_file), media_type="text/html")
    except Exception as e:
        logger.warning(f"加载UI文件失败，返回备用页: {e}")
    # 无 static/index.html 时返回备用页，避免 500
    fallback = (
        "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>工具合规扫描 Agent</title></head><body>"
        "<h1>工具合规扫描 Agent</h1><p>Web UI 文件未找到，请使用以下链接：</p>"
        "<ul><li><a href='/docs'>API 文档</a></li><li><a href='/health'>健康检查</a></li></ul></body></html>"
    )
    return HTMLResponse(content=fallback)


# ==================== 数据模型 ====================

class ToolRequest(BaseModel):
    """工具创建请求"""
    name: str = Field(..., description="工具名称", min_length=1, max_length=255)
    version: Optional[str] = Field(None, description="工具版本", max_length=100)


class ToolResponse(BaseModel):
    """工具响应"""
    id: int
    name: str
    version: Optional[str]
    source: str
    created_at: Optional[str] = None


class BatchToolRequest(BaseModel):
    """批量工具创建请求"""
    tools: List[str] = Field(..., description="工具名称列表", min_items=1)


class BatchToolResponse(BaseModel):
    """批量工具创建响应"""
    total: int
    created: int
    existing: int
    tools: List[ToolResponse]


class ScanRequest(BaseModel):
    """扫描请求"""
    tool_ids: List[int] = Field(..., description="工具ID列表", min_items=1)


class ScanResponse(BaseModel):
    """扫描响应"""
    message: str
    task_count: int
    tool_ids: List[int]
    tasks: List[Dict[str, Any]] = Field(default_factory=list, description="扫描任务列表")


class ScanTaskStatusResponse(BaseModel):
    """扫描任务状态响应"""
    tool_id: int
    tool_name: str
    status: str
    progress: Optional[float] = None
    current_step: Optional[str] = None  # 当前步骤描述
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ComplianceScanRequest(BaseModel):
    """一体化合规扫描请求（工具名列表）"""
    tools: List[str] = Field(..., description="工具名称列表", min_items=1)


# ==================== 工具管理API ====================

@app.post("/api/v1/tools", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_request: ToolRequest,
    db: Session = Depends(get_db)
):
    """
    创建单个工具
    
    - **name**: 工具名称
    - **version**: 工具版本（可选）
    """
    try:
        tool = get_or_create_tool(db, tool_request.name, tool_request.version)
        
        return ToolResponse(
            id=tool.id,
            name=tool.name,
            version=tool.version,
            source=tool.source,
            created_at=tool.created_at.isoformat() if tool.created_at else None
        )
        
    except Exception as e:
        logger.error(f"创建工具失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建工具失败: {str(e)}"
        )


@app.post("/api/v1/tools/batch", response_model=BatchToolResponse, status_code=status.HTTP_201_CREATED)
async def batch_create_tools_endpoint(
    batch_request: BatchToolRequest,
    db: Session = Depends(get_db)
):
    """
    批量创建工具
    
    - **tools**: 工具名称列表（支持换行分隔或逗号分隔）
    """
    try:
        # 解析工具名称列表
        tool_names = parse_tool_names("\n".join(batch_request.tools))
        
        logger.info(f"批量创建工具请求，解析后工具数量: {len(tool_names)}")
        
        # 批量创建工具
        created_tools, existing_count = batch_create_tools(db, tool_names)
        
        logger.info(f"批量创建工具完成: 创建 {len(created_tools)} 个，已存在 {existing_count} 个")
        
        return BatchToolResponse(
            total=len(tool_names),
            created=len(created_tools),
            existing=existing_count,
            tools=[
                ToolResponse(
                    id=tool.id,
                    name=tool.name,
                    version=tool.version,
                    source=tool.source,
                    created_at=tool.created_at.isoformat() if tool.created_at else None
                )
                for tool in created_tools
            ]
        )
        
    except Exception as e:
        logger.error(f"批量创建工具失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量创建工具失败: {str(e)}"
        )


# ==================== 扫描API ====================

@app.post("/api/v1/scan/start", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(
    scan_request: ScanRequest,
    db: Session = Depends(get_db)
):
    """
    启动合规扫描任务
    
    - **tool_ids**: 工具ID列表
    """
    try:
        scan_service = get_scan_service()
        
        # 验证工具是否存在
        tools = db.query(Tool).filter(Tool.id.in_(scan_request.tool_ids)).all()
        if len(tools) != len(scan_request.tool_ids):
            found_ids = {tool.id for tool in tools}
            missing_ids = set(scan_request.tool_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: {missing_ids}"
            )
        
        # 创建扫描任务（传入工具ID列表，不是Tool对象列表）
        tasks = scan_service.create_scan_tasks(scan_request.tool_ids, db)
        
        # 启动扫描（异步）
        scan_service.start()
        
        logger.info(f"扫描任务已启动: {len(tasks)} 个任务")
        
        # 构建任务信息列表
        tasks_info = [
            {
                "tool_id": task.tool_id,
                "tool_name": task.tool_name,
                "status": task.status.value,
                "report_id": None  # 初始时还没有报告ID
            }
            for task in tasks
        ]
        
        return ScanResponse(
            message="扫描任务已启动",
            task_count=len(tasks),
            tool_ids=scan_request.tool_ids,
            tasks=tasks_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动扫描失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动扫描失败: {str(e)}"
        )


@app.post("/api/v1/compliance/scan", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def compliance_scan(
    request: ComplianceScanRequest,
    db: Session = Depends(get_db),
    _: None = Depends(api_auth_guard)
):
    """
    一体化合规扫描接口（工具名称列表）
    
    - **tools**: 工具名称列表
    
    行为：
    1. 批量创建/获取工具记录（与 /api/v1/tools/batch 一致）
    2. 启动扫描任务（与 /api/v1/scan/start 一致）
    3. 返回 ScanResponse，包含任务列表
    """
    try:
        tool_names = [t.strip() for t in (request.tools or []) if t and t.strip()]
        if not tool_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tools 列表不能为空"
            )
        
        tools, existing_count = batch_create_tools(db, tool_names)
        tool_ids = [tool.id for tool in tools]
        
        scan_service = get_scan_service()
        tasks = scan_service.create_scan_tasks(tool_ids, db)
        scan_service.start()
        
        tasks_info = [
            {
                "tool_id": task.tool_id,
                "tool_name": task.tool_name,
                "status": task.status.value,
                "report_id": None
            }
            for task in tasks
        ]
        
        return ScanResponse(
            message=f"扫描任务已启动（共 {len(tasks)} 个工具，其中已存在 {existing_count} 个）",
            task_count=len(tasks),
            tool_ids=tool_ids,
            tasks=tasks_info
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"一体化合规扫描失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"一体化合规扫描失败: {str(e)}"
        )


@app.get("/api/v1/scan/status/{tool_id}", response_model=ScanTaskStatusResponse)
async def get_scan_status(
    tool_id: int,
    db: Session = Depends(get_db)
):
    """
    获取扫描任务状态
    
    - **tool_id**: 工具ID
    """
    try:
        scan_service = get_scan_service()
        task = scan_service.get_task_status(tool_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"扫描任务不存在: tool_id={tool_id}"
            )
        
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: ID {tool_id}"
            )
        
        return ScanTaskStatusResponse(
            tool_id=tool_id,
            tool_name=tool.name,
            status=task.status.value,
            progress=getattr(task, 'progress', None),
            current_step=getattr(task, 'current_step', None),
            result=task.result,
            error=getattr(task, 'error', None) or getattr(task, 'error_message', None)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取扫描状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取扫描状态失败: {str(e)}"
        )


# ==================== 报告API ====================

@app.get("/api/v1/reports/{report_id}", response_model=Dict[str, Any])
async def get_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    获取合规报告
    
    - **report_id**: 报告ID
    """
    try:
        report = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报告不存在: ID {report_id}"
            )
        
        tool = db.query(Tool).filter(Tool.id == report.tool_id).first()
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: ID {report.tool_id}"
            )
        
        report_service = get_report_service()
        json_report = report_service.generate_json_report(tool, report, db)
        
        return json_report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报告失败: {str(e)}"
        )


@app.get("/api/v1/reports/{report_id}/export")
async def export_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    导出合规报告为JSON文件
    
    - **report_id**: 报告ID
    """
    try:
        report = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报告不存在: ID {report_id}"
            )
        
        tool = db.query(Tool).filter(Tool.id == report.tool_id).first()
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: ID {report.tool_id}"
            )
        
        report_service = get_report_service()
        filepath = report_service.save_json_report(tool, report, db)
        
        return FileResponse(
            path=str(filepath),
            filename=filepath.name,
            media_type="application/json"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出报告失败: {str(e)}"
        )


# ==================== 工具信息库管理 API（/knowledge-base） ====================

@app.get("/api/v1/knowledge-base/{tool_name}", response_model=Dict[str, Any])
async def get_knowledge_base_entry(
    tool_name: str,
    db: Session = Depends(get_db)
):
    """
    获取工具信息库条目
    
    - **tool_name**: 工具名称
    """
    try:
        from src.services.knowledge_base_service import get_knowledge_base_dict
        
        kb_data = get_knowledge_base_dict(db, tool_name)
        
        if not kb_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具信息库中不存在工具: {tool_name}"
            )
        
        return {
            "tool_name": tool_name,
            "data": kb_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具信息库条目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具信息库条目失败: {str(e)}"
        )


@app.put("/api/v1/knowledge-base/{tool_name}", response_model=Dict[str, Any])
async def update_knowledge_base_entry(
    tool_name: str,
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    创建或更新工具知识库条目
    
    - **tool_name**: 工具名称
    - **data**: 知识库数据（JSON格式）
    """
    try:
        from src.services.knowledge_base_service import create_or_update_knowledge_base, knowledge_base_entry_to_dict
        
        entry = create_or_update_knowledge_base(
            db=db,
            tool_name=tool_name,
            data=data,
            source="user",
            updated_by="user"  # TODO: 从认证信息获取用户ID
        )
        
        return {
            "tool_name": tool_name,
            "data": knowledge_base_entry_to_dict(entry),
            "message": "知识库条目已更新"
        }
        
    except Exception as e:
        logger.error(f"更新知识库条目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新知识库条目失败: {str(e)}"
        )


@app.delete("/api/v1/knowledge-base/{tool_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base_entry(
    tool_name: str,
    db: Session = Depends(get_db)
):
    """
    删除工具知识库条目
    
    - **tool_name**: 工具名称
    """
    try:
        from src.services.knowledge_base_service import delete_knowledge_base_entry
        
        success = delete_knowledge_base_entry(db, tool_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"知识库中不存在工具: {tool_name}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库条目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除知识库条目失败: {str(e)}"
        )


@app.get("/api/v1/knowledge-base", response_model=Dict[str, Any])
async def list_knowledge_base_entries(
    limit: int = Query(1000, ge=1, le=10000, description="返回数量限制"),
    order_by: str = Query("tool_name", description="排序字段: tool_name/updated_at"),
    db: Session = Depends(get_db)
):
    """
    列出所有知识库条目（按字母顺序）
    
    - **limit**: 返回数量限制（默认1000）
    - **order_by**: 排序字段（tool_name/updated_at，默认tool_name）
    """
    try:
        from src.services.knowledge_base_service import list_all_knowledge_base_entries, knowledge_base_entry_to_dict
        
        entries = list_all_knowledge_base_entries(db, limit, order_by)
        
        return {
            "total": len(entries),
            "entries": [
                {
                    "tool_name": entry.tool_name,
                    "data": knowledge_base_entry_to_dict(entry)
                }
                for entry in entries
            ]
        }
        
    except Exception as e:
        logger.error(f"列出知识库条目失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出知识库条目失败: {str(e)}"
        )


@app.get("/api/v1/knowledge-base/{tool_name}/detail", response_model=Dict[str, Any])
async def get_kb_detail_for_display(
    tool_name: str,
    db: Session = Depends(get_db)
):
    """
    获取知识库条目的详细信息（用于前端展示）
    
    - **tool_name**: 工具名称
    """
    try:
        from src.services.knowledge_base_service import get_knowledge_base_dict
        from src.services.kb_diff_service import prepare_kb_data_from_tos_analysis
        
        kb_data = get_knowledge_base_dict(db, tool_name)
        
        if not kb_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"知识库中不存在工具: {tool_name}"
            )
        
        # 格式化数据，提取4个关键信息
        license_info = {
            "license_type": kb_data.get("license_type"),
            "license_version": kb_data.get("license_version"),
            "license_mode": kb_data.get("license_mode")
        }
        
        company_info = {
            "company_name": kb_data.get("company_name"),
            "company_country": kb_data.get("company_country"),
            "company_headquarters": kb_data.get("company_headquarters"),
            "china_office": kb_data.get("china_office")
        }
        
        commercial_restrictions = {
            "commercial_license_required": kb_data.get("commercial_license_required"),
            "free_for_commercial": kb_data.get("free_for_commercial"),
            "restrictions": kb_data.get("commercial_restrictions"),
            "user_limit": kb_data.get("user_limit"),
            "feature_restrictions": kb_data.get("feature_restrictions")
        }
        
        alternative_tools = kb_data.get("alternative_tools", [])
        if not isinstance(alternative_tools, list):
            alternative_tools = []
        
        return {
            "tool_name": tool_name,
            "license_info": license_info,
            "company_info": company_info,
            "commercial_restrictions": commercial_restrictions,
            "alternative_tools": alternative_tools[:2],  # 只返回前2个
            "source": kb_data.get("source"),
            "updated_at": kb_data.get("updated_at"),
            "updated_by": kb_data.get("updated_by")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识库详情失败: {str(e)}"
        )


@app.get("/api/v1/reports/{report_id}/kb-diff", response_model=Dict[str, Any])
async def get_kb_diff_for_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """
    获取报告的知识库差异对比信息
    
    - **report_id**: 报告ID
    """
    try:
        report = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报告不存在: ID {report_id}"
            )
        
        tool = db.query(Tool).filter(Tool.id == report.tool_id).first()
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在"
            )
        
        # 获取TOS分析结果
        tos_analysis = json.loads(report.tos_analysis) if report.tos_analysis else {}
        if not tos_analysis:
            return {
                "available": False,
                "reason": "报告中没有TOS分析数据"
            }
        
        # 检查知识库并准备差异对比
        from src.services.kb_diff_service import check_and_prepare_kb_update
        
        kb_update_info = check_and_prepare_kb_update(tool.name, tos_analysis, db)
        
        return {
            "tool_name": tool.name,
            "exists": kb_update_info["exists"],
            "has_changes": kb_update_info["diff"]["has_changes"] if kb_update_info["diff"] else False,
            "diff": kb_update_info["diff"],
            "new_data": kb_update_info["new_data"],
            "existing_data": kb_update_info["kb_entry"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库差异对比失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识库差异对比失败: {str(e)}"
        )


@app.post("/api/v1/knowledge-base/{tool_name}/create-from-report", response_model=Dict[str, Any])
async def create_kb_from_report(
    tool_name: str,
    report_id: int = Query(..., description="报告ID"),
    db: Session = Depends(get_db)
):
    """
    从报告结果创建新的知识库记录（用户确认后）
    
    - **tool_name**: 工具名称
    - **report_id**: 报告ID
    """
    try:
        from src.services.knowledge_base_service import create_or_update_knowledge_base, knowledge_base_entry_to_dict, get_knowledge_base_entry
        from src.services.kb_diff_service import prepare_kb_data_from_tos_analysis
        
        # 检查工具信息库中是否已存在
        existing_entry = get_knowledge_base_entry(db, tool_name)
        if existing_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工具信息库中已存在工具: {tool_name}，请使用更新接口"
            )
        
        # 获取报告
        report = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报告不存在: ID {report_id}"
            )
        
        # 获取TOS分析结果
        tos_analysis = json.loads(report.tos_analysis) if report.tos_analysis else {}
        if not tos_analysis:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="报告中没有TOS分析数据"
            )
        
        # 准备工具信息库数据
        kb_data = prepare_kb_data_from_tos_analysis(tos_analysis)
        
        # 创建工具信息库条目
        entry = create_or_update_knowledge_base(
            db=db,
            tool_name=tool_name,
            data=kb_data,
            source="ai",
            updated_by="user"
        )
        
        logger.info(f"用户确认创建工具信息库条目: {tool_name} (报告ID: {report_id})")
        
        return {
            "message": "工具信息库记录创建成功",
            "tool_name": tool_name,
            "data": knowledge_base_entry_to_dict(entry)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从报告创建知识库失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"从报告创建知识库失败: {str(e)}"
        )


@app.post("/api/v1/knowledge-base/{tool_name}/update-from-report", response_model=Dict[str, Any])
async def update_kb_from_report(
    tool_name: str,
    report_id: int = Query(..., description="报告ID"),
    db: Session = Depends(get_db)
):
    """
    从报告结果更新工具信息库
    
    - **tool_name**: 工具名称
    - **report_id**: 报告ID
    """
    try:
        from src.services.knowledge_base_service import create_or_update_knowledge_base, knowledge_base_entry_to_dict
        from src.services.kb_diff_service import prepare_kb_data_from_tos_analysis
        
        # 获取报告
        report = db.query(ComplianceReport).filter(ComplianceReport.id == report_id).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报告不存在: ID {report_id}"
            )
        
        # 获取TOS分析结果
        tos_analysis = json.loads(report.tos_analysis) if report.tos_analysis else {}
        if not tos_analysis:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="报告中没有TOS分析数据"
            )
        
        # 准备知识库数据
        kb_data = prepare_kb_data_from_tos_analysis(tos_analysis)
        
        # 更新或创建知识库条目
        entry = create_or_update_knowledge_base(
            db=db,
            tool_name=tool_name,
            data=kb_data,
            source="ai",
            updated_by="user"
        )
        
        logger.info(f"从报告更新知识库: {tool_name} (报告ID: {report_id})")
        
        return {
            "message": "知识库更新成功",
            "tool_name": tool_name,
            "data": knowledge_base_entry_to_dict(entry)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从报告更新知识库失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"从报告更新知识库失败: {str(e)}"
        )


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    import uvicorn
    cfg = get_config()
    uvicorn.run(
        app,
        host=cfg.service.host,
        port=cfg.service.port,
        reload=cfg.service.debug
    )
