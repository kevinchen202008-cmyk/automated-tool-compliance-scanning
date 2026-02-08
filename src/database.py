"""
数据库连接和初始化模块
Database connection and initialization module
"""

import os
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from src.config import get_config
from src.models import Base


# 全局变量
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_database_url() -> str:
    """
    获取数据库连接URL
    
    Returns:
        str: 数据库连接URL
    """
    config = get_config()
    db_config = config.database
    
    if db_config.type == "sqlite":
        # 确保数据库目录存在
        db_path = Path(db_config.path)
        db_dir = db_path.parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite 连接字符串
        return f"sqlite:///{db_path.absolute()}"
    
    elif db_config.type == "mysql":
        # MySQL 连接字符串
        user = db_config.user or ""
        password = db_config.password or ""
        host = db_config.host or "localhost"
        port = db_config.port or 3306
        database = db_config.database or "compliance_scanning"
        
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    
    else:
        raise ValueError(f"不支持的数据库类型: {db_config.type}")


def get_engine() -> Engine:
    """
    获取数据库引擎（单例模式）
    
    Returns:
        Engine: SQLAlchemy 引擎
    """
    global _engine
    
    if _engine is None:
        database_url = get_database_url()
        config = get_config()
        
        # SQLite 特殊配置
        if config.database.type == "sqlite":
            # 启用外键约束
            engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=config.service.debug
            )
            
            # 为 SQLite 启用外键约束
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        else:
            # MySQL 或其他数据库
            engine = create_engine(
                database_url,
                echo=config.service.debug,
                pool_pre_ping=True,
                pool_recycle=3600
            )
        
        _engine = engine
    
    return _engine


def get_session() -> sessionmaker:
    """
    获取数据库会话工厂（单例模式）
    
    Returns:
        sessionmaker: SQLAlchemy 会话工厂
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return _SessionLocal


def init_database() -> None:
    """
    初始化数据库：创建所有表
    
    Raises:
        Exception: 如果数据库初始化失败
    """
    try:
        engine = get_engine()
        
        # 确保所有模型都被导入和注册
        from src import models  # 导入所有模型以确保它们被注册到Base.metadata
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        print(f"数据库初始化成功: {get_config().database.path}")
    except Exception as e:
        raise Exception(f"数据库初始化失败: {str(e)}")


def get_db() -> Session:
    """
    获取数据库会话（用于依赖注入）
    
    Yields:
        Session: 数据库会话
    """
    SessionLocal = get_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_exists() -> bool:
    """
    检查数据库文件是否存在
    
    Returns:
        bool: 数据库文件是否存在
    """
    config = get_config()
    if config.database.type == "sqlite":
        db_path = Path(config.database.path)
        return db_path.exists()
    else:
        # MySQL 等需要连接测试
        try:
            engine = get_engine()
            with engine.connect():
                return True
        except Exception:
            return False
