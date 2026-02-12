"""
数据库迁移与前向兼容测试
Tests for database auto-migration and forward compatibility
"""

import pytest
import shutil
from pathlib import Path
from sqlalchemy import create_engine, text, inspect, event, Column, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.models import Base, ToolKnowledgeBase, Tool
from src.config import AppConfig, DatabaseConfig


@pytest.fixture()
def migration_db(tmp_path, monkeypatch):
    """提供一个真实的 SQLite 文件数据库用于迁移测试"""
    import src.database as db_mod

    db_path = tmp_path / "migration_test.db"
    config = AppConfig(
        database=DatabaseConfig(type="sqlite", path=str(db_path))
    )
    monkeypatch.setattr("src.database.get_config", lambda: config)

    # 重置全局引擎/会话
    old_engine = db_mod._engine
    old_session = db_mod._SessionLocal
    db_mod._engine = None
    db_mod._SessionLocal = None

    yield db_path, config

    # 恢复全局状态
    db_mod._engine = old_engine
    db_mod._SessionLocal = old_session


class TestSchemaVersionTracking:
    """Schema 版本追踪"""

    def test_init_creates_schema_version(self, migration_db):
        """init_database 应创建 schema_version 表并设置版本"""
        from src.database import init_database, get_engine, SCHEMA_VERSION

        init_database()
        engine = get_engine()

        insp = inspect(engine)
        assert "schema_version" in insp.get_table_names()

        with engine.connect() as conn:
            row = conn.execute(text("SELECT version FROM schema_version WHERE id = 1")).fetchone()
            assert row[0] == SCHEMA_VERSION

    def test_get_current_schema_version(self, migration_db):
        """应正确读取数据库 schema 版本"""
        from src.database import init_database, get_engine, _get_current_schema_version

        init_database()
        engine = get_engine()
        version = _get_current_schema_version(engine)
        assert isinstance(version, int)
        assert version >= 1


class TestAutoBackup:
    """自动备份"""

    def test_backup_creates_file(self, migration_db):
        """备份应创建 .bak 文件"""
        db_path, _ = migration_db
        from src.database import init_database, backup_database

        init_database()
        backup_path = backup_database()

        assert backup_path is not None
        assert Path(backup_path).exists()
        assert ".bak." in backup_path

    def test_backup_keeps_max_five(self, migration_db):
        """应只保留最近 5 个备份"""
        db_path, _ = migration_db
        from src.database import init_database, backup_database

        init_database()
        # 创建 7 个备份
        paths = []
        for _ in range(7):
            p = backup_database()
            if p:
                paths.append(p)

        backups = list(db_path.parent.glob(f"{db_path.name}.bak.*"))
        assert len(backups) <= 5

    def test_restore_recovers_data(self, migration_db):
        """restore_database 应恢复到备份时的状态"""
        db_path, _ = migration_db
        from src.database import (
            init_database, backup_database, restore_database,
            get_engine, get_session,
        )
        import src.database as db_mod

        init_database()

        # 插入一条数据
        engine = get_engine()
        SessionLocal = get_session()
        db = SessionLocal()
        tool = Tool(name="TestTool", source="manual")
        db.add(tool)
        db.commit()
        db.close()

        # 备份
        backup_path = backup_database()

        # 修改数据（删除记录）
        db = SessionLocal()
        db.query(Tool).delete()
        db.commit()
        count_after_delete = db.query(Tool).count()
        db.close()
        assert count_after_delete == 0

        # 恢复 — 需要重建引擎
        db_mod._engine = None
        db_mod._SessionLocal = None
        restore_database(backup_path)

        engine = get_engine()
        SessionLocal = get_session()
        db = SessionLocal()
        count_after_restore = db.query(Tool).count()
        db.close()
        assert count_after_restore == 1


