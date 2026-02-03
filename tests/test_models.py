"""测试 models/config_schema.py 数据模型"""

import pytest
from dataclasses import asdict
from models.config_schema import GroupSettings, PluginConfig


@pytest.mark.unit
class TestGroupSettings:
    """测试 GroupSettings 数据类"""

    def test_group_settings_default_values(self):
        """测试默认值"""
        settings = GroupSettings()
        assert settings.custom_time is None

    def test_group_settings_set_custom_time(self):
        """测试设置 custom_time"""
        settings = GroupSettings(custom_time="09:00")
        assert settings.custom_time == "09:00"

    def test_group_settings_serialization(self):
        """测试数据类的序列化"""
        settings = GroupSettings(custom_time="10:30")
        data = asdict(settings)
        assert data == {"custom_time": "10:30"}

    def test_group_settings_none_serialization(self):
        """测试 None 值的序列化"""
        settings = GroupSettings()
        data = asdict(settings)
        assert data == {"custom_time": None}


@pytest.mark.unit
class TestPluginConfig:
    """测试 PluginConfig 数据类"""

    def test_plugin_config_default_values(self):
        """测试默认值"""
        config = PluginConfig()
        assert config.group_settings == {}
        assert config.api_endpoints == []
        assert config.templates == []

    def test_plugin_config_set_fields(self):
        """测试设置各个字段"""
        config = PluginConfig(
            api_endpoints=["https://api.example.com"],
            templates=[{"format": "test {time}"}],
        )
        assert config.api_endpoints == ["https://api.example.com"]
        assert config.templates == [{"format": "test {time}"}]

    def test_plugin_config_group_settings_operations(self):
        """测试 group_settings 字典操作"""
        config = PluginConfig()

        # 添加群组设置
        config.group_settings["123456"] = GroupSettings(custom_time="09:00")
        assert "123456" in config.group_settings
        assert config.group_settings["123456"].custom_time == "09:00"

        # 修改群组设置
        config.group_settings["123456"].custom_time = "10:00"
        assert config.group_settings["123456"].custom_time == "10:00"

        # 删除群组设置
        del config.group_settings["123456"]
        assert "123456" not in config.group_settings

    def test_plugin_config_serialization(self):
        """测试数据类的序列化"""
        config = PluginConfig(
            group_settings={"123": GroupSettings(custom_time="09:00")},
            api_endpoints=["https://api.example.com"],
            templates=[{"format": "test {time}"}],
        )
        data = asdict(config)

        assert data["group_settings"]["123"]["custom_time"] == "09:00"
        assert data["api_endpoints"] == ["https://api.example.com"]
        assert data["templates"] == [{"format": "test {time}"}]

    def test_plugin_config_multiple_groups(self):
        """测试多个群组设置"""
        config = PluginConfig()
        config.group_settings["group1"] = GroupSettings(custom_time="09:00")
        config.group_settings["group2"] = GroupSettings(custom_time="10:00")
        config.group_settings["group3"] = GroupSettings()

        assert len(config.group_settings) == 3
        assert config.group_settings["group1"].custom_time == "09:00"
        assert config.group_settings["group2"].custom_time == "10:00"
        assert config.group_settings["group3"].custom_time is None
