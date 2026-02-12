"""
工具服务单元测试
Unit tests for tool_service module
"""

import pytest
from src.services.tool_service import (
    validate_tool_name,
    parse_tool_names,
    get_or_create_tool,
    batch_create_tools,
)


class TestValidateToolName:

    def test_valid_names(self):
        assert validate_tool_name("Docker")[0] is True
        assert validate_tool_name("Docker Desktop")[0] is True
        assert validate_tool_name("node.js")[0] is True
        assert validate_tool_name("my-tool_v2")[0] is True

    def test_empty_name(self):
        ok, msg = validate_tool_name("")
        assert ok is False
        assert "不能为空" in msg

    def test_spaces_only(self):
        ok, msg = validate_tool_name("   ")
        assert ok is False

    def test_too_long(self):
        ok, msg = validate_tool_name("a" * 101)
        assert ok is False
        assert "100" in msg

    def test_invalid_chars(self):
        ok, msg = validate_tool_name("tool@#!")
        assert ok is False


class TestParseToolNames:

    def test_newline_separated(self):
        result = parse_tool_names("Docker\nGit\nPodman")
        assert result == ["Docker", "Git", "Podman"]

    def test_comma_separated(self):
        result = parse_tool_names("Docker, Git, Podman")
        assert result == ["Docker", "Git", "Podman"]

    def test_deduplicate(self):
        result = parse_tool_names("Docker\nDocker\ndocker")
        assert len(result) == 1

    def test_empty(self):
        assert parse_tool_names("") == []
        assert parse_tool_names(None) == []


class TestGetOrCreateTool:
    """需要数据库 session 的测试"""

    def test_create_new_tool(self, db):
        tool = get_or_create_tool(db, "NewTool")
        assert tool.id is not None
        assert tool.name == "NewTool"

    def test_get_existing_tool(self, db):
        t1 = get_or_create_tool(db, "SameTool")
        t2 = get_or_create_tool(db, "SameTool")
        assert t1.id == t2.id

    def test_case_insensitive(self, db):
        t1 = get_or_create_tool(db, "Docker")
        t2 = get_or_create_tool(db, "docker")
        assert t1.id == t2.id

    def test_invalid_name_raises(self, db):
        with pytest.raises(ValueError):
            get_or_create_tool(db, "")


class TestBatchCreateTools:

    def test_batch_create(self, db):
        tools, existing = batch_create_tools(db, ["ToolX", "ToolY"])
        assert len(tools) == 2
        assert existing == 0

    def test_batch_with_existing(self, db):
        get_or_create_tool(db, "Existing")
        tools, existing = batch_create_tools(db, ["Existing", "Brand-New"])
        assert existing == 1
        assert len(tools) == 2
