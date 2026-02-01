"""配置数据模型"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class GroupSettings:
    """群组设置"""
    custom_time: Optional[str] = None  # 自定义发送时间，格式 HH:MM


@dataclass
class PluginConfig:
    """插件配置"""
    group_settings: Dict[str, GroupSettings] = field(default_factory=dict)
    api_endpoints: List[str] = field(default_factory=list)
    templates: List[Dict[str, Any]] = field(default_factory=list)


__all__ = ["GroupSettings", "PluginConfig"]
