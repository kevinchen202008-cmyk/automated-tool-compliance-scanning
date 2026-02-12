"""
扫描服务模块
Scan service module for managing compliance scanning tasks
"""

import asyncio
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from src.models import Tool, ComplianceReport
from src.logger import get_logger
from src.config import get_config
from src.services.tool_info_service import get_tool_info
from src.services.tos_service import get_and_analyze_tos
from src.services.compliance_engine import get_compliance_engine
from src.services.ai_client import get_ai_client
from src.services.tool_knowledge_base import merge_tos_analysis_with_knowledge_base

logger = get_logger()


class ScanTaskStatus(str, Enum):
    """扫描任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanTask:
    """扫描任务类"""
    
    def __init__(self, tool_id: int, tool_name: str):
        self.tool_id = tool_id
        self.tool_name = tool_name
        self.status = ScanTaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.error: Optional[str] = None  # 兼容性：error 和 error_message 都支持
        self.result: Optional[Dict[str, Any]] = None
        self.progress: Optional[float] = None  # 进度（0.0-1.0）
        self.current_step: Optional[str] = None  # 当前步骤描述
    
    def start(self):
        """开始处理任务"""
        self.status = ScanTaskStatus.PROCESSING
        self.started_at = datetime.now()
        self.progress = 0.0
        self.current_step = "初始化扫描任务"
        logger.info(f"开始扫描任务: {self.tool_name} (ID: {self.tool_id})")
    
    def update_progress(self, progress: float, step: str):
        """更新任务进度"""
        self.progress = max(0.0, min(1.0, progress))  # 限制在0-1之间
        self.current_step = step
        logger.debug(f"任务进度更新: {self.tool_name} - {step} ({progress*100:.1f}%)")
    
    def complete(self, result: Dict[str, Any]):
        """完成任务"""
        self.status = ScanTaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        logger.info(f"完成扫描任务: {self.tool_name} (ID: {self.tool_id})")
    
    def fail(self, error_message: str):
        """任务失败"""
        self.status = ScanTaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        self.error = error_message  # 同时设置 error 属性
        logger.error(f"扫描任务失败: {self.tool_name} (ID: {self.tool_id}) - {error_message}")


class ScanService:
    """扫描服务类"""
    
    def __init__(self):
        self.config = get_config()
        self.max_concurrent = self.config.scanning.max_concurrent
        self.tasks: Dict[int, ScanTask] = {}
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    def create_scan_tasks(self, tool_ids: List[int], db: Session) -> List[ScanTask]:
        """
        为工具ID列表创建扫描任务
        
        Args:
            tool_ids: 工具ID列表
            db: 数据库会话
        
        Returns:
            List[ScanTask]: 扫描任务列表
        """
        tasks = []
        
        for tool_id in tool_ids:
            # 验证工具是否存在
            tool = db.query(Tool).filter(Tool.id == tool_id).first()
            if not tool:
                logger.warning(f"工具不存在: ID {tool_id}")
                continue
            
            # 创建扫描任务
            task = ScanTask(tool_id=tool.id, tool_name=tool.name)
            self.tasks[tool_id] = task
            tasks.append(task)
            logger.info(f"创建扫描任务: {tool.name} (ID: {tool_id})")
        
        return tasks
    
    def start(self):
        """
        启动扫描服务（异步处理所有待处理的任务）
        """
        if not self.tasks:
            logger.warning("没有待处理的扫描任务")
            return
        
        # 在新线程中异步处理所有任务
        import threading
        import asyncio
        
        def run_async_tasks():
            """在新的事件循环中运行异步任务"""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                new_loop.run_until_complete(self._process_all_tasks())
            finally:
                new_loop.close()
        
        # 在后台线程中运行
        thread = threading.Thread(target=run_async_tasks, daemon=True)
        thread.start()
        logger.info(f"已启动扫描服务，待处理任务数: {len(self.tasks)}")
    
    async def _process_all_tasks(self):
        """处理所有扫描任务"""
        from src.database import get_session
        SessionLocal = get_session()
        
        tasks_to_process = list(self.tasks.values())
        logger.info(f"开始处理 {len(tasks_to_process)} 个扫描任务")
        
        # 并发处理所有任务
        async def process_task(task):
            db = SessionLocal()
            try:
                await self.scan_tool(task, db)
            except Exception as e:
                logger.error(f"处理扫描任务失败: {task.tool_name} - {e}")
            finally:
                db.close()
        
        # 使用gather并发执行所有任务
        await asyncio.gather(*[process_task(task) for task in tasks_to_process])
    
    async def scan_tool(self, task: ScanTask, db: Session):
        """
        扫描单个工具（异步）
        
        Args:
            task: 扫描任务
            db: 数据库会话
        """
        async with self.semaphore:  # 控制并发数
            try:
                task.start()
                
                # 1. 获取工具信息（Story 2.4）
                task.update_progress(0.1, "获取工具基本信息...")
                tool = db.query(Tool).filter(Tool.id == task.tool_id).first()
                if not tool:
                    raise ValueError(f"工具不存在: ID {task.tool_id}")
                
                # 1. 获取工具信息（简化：仅获取基本信息，不进行详细分析）
                tool_info = await get_tool_info(tool, db)
                logger.info(f"获取工具信息完成: {tool.name}")
                
                # 2. 获取和分析TOS信息（核心功能）
                task.update_progress(0.3, "搜索和分析工具服务条款(TOS)...")
                tos_result = await get_and_analyze_tos(tool, db)
                tos_analysis = tos_result.get("tos_analysis") if tos_result["success"] else None
                
                if tos_result["success"]:
                    logger.info(f"TOS信息获取和分析完成: {tool.name}")
                else:
                    logger.warning(f"TOS信息获取失败: {tool.name} - {tos_result.get('error', 'unknown')}")
                
                # 2.5. 合并知识库信息（AI结果优先，知识库用于补充）
                task.update_progress(0.5, "合并知识库信息...")
                tos_analysis = merge_tos_analysis_with_knowledge_base(tool.name, tos_analysis, db)
                if tos_analysis and len(tos_analysis) > 0:
                    logger.info(f"已合并TOS分析和知识库信息: {tool.name}")
                
                # 3. 独立获取替代方案（核心功能，不依赖TOS分析）
                task.update_progress(0.7, "分析替代方案...")
                alternative_tools = []
                if not tos_analysis or not tos_analysis.get("alternative_tools"):
                    try:
                        ai_client = get_ai_client()
                        alternative_tools = await ai_client.get_alternative_tools(tool.name)
                        if alternative_tools:
                            logger.info(f"独立获取替代方案成功: {tool.name} - 找到 {len(alternative_tools)} 个替代方案")
                            # 如果TOS分析存在但没有替代方案，补充进去
                            if tos_analysis:
                                tos_analysis["alternative_tools"] = alternative_tools
                            else:
                                # 如果TOS分析不存在，创建一个包含替代方案的最小结构
                                tos_analysis = {"alternative_tools": alternative_tools}
                    except Exception as e:
                        logger.warning(f"独立获取替代方案失败: {tool.name} - {e}")
                        # 如果AI获取替代方案也失败，且知识库有替代方案，使用知识库的
                        if tos_analysis and tos_analysis.get("alternative_tools"):
                            logger.info(f"使用知识库中的替代方案: {tool.name}")
                
                # 4. 生成合规报告（简化模式：仅保存TOS分析和替代方案，跳过多维度评估）
                task.update_progress(0.9, "生成合规报告...")
                compliance_engine = get_compliance_engine()
                report = await compliance_engine.generate_compliance_report(
                    tool=tool,
                    db=db,
                    tool_info=tool_info,
                    tos_analysis=tos_analysis
                )
                
                logger.info(f"合规报告生成完成: {tool.name} - 报告ID: {report.id}")
                
                # 完成任务
                task.update_progress(1.0, "扫描完成")
                task.complete({
                    "tool_id": task.tool_id,
                    "report_id": report.id,
                    "message": "合规扫描完成"
                })
                    
            except Exception as e:
                logger.error(f"扫描工具失败: {task.tool_name} - {e}")
                task.fail("扫描失败，请查看服务端日志")
    
    async def scan_tools(self, tool_ids: List[int], db: Session) -> Dict[int, ScanTask]:
        """
        并发扫描多个工具
        
        Args:
            tool_ids: 工具ID列表
            db: 数据库会话
        
        Returns:
            Dict[int, ScanTask]: 工具ID到扫描任务的映射
        """
        # 创建扫描任务
        tasks = self.create_scan_tasks(tool_ids, db)
        
        if not tasks:
            logger.warning("没有有效的扫描任务")
            return {}
        
        # 并发执行扫描任务
        scan_coroutines = [self.scan_tool(task, db) for task in tasks]
        await asyncio.gather(*scan_coroutines)
        
        return {task.tool_id: task for task in tasks}
    
    def get_task_status(self, tool_id: int) -> Optional[ScanTask]:
        """
        获取任务状态
        
        Args:
            tool_id: 工具ID
        
        Returns:
            Optional[ScanTask]: 扫描任务，如果不存在返回None
        """
        return self.tasks.get(tool_id)
    
    def get_all_tasks_status(self) -> Dict[int, ScanTask]:
        """
        获取所有任务状态
        
        Returns:
            Dict[int, ScanTask]: 所有扫描任务
        """
        return self.tasks.copy()


# 全局扫描服务实例
_scan_service: Optional[ScanService] = None


def get_scan_service() -> ScanService:
    """
    获取扫描服务实例（单例模式）
    
    Returns:
        ScanService: 扫描服务实例
    """
    global _scan_service
    if _scan_service is None:
        _scan_service = ScanService()
    return _scan_service
