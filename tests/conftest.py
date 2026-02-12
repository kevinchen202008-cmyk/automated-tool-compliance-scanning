"""
Pytest 公共 fixtures
Shared fixtures for all test modules
"""

import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from src.models import Base


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """设置测试环境变量，确保使用默认配置而非本地 config.yaml"""
    # 指向一个不存在的路径，使 load_config 回退到默认配置
    os.environ["CONFIG_PATH"] = "__test_nonexistent__.yaml"
    yield
    os.environ.pop("CONFIG_PATH", None)


@pytest.fixture()
def test_engine():
    """创建内存 SQLite 引擎（每个测试隔离）"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _rec):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(test_engine) -> Session:
    """提供独立的数据库 Session，测试结束后自动回滚"""
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(test_engine, db):
    """
    提供 FastAPI TestClient，
    使用测试用的内存 DB 覆盖默认 get_db 依赖。
    """
    from fastapi.testclient import TestClient
    from src.main import app
    from src.database import get_db as _get_db

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[_get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
