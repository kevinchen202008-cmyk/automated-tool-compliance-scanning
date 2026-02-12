"""
请求/响应数据模型
Pydantic request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ==================== 工具管理 ====================

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
    tools: List[str] = Field(..., description="工具名称列表", min_length=1)


class BatchToolResponse(BaseModel):
    """批量工具创建响应"""
    total: int
    created: int
    existing: int
    tools: List[ToolResponse]


# ==================== 扫描 ====================

class ScanRequest(BaseModel):
    """扫描请求"""
    tool_ids: List[int] = Field(..., description="工具ID列表", min_length=1)


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
    current_step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ComplianceScanRequest(BaseModel):
    """一体化合规扫描请求（工具名列表）"""
    tools: List[str] = Field(..., description="工具名称列表", min_length=1)
