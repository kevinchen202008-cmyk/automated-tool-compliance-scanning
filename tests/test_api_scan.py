"""
扫描与报告 API 接口测试
Tests for scan and report API endpoints
"""

import pytest


class TestScanAPI:
    """扫描相关接口"""

    def _create_tools(self, client, names):
        resp = client.post("/api/v1/tools/batch", json={"tools": names})
        assert resp.status_code == 201
        return [t["id"] for t in resp.json()["tools"]]

    def test_start_scan_nonexistent_tool(self, client):
        """扫描不存在的工具应返回 404"""
        resp = client.post(
            "/api/v1/scan/start",
            json={"tool_ids": [99999]},
        )
        assert resp.status_code == 404

    def test_start_scan_empty_list(self, client):
        resp = client.post("/api/v1/scan/start", json={"tool_ids": []})
        assert resp.status_code == 422  # min_items=1

    def test_get_scan_status_nonexistent(self, client):
        """查询不存在的扫描任务应返回 404"""
        resp = client.get("/api/v1/scan/status/99999")
        assert resp.status_code == 404


class TestReportAPI:
    """报告相关接口"""

    def test_get_report_not_found(self, client):
        resp = client.get("/api/v1/reports/99999")
        assert resp.status_code == 404

    def test_export_report_not_found(self, client):
        resp = client.get("/api/v1/reports/99999/export")
        assert resp.status_code == 404


class TestComplianceScan:
    """一体化合规扫描接口"""

    def test_compliance_scan_empty_tools(self, client):
        resp = client.post(
            "/api/v1/compliance/scan",
            json={"tools": []},
        )
        assert resp.status_code == 422  # min_items=1
