"""
工具合规扫描 Agent 服务 - 主入口
Main entry point for Tool Compliance Scanning Agent Service
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from src.config import get_config, load_config
from src.database import init_database, check_database_exists
from src.logger import setup_logger, get_logger

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 鉴权已启用但未配置 api_key",
        )
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库"""
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
    yield


# 创建 FastAPI 应用
app = FastAPI(
    title="工具合规扫描 Agent 服务",
    description="基于 AI 的工具合规扫描服务，支持工具合规性评估和报告生成",
    version="0.1.0",
    lifespan=lifespan,
)

# 挂载静态文件目录
try:
    from pathlib import Path

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
except Exception as e:
    logger.warning(f"无法挂载静态文件目录: {e}")


# ==================== 注册路由模块 ====================

from src.routers.tools import router as tools_router
from src.routers.scan import router as scan_router
from src.routers.knowledge_base import router as kb_router

app.include_router(tools_router)
app.include_router(scan_router)
app.include_router(kb_router)


# ==================== 基础路由 ====================


@app.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "service": "工具合规扫描 Agent 服务",
        "version": "0.1.0",
        "status": "running",
        "description": "Tool Compliance Scanning Agent Service",
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "tool-compliance-scanning-agent"},
    )


@app.get("/ui")
async def ui():
    """Web UI 界面（无需授权，直接访问）"""
    from pathlib import Path

    ui_file = Path(__file__).resolve().parent / "static" / "index.html"
    try:
        if ui_file.exists():
            return FileResponse(path=str(ui_file), media_type="text/html")
    except Exception as e:
        logger.warning(f"加载UI文件失败，返回备用页: {e}")
    fallback = (
        "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>工具合规扫描 Agent</title></head><body>"
        "<h1>工具合规扫描 Agent</h1><p>Web UI 文件未找到，请使用以下链接：</p>"
        "<ul><li><a href='/docs'>API 文档</a></li><li><a href='/health'>健康检查</a></li></ul></body></html>"
    )
    return HTMLResponse(content=fallback)


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    import uvicorn

    cfg = get_config()
    uvicorn.run(app, host=cfg.service.host, port=cfg.service.port, reload=cfg.service.debug)
