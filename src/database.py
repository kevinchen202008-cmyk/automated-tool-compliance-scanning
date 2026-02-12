"""
数据库连接、初始化与自动迁移模块
Database connection, initialization, and auto-migration module

升级策略（前向兼容）：
- 只添加新列，不删除/重命名旧列
- 新列必须为 nullable 或有默认值
- 每次启动时自动检测 schema 差异并补齐
- SQLite 升级前自动备份数据库文件
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, event, inspect, text, Column, Integer, String, DateTime
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import func
from src.config import get_config
from src.models import Base


# ==================== 全局变量 ====================

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None

# 当前 schema 版本（每次有 schema 变更时递增）
SCHEMA_VERSION = 2


# ==================== 连接与引擎 ====================


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


# ==================== 数据库备份 ====================


def backup_database() -> Optional[str]:
    """
    备份 SQLite 数据库文件。
    备份文件保存在同目录下，格式：{原文件名}.bak.{时间戳}
    
    Returns:
        Optional[str]: 备份文件路径，非 SQLite 返回 None
    """
    config = get_config()
    if config.database.type != "sqlite":
        return None
    
    db_path = Path(config.database.path)
    if not db_path.exists():
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.name}.bak.{timestamp}"
    shutil.copy2(str(db_path), str(backup_path))
    
    # 只保留最近 5 个备份
    backups = sorted(db_path.parent.glob(f"{db_path.name}.bak.*"), key=lambda p: p.stat().st_mtime)
    for old_backup in backups[:-5]:
        old_backup.unlink(missing_ok=True)
    
    return str(backup_path)


def restore_database(backup_path: str) -> None:
    """
    从备份恢复 SQLite 数据库文件。
    
    Args:
        backup_path: 备份文件路径
    """
    config = get_config()
    if config.database.type != "sqlite":
        return
    
    db_path = Path(config.database.path)
    backup = Path(backup_path)
    if backup.exists():
        shutil.copy2(str(backup), str(db_path))


# ==================== Schema 版本追踪 ====================


def _ensure_schema_version_table(engine: Engine) -> None:
    """确保 schema_version 表存在"""
    with engine.connect() as conn:
        insp = inspect(engine)
        if "schema_version" not in insp.get_table_names():
            conn.execute(text(
                "CREATE TABLE schema_version ("
                "  id INTEGER PRIMARY KEY,"
                "  version INTEGER NOT NULL,"
                "  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
                "  description TEXT"
                ")"
            ))
            conn.execute(text(
                "INSERT INTO schema_version (id, version, description) "
                "VALUES (1, 1, 'initial schema')"
            ))
            conn.commit()


def _get_current_schema_version(engine: Engine) -> int:
    """获取当前数据库的 schema 版本"""
    _ensure_schema_version_table(engine)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version FROM schema_version WHERE id = 1"))
        row = result.fetchone()
        return row[0] if row else 0


def _set_schema_version(engine: Engine, version: int, description: str = "") -> None:
    """更新 schema 版本"""
    with engine.connect() as conn:
        conn.execute(text(
            "UPDATE schema_version SET version = :v, applied_at = CURRENT_TIMESTAMP, "
            "description = :d WHERE id = 1"
        ), {"v": version, "d": description})
        conn.commit()


# ==================== 自动列补齐（前向兼容） ====================


def _get_existing_columns(engine: Engine, table_name: str) -> List[str]:
    """获取表中已存在的列名列表"""
    insp = inspect(engine)
    if table_name not in insp.get_table_names():
        return []
    columns = insp.get_columns(table_name)
    return [col["name"] for col in columns]


def _get_column_ddl_type(column: Column, db_type: str) -> str:
    """
    将 SQLAlchemy Column 类型转换为 DDL 类型字符串。
    
    Args:
        column: SQLAlchemy Column 对象
        db_type: 数据库类型 (sqlite/mysql)
    """
    from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, JSON
    col_type = type(column.type)
    
    if col_type == String:
        length = getattr(column.type, "length", 255) or 255
        return f"VARCHAR({length})"
    elif col_type == Integer:
        return "INTEGER"
    elif col_type == Float:
        return "FLOAT" if db_type == "mysql" else "REAL"
    elif col_type == Boolean:
        return "BOOLEAN" if db_type == "mysql" else "INTEGER"
    elif col_type == Text:
        return "TEXT"
    elif col_type == DateTime:
        return "TIMESTAMP" if db_type == "mysql" else "DATETIME"
    elif col_type == JSON:
        return "JSON" if db_type == "mysql" else "TEXT"
    else:
        return "TEXT"


def auto_add_missing_columns(engine: Engine) -> List[str]:
    """
    自动检测所有 ORM 模型与数据库表的列差异，补齐缺失列。
    
    规则（前向兼容）：
    - 只添加新列，不删除/重命名旧列
    - 新列必须为 nullable 或有 server_default
    - 仅在 schema 版本变更时执行
    
    Returns:
        List[str]: 成功添加的列描述列表
    """
    config = get_config()
    db_type = config.database.type
    added = []
    
    from src import models  # 确保所有模型已注册
    
    for table in Base.metadata.sorted_tables:
        table_name = table.name
        existing_cols = _get_existing_columns(engine, table_name)
        
        if not existing_cols:
            # 表不存在，create_all 会创建它
            continue
        
        for column in table.columns:
            if column.name in existing_cols:
                continue
            
            # 新列必须 nullable 或有默认值，否则跳过（避免破坏已有数据）
            if not column.nullable and column.default is None and column.server_default is None:
                continue
            
            col_ddl = _get_column_ddl_type(column, db_type)
            default_clause = ""
            if column.server_default is not None:
                default_clause = f" DEFAULT {column.server_default.arg}"
            elif column.default is not None and hasattr(column.default, "arg") and not callable(column.default.arg):
                default_clause = f" DEFAULT '{column.default.arg}'"
            
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_ddl}{default_clause}"
            
            try:
                with engine.connect() as conn:
                    conn.execute(text(alter_sql))
                    conn.commit()
                desc = f"{table_name}.{column.name} ({col_ddl})"
                added.append(desc)
            except Exception:
                # 列可能已存在（并发/缓存），安全忽略
                pass
    
    return added


# ==================== 初始化与迁移 ====================


def init_database() -> None:
    """
    初始化数据库：创建所有表
    
    Raises:
        Exception: 如果数据库初始化失败
    """
    try:
        engine = get_engine()
        
        # 确保所有模型都被导入和注册
        from src import models  # noqa: F401
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        # 初始化 schema 版本
        _ensure_schema_version_table(engine)
        _set_schema_version(engine, SCHEMA_VERSION, "initial creation")
        
        print(f"数据库初始化成功: {get_config().database.path}")
    except Exception as e:
        raise Exception(f"数据库初始化失败: {str(e)}")


def migrate_database() -> Dict[str, Any]:
    """
    自动迁移数据库 schema（升级时调用）。
    
    流程：
    1. 检测当前 schema 版本是否低于代码中的 SCHEMA_VERSION
    2. 如果需要迁移：备份数据库 → 补齐缺失列 → 创建新表 → 更新版本号
    3. 迁移失败时自动回滚到备份
    
    Returns:
        Dict[str, Any]: 迁移结果（含 migrated, backup_path, added_columns 等）
    """
    engine = get_engine()
    from src import models  # noqa: F401
    
    current_version = _get_current_schema_version(engine)
    
    if current_version >= SCHEMA_VERSION:
        return {"migrated": False, "reason": "schema is up to date", "version": current_version}
    
    # 需要迁移
    backup_path = backup_database()
    
    try:
        # 1. 补齐缺失列（前向兼容：只加不删）
        added_columns = auto_add_missing_columns(engine)
        
        # 2. 创建可能的新表（create_all 跳过已存在的表）
        Base.metadata.create_all(bind=engine)
        
        # 3. 更新 schema 版本
        _set_schema_version(
            engine,
            SCHEMA_VERSION,
            f"auto-migrated from v{current_version} to v{SCHEMA_VERSION}"
        )
        
        return {
            "migrated": True,
            "from_version": current_version,
            "to_version": SCHEMA_VERSION,
            "backup_path": backup_path,
            "added_columns": added_columns,
        }
    except Exception as e:
        # 迁移失败，回滚
        if backup_path:
            try:
                restore_database(backup_path)
            except Exception:
                pass  # 回滚也失败则保留损坏状态，由运维手动处理
        raise Exception(f"数据库迁移失败（已尝试回滚）: {e}")


# ==================== 会话与依赖注入 ====================


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
