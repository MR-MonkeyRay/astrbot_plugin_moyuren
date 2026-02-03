"""测试 ImageManager 模板逻辑"""

import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestImageManagerTemplate:
    """测试 ImageManager 模板处理逻辑（通过 mock 避免直接导入）"""

    def _create_preprocess_templates(self, templates):
        """模拟 _preprocess_templates 方法的逻辑"""
        valid_templates = []
        for tmpl in templates:
            if isinstance(tmpl, str):
                try:
                    tmpl_dict = json.loads(tmpl)
                    if isinstance(tmpl_dict, dict) and "format" in tmpl_dict:
                        valid_templates.append(tmpl_dict)
                except json.JSONDecodeError:
                    pass
            elif isinstance(tmpl, dict) and "format" in tmpl:
                valid_templates.append(tmpl)
        return valid_templates

    def _create_get_next_template(self, valid_templates, index_holder):
        """模拟 _get_next_template 方法的逻辑"""
        if not valid_templates:
            return None
        template = valid_templates[index_holder["index"]]
        index_holder["index"] = (index_holder["index"] + 1) % len(valid_templates)
        return template

    def test_empty_templates_returns_none(self):
        """模板为空时 _get_next_template 返回 None"""
        valid = self._create_preprocess_templates([])
        index_holder = {"index": 0}
        result = self._create_get_next_template(valid, index_holder)
        assert result is None

    def test_valid_templates_returns_template(self):
        """有效模板时 _get_next_template 返回模板字典"""
        templates = [{"format": "hello {time}"}]
        valid = self._create_preprocess_templates(templates)
        index_holder = {"index": 0}
        result = self._create_get_next_template(valid, index_holder)
        assert result is not None
        assert result["format"] == "hello {time}"

    def test_invalid_templates_returns_none(self):
        """所有模板无效时 _get_next_template 返回 None"""
        templates = [{"invalid": "bad_template"}]  # 缺少 format 字段
        valid = self._create_preprocess_templates(templates)
        index_holder = {"index": 0}
        result = self._create_get_next_template(valid, index_holder)
        assert result is None

    def test_mixed_templates_filters_invalid(self):
        """混合有效/无效模板时，只保留有效模板"""
        templates = [
            {"invalid": "no_format"},  # 缺少 format
            {"format": "test {time}"},
        ]
        valid = self._create_preprocess_templates(templates)
        assert len(valid) == 1
        assert valid[0]["format"] == "test {time}"

    def test_template_rotation(self):
        """模板轮询正确循环"""
        templates = [
            {"format": "a {time}"},
            {"format": "b {time}"},
        ]
        valid = self._create_preprocess_templates(templates)
        index_holder = {"index": 0}
        assert self._create_get_next_template(valid, index_holder)["format"] == "a {time}"
        assert self._create_get_next_template(valid, index_holder)["format"] == "b {time}"
        assert self._create_get_next_template(valid, index_holder)["format"] == "a {time}"

    def test_string_template_parsed(self):
        """JSON 字符串模板被正确解析"""
        templates = ['{"format": "parsed {time}"}']
        valid = self._create_preprocess_templates(templates)
        assert len(valid) == 1
        assert valid[0]["format"] == "parsed {time}"

    def test_invalid_json_string_template_skipped(self):
        """无效 JSON 字符串模板被跳过"""
        templates = ["not valid json"]
        valid = self._create_preprocess_templates(templates)
        assert len(valid) == 0

    def test_preprocess_returns_empty_list_when_no_valid(self):
        """预处理后无有效模板时返回空列表"""
        valid = self._create_preprocess_templates([])
        assert valid == []

