"""
数据库初始化脚本
Database initialization script

使用方法:
    python src/db_init.py
"""

from src.database import init_database, get_config
from src.config import get_config as get_app_config

if __name__ == "__main__":
    print("开始初始化数据库...")
    try:
        config = get_app_config()
        print(f"数据库类型: {config.database.type}")
        print(f"数据库路径: {config.database.path}")
        
        init_database()
        print("数据库初始化成功！")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        exit(1)
