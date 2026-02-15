import yaml
import os
from astrbot.api import logger
from typing import Dict, Any, Optional
from pathlib import Path
from ..utils.decorators import config_operation_handler


class ConfigManager:
    def __init__(self, config_dir: Path):
        self.config_file = config_dir / "config.yaml"
        self.group_settings: Dict[str, Dict[str, Any]] = {}

    @config_operation_handler
    def load_config(self) -> Optional[bool]:
        """加载配置文件

        Returns:
            bool: 加载是否成功
        """
        self.group_settings = {}  # 确保初始化为空字典

        if not os.path.exists(self.config_file):
            logger.info("配置文件不存在，将创建新的配置文件")
            return self.save_config()

        with open(self.config_file, "r", encoding="utf-8") as f:
            loaded_data = f.read().strip()
            if not loaded_data:  # 处理空文件的情况
                logger.warning("配置文件为空，使用默认空字典")
                return True

            loaded_settings = yaml.safe_load(loaded_data)
            if loaded_settings is None:
                logger.warning("配置文件为空或仅含注释，使用默认空字典")
                return True
            if not isinstance(loaded_settings, dict):
                logger.error(f"配置文件格式错误：期望字典类型，实际为 {type(loaded_settings)}")
                # 备份损坏的配置文件
                backup_file = f"{self.config_file}.bak"
                os.rename(self.config_file, backup_file)
                logger.info(f"已将损坏的配置文件备份为: {backup_file}")
                return True

            # 验证并加载配置
            for target, settings in loaded_settings.items():
                if not isinstance(settings, dict):
                    logger.warning(f"跳过无效的群设置 {target}: {settings}")
                    continue

                # 兼容旧版本配置，保留custom_time
                if "custom_time" in settings:
                    # 只有当存在有效配置时才初始化群设置
                    if target not in self.group_settings:
                        self.group_settings[target] = {}
                    self.group_settings[target]["custom_time"] = settings["custom_time"]
                # 如果只有 trigger_word 而没有 custom_time，跳过该群组（避免创建空条目）

            logger.info(f"已加载摸鱼人配置: {len(self.group_settings)}个群聊的设置")
            return True

    @config_operation_handler
    def save_config(self) -> Optional[bool]:
        """保存配置到文件

        Returns:
            bool: 保存是否成功
        """
        # 确保group_settings是字典类型
        if not isinstance(self.group_settings, dict):
            raise ValueError(
                f"保存配置失败：group_settings类型错误 ({type(self.group_settings)})"
            )

        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                self.group_settings,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        logger.info("摸鱼人配置已保存")
        return True

    def set_group_time(self, target: str, time_str: str) -> bool:
        """设置群组定时时间

        修改内存 → 保存配置 → 失败则回滚

        Args:
            target: 会话ID
            time_str: 时间字符串，格式 HH:MM

        Returns:
            bool: 是否成功
        """
        # 备份用于回滚
        old_settings = self.group_settings.get(target, {}).copy()
        had_target = target in self.group_settings

        # 修改内存
        if target not in self.group_settings:
            self.group_settings[target] = {}
        self.group_settings[target]["custom_time"] = time_str

        # 保存配置
        if not self.save_config():
            # 回滚
            if had_target:
                self.group_settings[target] = old_settings
            else:
                self.group_settings.pop(target, None)
            logger.error(f"保存群组 {target} 时间设置失败，已回滚")
            return False
        return True

    def clear_group_time(self, target: str) -> bool:
        """清除群组定时时间

        修改内存 → 保存配置 → 失败则回滚

        Args:
            target: 会话ID

        Returns:
            bool: 是否成功
        """
        # 备份用于回滚
        old_settings = self.group_settings.get(target, {}).copy()
        had_target = target in self.group_settings

        if not had_target or "custom_time" not in self.group_settings.get(target, {}):
            return True  # 没有需要清除的

        # 修改内存
        del self.group_settings[target]["custom_time"]
        if len(self.group_settings[target]) == 0:
            del self.group_settings[target]

        # 保存配置
        if not self.save_config():
            # 回滚
            if had_target:
                self.group_settings[target] = old_settings
            else:
                self.group_settings.pop(target, None)
            logger.error(f"清除群组 {target} 时间设置失败，已回滚")
            return False
        return True
