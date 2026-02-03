"""路径工具函数"""

from pathlib import Path
from astrbot.core.utils.astrbot_path import get_astrbot_data_path
from astrbot.api import logger

# 项目根目录
PLUGIN_ROOT = Path(__file__).parents[1]
DATA_DIR = PLUGIN_ROOT / "data"

# AstrBot 数据目录（使用现有路径结构）
DATA_ROOT = Path(get_astrbot_data_path()) / "plugin_data" / "astrbot_plugin_moyuren"
CONFIG_DIR = DATA_ROOT  # ⚠️ 不是 DATA_ROOT / "config"
CACHE_DIR = DATA_ROOT / "cache"

# ⚠️ 重要：不要在这里执行 mkdir()，移到函数中


def migrate_legacy_config():
    """
    迁移旧配置文件（显式调用）

    ⚠️ 重要：此函数必须在插件初始化时显式调用，
    不要在模块顶层执行，避免导入副作用。
    """
    # 确保目录存在（移到这里）
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # 探测多个可能的旧配置路径
    possible_old_paths = [
        PLUGIN_ROOT / "config.yaml",
        PLUGIN_ROOT / "data" / "config.json",
        # ⚠️ 重要：补充现有实际路径
        Path(get_astrbot_data_path()) / "plugin_data" / "astrbot_plugin_moyuren" / "config.yaml",
    ]

    target_path = CONFIG_DIR / "config.yaml"

    if target_path.exists():
        return  # 新配置已存在，无需迁移

    import shutil
    for old_path in possible_old_paths:
        if old_path.exists():
            try:
                shutil.copy2(old_path, target_path)
                logger.info(f"[迁移] 配置文件: {old_path} -> {target_path}")
                return
            except Exception as e:
                logger.error(f"[迁移] 配置迁移失败: {e}")


__all__ = ["PLUGIN_ROOT", "DATA_DIR", "CONFIG_DIR", "CACHE_DIR", "migrate_legacy_config"]
