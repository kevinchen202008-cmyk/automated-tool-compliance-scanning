"""
工具管理 API 接口测试
Tests for tool management API endpoints
"""

import pytest


class TestCreateTool:
    """POST /api/v1/tools"""

    def test_create_tool_success(self, client):
        resp = client.post("/api/v1/tools", json={"name": "Docker"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Docker"
        assert data["id"] > 0

    def test_create_tool_duplicate_returns_existing(self, client):
        """同名工具应返回已有记录"""
        r1 = client.post("/api/v1/tools", json={"name": "Git"})
        r2 = client.post("/api/v1/tools", json={"name": "Git"})
        assert r1.json()["id"] == r2.json()["id"]

    def test_create_tool_empty_name(self, client):
        resp = client.post("/api/v1/tools", json={"name": ""})
        assert resp.status_code == 422  # Pydantic 验证失败


class TestBatchCreateTools:
    """POST /api/v1/tools/batch"""

    def test_batch_create_tools(self, client):
        resp = client.post(
            "/api/v1/tools/batch",
            json={"tools": ["Docker", "Kubernetes", "Podman"]},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total"] == 3
        assert data["created"] + data["existing"] == data["total"]
        assert len(data["tools"]) >= 1

    def test_batch_create_tools_dedup(self, client):
        """批量创建中的重复工具应被去重"""
        # 先创建一次
        client.post("/api/v1/tools/batch", json={"tools": ["Redis"]})
        # 再次创建（含已有 + 新建）
        resp = client.post(
            "/api/v1/tools/batch",
            json={"tools": ["Redis", "Nginx"]},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["existing"] >= 1

    def test_batch_create_empty_list(self, client):
        resp = client.post("/api/v1/tools/batch", json={"tools": []})
        assert resp.status_code == 422  # min_items=1 验证
