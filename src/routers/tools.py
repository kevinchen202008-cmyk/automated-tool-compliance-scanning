"""
工具管理 API 路由
Tool management API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.logger import get_logger
from src.schemas import ToolRequest, ToolResponse, BatchToolRequest, BatchToolResponse
from src.services.tool_service import get_or_create_tool, parse_tool_names, batch_create_tools

logger = get_logger()
router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_request: ToolRequest,
    db: Session = Depends(get_db),
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
            created_at=tool.created_at.isoformat() if tool.created_at else None,
        )
    except Exception as e:
        logger.error(f"创建工具失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建工具失败，请查看服务端日志",
        )


@router.post("/batch", response_model=BatchToolResponse, status_code=status.HTTP_201_CREATED)
async def batch_create_tools_endpoint(
    batch_request: BatchToolRequest,
    db: Session = Depends(get_db),
):
    """
    批量创建工具

    - **tools**: 工具名称列表（支持换行分隔或逗号分隔）
    """
    try:
        tool_names = parse_tool_names("\n".join(batch_request.tools))
        logger.info(f"批量创建工具请求，解析后工具数量: {len(tool_names)}")
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
                    created_at=tool.created_at.isoformat() if tool.created_at else None,
                )
                for tool in created_tools
            ],
        )
    except Exception as e:
        logger.error(f"批量创建工具失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量创建工具失败，请查看服务端日志",
        )
