"""
知识库服务单元测试
Unit tests for knowledge_base_service module
"""

import pytest
from src.services.knowledge_base_service import (
    create_or_update_knowledge_base,
    get_knowledge_base_entry,
    get_knowledge_base_dict,
    list_all_knowledge_base_entries,
    delete_knowledge_base_entry,
    knowledge_base_entry_to_dict,
)


SAMPLE_DATA = {
    "license_type": "MIT",
    "license_version": "1.0",
    "license_mode": "开源",
    "company_name": "TestCorp",
    "company_country": "US",
    "company_headquarters": "NYC",
    "china_office": False,
    "commercial_license_required": False,
    "free_for_commercial": True,
    "commercial_restrictions": None,
    "user_limit": None,
    "feature_restrictions": None,
    "alternative_tools": [],
    "data_usage": None,
    "privacy_policy": None,
    "service_restrictions": None,
    "risk_points": [],
    "compliance_notes": None,
}


class TestKnowledgeBaseService:

    def test_create_entry(self, db):
        entry = create_or_update_knowledge_base(db, "TestTool", SAMPLE_DATA)
        assert entry.id is not None
        assert entry.tool_name == "TestTool"
        assert entry.license_type == "MIT"

    def test_update_entry(self, db):
        create_or_update_knowledge_base(db, "UpdateMe", SAMPLE_DATA)
        updated = dict(SAMPLE_DATA, license_type="Apache-2.0")
        entry = create_or_update_knowledge_base(db, "UpdateMe", updated)
        assert entry.license_type == "Apache-2.0"

    def test_get_entry(self, db):
        create_or_update_knowledge_base(db, "FindMe", SAMPLE_DATA)
        entry = get_knowledge_base_entry(db, "FindMe")
        assert entry is not None
        assert entry.tool_name == "FindMe"

    def test_get_entry_case_insensitive(self, db):
        create_or_update_knowledge_base(db, "CaseTool", SAMPLE_DATA)
        entry = get_knowledge_base_entry(db, "casetool")
        assert entry is not None

    def test_get_entry_not_found(self, db):
        entry = get_knowledge_base_entry(db, "NoSuch")
        assert entry is None

    def test_get_dict(self, db):
        create_or_update_knowledge_base(db, "DictTool", SAMPLE_DATA)
        d = get_knowledge_base_dict(db, "DictTool")
        assert d is not None
        assert d["license_type"] == "MIT"

    def test_list_entries(self, db):
        create_or_update_knowledge_base(db, "ListA", SAMPLE_DATA)
        create_or_update_knowledge_base(db, "ListB", SAMPLE_DATA)
        entries = list_all_knowledge_base_entries(db)
        assert len(entries) >= 2

    def test_list_entries_order_by_updated(self, db):
        create_or_update_knowledge_base(db, "OrderA", SAMPLE_DATA)
        create_or_update_knowledge_base(db, "OrderB", SAMPLE_DATA)
        entries = list_all_knowledge_base_entries(db, order_by="updated_at")
        assert len(entries) >= 2

    def test_delete_entry(self, db):
        create_or_update_knowledge_base(db, "DeleteMe", SAMPLE_DATA)
        result = delete_knowledge_base_entry(db, "DeleteMe")
        assert result is True
        assert get_knowledge_base_entry(db, "DeleteMe") is None

    def test_delete_nonexistent(self, db):
        result = delete_knowledge_base_entry(db, "Ghost")
        assert result is False

    def test_entry_to_dict(self, db):
        entry = create_or_update_knowledge_base(db, "DictConvert", SAMPLE_DATA)
        d = knowledge_base_entry_to_dict(entry)
        assert isinstance(d, dict)
        assert d["license_type"] == "MIT"
        assert isinstance(d["alternative_tools"], list)
