"""
初始化知识库：将内置知识库数据导入到数据库
Initialize knowledge base: Import built-in knowledge base data to database
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db, init_database
from src.services.knowledge_base_service import create_or_update_knowledge_base
from src.services.tool_knowledge_base import TOOL_KNOWLEDGE_BASE
from src.logger import setup_logger, get_logger

setup_logger()
logger = get_logger()


def init_knowledge_base():
    """
    初始化知识库：将内置知识库数据导入到数据库
    """
    try:
        # 初始化数据库
        init_database()
        logger.info("数据库初始化完成")
        
        # 获取数据库会话
        from src.database import get_session
        SessionLocal = get_session()
        db = SessionLocal()
        
        try:
            # 导入内置知识库数据
            imported_count = 0
            for tool_name, data in TOOL_KNOWLEDGE_BASE.items():
                try:
                    create_or_update_knowledge_base(
                        db=db,
                        tool_name=tool_name,
                        data=data,
                        source="system",
                        updated_by="system"
                    )
                    imported_count += 1
                    logger.info(f"已导入知识库条目: {tool_name}")
                except Exception as e:
                    logger.error(f"导入知识库条目失败: {tool_name} - {e}")
            
            logger.info(f"知识库初始化完成: 共导入 {imported_count} 个条目")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"知识库初始化失败: {e}")
        raise


if __name__ == "__main__":
    print("开始初始化知识库...")
    init_knowledge_base()
    print("知识库初始化完成！")
