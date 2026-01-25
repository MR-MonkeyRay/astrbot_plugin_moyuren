"""测试 utils/constants.py 常量定义"""

import pytest
from utils.constants import (
    PLUGIN_NAME,
    PLUGIN_VERSION,
    PLUGIN_AUTHOR,
    PLUGIN_DESC,
    PLUGIN_REPO,
    DEFAULT_API_ENDPOINTS,
    DEFAULT_TEMPLATE,
)


@pytest.mark.unit
class TestConstants:
    """测试常量定义"""

    def test_plugin_name_exists_and_type(self):
        """测试 PLUGIN_NAME 常量存在且为 str 类型"""
        assert isinstance(PLUGIN_NAME, str)
        assert PLUGIN_NAME == "moyuren"

    def test_plugin_version_exists_and_type(self):
        """测试 PLUGIN_VERSION 常量存在且为 str 类型"""
        assert isinstance(PLUGIN_VERSION, str)
        assert PLUGIN_VERSION == "3.0.0"

    def test_plugin_author_exists_and_type(self):
        """测试 PLUGIN_AUTHOR 常量存在且为 str 类型"""
        assert isinstance(PLUGIN_AUTHOR, str)
        assert len(PLUGIN_AUTHOR) > 0

    def test_plugin_desc_exists_and_type(self):
        """测试 PLUGIN_DESC 常量存在且为 str 类型"""
        assert isinstance(PLUGIN_DESC, str)
        assert len(PLUGIN_DESC) > 0

    def test_plugin_repo_exists_and_type(self):
        """测试 PLUGIN_REPO 常量存在且为 str 类型"""
        assert isinstance(PLUGIN_REPO, str)
        assert PLUGIN_REPO.startswith("https://")

    def test_default_api_endpoints_not_empty(self):
        """测试 DEFAULT_API_ENDPOINTS 为非空列表"""
        assert isinstance(DEFAULT_API_ENDPOINTS, list)
        assert len(DEFAULT_API_ENDPOINTS) > 0

    def test_default_api_endpoints_type(self):
        """测试 DEFAULT_API_ENDPOINTS 元素类型正确"""
        for endpoint in DEFAULT_API_ENDPOINTS:
            assert isinstance(endpoint, str)
            assert endpoint.startswith("http")

    def test_default_template_required_keys(self):
        """测试 DEFAULT_TEMPLATE 包含必要的键"""
        assert isinstance(DEFAULT_TEMPLATE, dict)
        assert "name" in DEFAULT_TEMPLATE
        assert "format" in DEFAULT_TEMPLATE

    def test_default_template_type(self):
        """测试 DEFAULT_TEMPLATE 类型正确"""
        assert isinstance(DEFAULT_TEMPLATE["name"], str)
        assert isinstance(DEFAULT_TEMPLATE["format"], str)

    def test_constant_values_correct(self):
        """测试常量值是否符合预期"""
        assert PLUGIN_NAME == "moyuren"
        assert PLUGIN_VERSION == "3.0.0"
        assert PLUGIN_AUTHOR == "MonkeyRay"
        assert "摸鱼人日历" in PLUGIN_DESC
        assert "github.com" in PLUGIN_REPO.lower()

    def test_default_template_format_contains_placeholder(self):
        """测试 DEFAULT_TEMPLATE 的 format 包含占位符"""
        assert "{time}" in DEFAULT_TEMPLATE["format"]