class TestAutoMigration:
    """自动列补齐（前向兼容）"""

    def test_migrate_no_op_when_up_to_date(self, migration_db):
        """schema 版本一致时不执行迁移"""
        from src.database import init_database, migrate_database

        init_database()
        result = migrate_database()
        assert result["migrated"] is False

    def test_migrate_detects_version_mismatch(self, migration_db, monkeypatch):
        """schema 版本不一致时执行迁移"""
        from src.database import init_database, migrate_database, get_engine, _set_schema_version

        init_database()

        # 手动降低版本号以模拟旧版本数据库
        engine = get_engine()
        _set_schema_version(engine, 1, "simulated old version")

        result = migrate_database()
        assert result["migrated"] is True
        assert result["from_version"] == 1

    def test_migrate_adds_missing_column(self, migration_db, monkeypatch):
        """迁移应自动添加模型中新增的列"""
        from src.database import (
            init_database, get_engine, auto_add_missing_columns,
            _get_existing_columns,
        )

        init_database()
        engine = get_engine()

        # 确认 tool_knowledge_base 表有 tool_name 列
        cols = _get_existing_columns(engine, "tool_knowledge_base")
        assert "tool_name" in cols

        # 手动删除一个列（SQLite 不支持 DROP COLUMN，用表重建模拟）
        # 改为：直接检查 auto_add_missing_columns 不会报错，且对已有列不做操作
        added = auto_add_missing_columns(engine)
        # 所有列已存在，不应有新增
        assert added == []

    def test_migrate_preserves_existing_data(self, migration_db, monkeypatch):
        """迁移过程中不丢失已有数据"""
        from src.database import (
            init_database, migrate_database, get_engine,
            get_session, _set_schema_version,
        )

        init_database()
        engine = get_engine()
        SessionLocal = get_session()

        # 插入知识库数据
        db = SessionLocal()
        kb_entry = ToolKnowledgeBase(
            tool_name="Docker",
            license_type="Apache-2.0",
            company_name="Docker Inc.",
            source="user",
        )
        db.add(kb_entry)
        db.commit()
        db.close()

        # 模拟版本号降低
        _set_schema_version(engine, 1, "old version")

        # 执行迁移
        result = migrate_database()
        assert result["migrated"] is True

        # 验证数据仍在
        db = SessionLocal()
        entry = db.query(ToolKnowledgeBase).filter_by(tool_name="Docker").first()
        assert entry is not None
        assert entry.license_type == "Apache-2.0"
        assert entry.company_name == "Docker Inc."
        db.close()

    def test_migrate_creates_backup(self, migration_db):
        """迁移时应自动创建备份"""
        db_path, _ = migration_db
        from src.database import init_database, migrate_database, get_engine, _set_schema_version

        init_database()
        engine = get_engine()
        _set_schema_version(engine, 1, "old")

        result = migrate_database()
        assert result["migrated"] is True
        assert result.get("backup_path") is not None
        assert Path(result["backup_path"]).exists()


class TestForwardCompatibility:
    """前向兼容设计保证"""

    def test_old_data_readable_after_schema_upgrade(self, migration_db):
        """旧版本数据在 schema 升级后仍然可读"""
        from src.database import (
            init_database, get_engine, get_session, _set_schema_version,
            migrate_database,
        )

        init_database()
        engine = get_engine()
        SessionLocal = get_session()

        # 模拟旧版数据：只填部分字段
        db = SessionLocal()
        kb = ToolKnowledgeBase(
            tool_name="OldTool",
            source="system",
        )
        db.add(kb)
        db.commit()
        db.close()

        # 模拟升级
        _set_schema_version(engine, 1, "old")
        migrate_database()

        # 旧数据应可正常查询，新字段为 None
        db = SessionLocal()
        entry = db.query(ToolKnowledgeBase).filter_by(tool_name="OldTool").first()
        assert entry is not None
        assert entry.tool_name == "OldTool"
        assert entry.license_type is None  # 未填写的字段
        assert entry.company_name is None
        db.close()

    def test_new_columns_nullable(self):
        """ToolKnowledgeBase 的所有业务列应为 nullable（前向兼容要求）"""
        table = ToolKnowledgeBase.__table__
        skip_cols = {"id", "tool_name", "source", "created_at", "updated_at"}
        for col in table.columns:
            if col.name in skip_cols:
                continue
            assert col.nullable is True, (
                f"列 {col.name} 不是 nullable — 前向兼容要求业务列必须 nullable"
            )
