"""
工具信息库 API 接口测试
Tests for knowledge base (tool info store) API endpoints
"""

import pytest


KB_DATA = {
    "license_type": "Apache-2.0",
    "license_version": "2.0",
    "license_mode": "开源",
    "company_name": "Test Corp",
    "company_country": "US",
    "company_headquarters": "San Francisco",
    "china_office": True,
    "commercial_license_required": False,
    "free_for_commercial": True,
    "commercial_restrictions": None,
    "user_limit": None,
    "feature_restrictions": None,
    "alternative_tools": [{"name": "AltTool", "type": "open-source"}],
}


class TestKnowledgeBaseCRUD:
    """工具信息库增删改查"""

    def _put(self, client, name, data=None):
        return client.put(
            f"/api/v1/knowledge-base/{name}",
            json=data or KB_DATA,
        )

    def test_create_entry(self, client):
        resp = self._put(client, "TestTool")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tool_name"] == "TestTool"
        assert data["message"] == "知识库条目已更新"

    def test_get_entry(self, client):
        self._put(client, "Kubectl")
        resp = client.get("/api/v1/knowledge-base/Kubectl")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tool_name"] == "Kubectl"
        assert data["data"]["license_type"] == "Apache-2.0"

    def test_get_entry_not_found(self, client):
        resp = client.get("/api/v1/knowledge-base/NonExistent")
        assert resp.status_code == 404

    def test_update_entry(self, client):
        self._put(client, "Helm")
        updated = dict(KB_DATA, license_type="MIT")
        resp = self._put(client, "Helm", updated)
        assert resp.status_code == 200
        assert resp.json()["data"]["license_type"] == "MIT"

    def test_delete_entry(self, client):
        self._put(client, "TempTool")
        resp = client.delete("/api/v1/knowledge-base/TempTool")
        assert resp.status_code == 204
        # 删除后应该 404
        resp2 = client.get("/api/v1/knowledge-base/TempTool")
        assert resp2.status_code == 404

    def test_delete_entry_not_found(self, client):
        resp = client.delete("/api/v1/knowledge-base/NoSuchTool")
        assert resp.status_code == 404

    def test_list_entries(self, client):
        self._put(client, "ToolA")
        self._put(client, "ToolB")
        resp = client.get("/api/v1/knowledge-base")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        names = [e["tool_name"] for e in data["entries"]]
        assert "ToolA" in names
        assert "ToolB" in names

    def test_list_entries_order_by_updated(self, client):
        self._put(client, "OldTool")
        self._put(client, "NewTool")
        resp = client.get("/api/v1/knowledge-base?order_by=updated_at")
        assert resp.status_code == 200

    def test_get_detail_for_display(self, client):
        self._put(client, "DetailTool")
        resp = client.get("/api/v1/knowledge-base/DetailTool/detail")
        assert resp.status_code == 200
        data = resp.json()
        assert "license_info" in data
        assert "company_info" in data
        assert "commercial_restrictions" in data
        assert "alternative_tools" in data
        assert data["license_info"]["license_type"] == "Apache-2.0"

    def test_get_detail_not_found(self, client):
        resp = client.get("/api/v1/knowledge-base/NoDetail/detail")
        assert resp.status_code == 404
