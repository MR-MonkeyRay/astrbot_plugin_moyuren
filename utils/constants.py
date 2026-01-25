"""常量定义"""

# 插件信息
PLUGIN_NAME = "moyuren"
PLUGIN_VERSION = "3.0.0"
PLUGIN_AUTHOR = "MonkeyRay"
PLUGIN_DESC = "一个功能完善的摸鱼人日历插件"
PLUGIN_REPO = "https://github.com/MR-MonkeyRay/astrbot_plugin_moyuren"

# 默认配置
DEFAULT_API_ENDPOINTS = [
    "https://api.52vmy.cn/api/wl/moyu",
]

DEFAULT_TEMPLATE = {
    "name": "默认样式",
    "format": "摸鱼人日历\n当前时间：{time}"
}

__all__ = [
    "PLUGIN_NAME",
    "PLUGIN_VERSION",
    "PLUGIN_AUTHOR",
    "PLUGIN_DESC",
    "PLUGIN_REPO",
    "DEFAULT_API_ENDPOINTS",
    "DEFAULT_TEMPLATE",
]
