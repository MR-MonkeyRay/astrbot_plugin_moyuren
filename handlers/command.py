from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api import logger
import astrbot.api.message_components as Comp
from datetime import datetime, timedelta
import re
import traceback
from typing import AsyncGenerator
from ..utils.decorators import command_error_handler


class CommandHelper:
    def __init__(self, config_manager, image_manager, context, scheduler=None):
        self.config_manager = config_manager
        self.image_manager = image_manager
        self.context = context
        self.scheduler = scheduler  # 添加调度器引用

    def parse_time_format(self, time_str: str) -> tuple[int, int]:
        """解析时间格式，支持HH:MM和HHMM格式"""
        time_str = time_str.strip()

        # 使用正则表达式匹配时间格式
        colon_pattern = re.compile(r"^(\d{1,2}):(\d{1,2})$")
        no_colon_pattern = re.compile(r"^(\d{4})$")

        # 尝试匹配 HH:MM 格式
        match = colon_pattern.match(time_str)
        if match:
            hour, minute = map(int, match.groups())
        else:
            # 尝试匹配 HHMM 格式
            match = no_colon_pattern.match(time_str)
            if not match:
                raise ValueError("时间格式不正确，请使用 HH:MM 或 HHMM 格式")
            time_digits = match.group(1)
            hour = int(time_digits[:2])
            minute = int(time_digits[2:])

        # 验证时间范围
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("时间范围不正确，小时应在0-23之间，分钟应在0-59之间")

        return hour, minute

    def normalize_session_id(self, event: AstrMessageEvent) -> str:
        """获取会话ID"""
        return event.unified_msg_origin

    def _get_sender_id(self, event: AstrMessageEvent) -> str | None:
        """获取消息发送者ID"""
        try:
            sender_id = event.get_sender_id()
            return str(sender_id) if sender_id is not None else None
        except Exception:
            return None

    async def is_group_admin(self, event: AstrMessageEvent) -> bool:
        """判断消息发送者是否为群管理员"""
        try:
            group = await event.get_group()
        except Exception as e:
            logger.error(f"获取群信息失败: {str(e)}")
            return False
        if not group:
            return False
        sender_id = self._get_sender_id(event)
        if sender_id is None:
            return False
        admins = getattr(group, "group_admins", None) or []
        return any(str(admin) == sender_id for admin in admins)

    async def is_group_owner(self, event: AstrMessageEvent) -> bool:
        """判断消息发送者是否为群主"""
        try:
            group = await event.get_group()
        except Exception as e:
            logger.error(f"获取群信息失败: {str(e)}")
            return False
        if not group:
            return False
        sender_id = self._get_sender_id(event)
        if sender_id is None:
            return False
        owner_id = getattr(group, "group_owner", None)
        if owner_id is None:
            return False
        return str(owner_id) == sender_id

    async def has_group_permission(self, event: AstrMessageEvent) -> tuple[bool, str | None]:
        """
        群聊权限判断，私聊直接放行
        返回: (是否有权限, 错误消息)
        """
        # 私聊直接放行
        if event.is_private_chat():
            return True, None

        # 群聊需要检查权限
        try:
            group = await event.get_group()
        except Exception as e:
            logger.error(f"获取群信息失败: {str(e)}")
            return False, "⚠️ 权限验证失败：无法获取群组信息，请稍后再试"

        if not group:
            return False, "⚠️ 权限验证失败：无法获取群组信息，请稍后再试"

        sender_id = self._get_sender_id(event)
        if sender_id is None:
            logger.warning("无法获取发送者ID")
            return False, "⚠️ 权限验证失败：无法获取用户信息"

        # 检查是否为群主
        owner_id = getattr(group, "group_owner", None)
        if owner_id is not None and str(owner_id) == sender_id:
            return True, None

        # 检查是否为管理员
        admins = getattr(group, "group_admins", None) or []
        if any(str(admin) == sender_id for admin in admins):
            return True, None

        return False, "⛔ 权限不足：仅群管理员或群主可执行此操作"

    @command_error_handler
    async def handle_set_time(
        self, event: AstrMessageEvent, time_str: str
    ) -> AsyncGenerator[MessageEventResult, None]:
        """处理设置时间命令"""
        # 权限检查
        has_perm, error_msg = await self.has_group_permission(event)
        if not has_perm:
            yield event.make_result().message(error_msg)
            return

        try:
            # 格式化时间字符串
            if len(time_str) == 4:  # HHMM格式
                time_str = f"{time_str[:2]}:{time_str[2:]}"
            elif len(time_str) != 5:  # 不是HH:MM格式
                yield event.make_result().message("时间格式错误，请使用HH:MM或HHMM格式")
                return

            # 验证时间格式
            try:
                hour, minute = map(int, time_str.split(":"))
                if not (0 <= hour < 24 and 0 <= minute < 60):
                    yield event.make_result().message(
                        "时间格式错误，小时必须在0-23之间，分钟必须在0-59之间"
                    )
                    return
            except ValueError:
                yield event.make_result().message("时间格式错误，请使用HH:MM或HHMM格式")
                return

            # 获取标准化的群组ID
            target = self.normalize_session_id(event)

            # 更新配置
            if target not in self.config_manager.group_settings:
                self.config_manager.group_settings[target] = {}
            self.config_manager.group_settings[target]["custom_time"] = time_str

            # 保存配置
            self.config_manager.save_config()

            # 计算等待时间
            now = datetime.now()
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # 如果目标时间已经过去，则设置为明天的这个时间
            if target_time <= now:
                target_time += timedelta(days=1)

            # 计算等待的秒数
            wait_seconds = int((target_time - now).total_seconds())
            hours = wait_seconds // 3600
            minutes = (wait_seconds % 3600) // 60
            seconds = wait_seconds % 60

            # 格式化等待时间显示
            wait_time_str = ""
            if hours > 0:
                wait_time_str += f"{hours}小时"
            if minutes > 0:
                wait_time_str += f"{minutes}分钟"
            if seconds > 0 or not wait_time_str:
                wait_time_str += f"{seconds}秒"

            # 唤醒调度器并更新任务队列
            if hasattr(self, "scheduler") and self.scheduler:
                self.scheduler.update_task_queue()
                self.scheduler.wakeup_event.set()

            # 使用 make_result() 构建消息
            result = event.make_result()
            result.message(
                f"✅ 定时发送已设置\n时间：{time_str}\n下一次发送将在 {wait_time_str}后进行"
            )
            yield result

        except Exception as e:
            logger.error(f"设置时间时出错: {str(e)}")
            logger.error(traceback.format_exc())
            yield event.make_result().message("❌ 设置时间时出错，请查看日志")

    @command_error_handler
    async def handle_clear_time(
        self, event: AstrMessageEvent
    ) -> AsyncGenerator[MessageEventResult, None]:
        """取消定时发送摸鱼图片的设置"""
        # 权限检查
        has_perm, error_msg = await self.has_group_permission(event)
        if not has_perm:
            yield event.make_result().message(error_msg)
            return

        target = self.normalize_session_id(event)
        if target not in self.config_manager.group_settings:
            yield event.make_result().message("❌ 当前群聊未设置自定义时间")
            return

        # 检查是否有自定义时间设置
        if "custom_time" not in self.config_manager.group_settings[target]:
            yield event.make_result().message("❌ 当前群聊未设置自定义时间")
            return

        # 获取当前时间设置，用于显示
        current_time = self.config_manager.group_settings[target]["custom_time"]

        # 重置时间设置
        if "custom_time" in self.config_manager.group_settings[target]:
            del self.config_manager.group_settings[target]["custom_time"]

        if len(self.config_manager.group_settings[target]) == 0:
            del self.config_manager.group_settings[target]

        self.config_manager.save_config()

        # 更新调度器
        if hasattr(self, "scheduler") and self.scheduler:
            # 从任务队列中删除对应任务
            self.scheduler.remove_task(target)
            # 更新任务队列
            self.scheduler.update_task_queue()
            # 唤醒调度器
            self.scheduler.wakeup_event.set()

        yield event.make_result().message(
            f"✅ 已取消定时发送\n原定时间：{current_time}"
        )

    @command_error_handler
    async def handle_list_time(
        self, event: AstrMessageEvent
    ) -> AsyncGenerator[MessageEventResult, None]:
        """列出当前群聊的时间设置"""
        target = self.normalize_session_id(event)
        if target not in self.config_manager.group_settings:
            yield event.make_result().message("当前群聊未设置任何配置")
            return

        settings = self.config_manager.group_settings[target]
        time_setting = settings.get("custom_time", "未设置")
        yield event.make_result().message(
            f"当前群聊设置:\n发送时间: {time_setting}"
        )

    @command_error_handler
    async def handle_execute_now(
        self, event: AstrMessageEvent
    ) -> AsyncGenerator[MessageEventResult, None]:
        """立即发送摸鱼人日历"""
        try:
            image_path = await self.image_manager.get_moyu_image()
            if not image_path:
                yield event.make_result().message("获取摸鱼图片失败，请稍后再试")
                return

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

            # 获取消息内容
            template = self.image_manager._get_next_template()

            # 确保模板是字典类型并包含必要的键
            if not isinstance(template, dict) or "format" not in template:
                logger.error(f"模板格式不正确")
                template = self.image_manager.default_template

            try:
                text = template["format"].format(time=current_time)
                logger.info(f"使用模板: {template.get('name', '未命名模板')}")
            except Exception as e:
                logger.error(f"格式化模板时出错: {str(e)}")
                # 使用一个简单的格式作为后备
                text = f"摸鱼人日历\n当前时间：{current_time}"

            # 创建简单的消息段列表传递给chain_result
            message_segments = [Comp.Plain(text), Comp.Image.fromFileSystem(image_path)]

            # 使用消息段列表
            yield event.chain_result(message_segments)

        except Exception as e:
            logger.error(f"执行立即发送命令时出错: {str(e)}")
            logger.error(traceback.format_exc())
            yield event.make_result().message(
                "发送摸鱼人日历失败，请查看日志获取详细信息"
            )

    @command_error_handler
    async def handle_next_time(
        self, event: AstrMessageEvent
    ) -> AsyncGenerator[MessageEventResult, None]:
        """查看下一次执行时间"""
        if not self.scheduler or not hasattr(self.scheduler, "task_queue"):
            yield event.make_result().message(
                "调度器未初始化，无法获取下一次执行时间"
            )
            return

        target = self.normalize_session_id(event)
        next_time = None
        for scheduled_time, scheduled_target in self.scheduler.task_queue:
            if scheduled_target != target:
                continue
            if next_time is None or scheduled_time < next_time:
                next_time = scheduled_time

        if not next_time:
            yield event.make_result().message("当前群聊未设置定时发送")
            return

        now = datetime.now()
        wait_seconds = int((next_time - now).total_seconds())
        if wait_seconds < 0:
            wait_seconds = 0

        hours = wait_seconds // 3600
        minutes = (wait_seconds % 3600) // 60
        seconds = wait_seconds % 60

        wait_time_str = ""
        if hours > 0:
            wait_time_str += f"{hours}小时"
        if minutes > 0:
            wait_time_str += f"{minutes}分钟"
        if seconds > 0 or not wait_time_str:
            wait_time_str += f"{seconds}秒"

        next_time_str = next_time.strftime("%Y-%m-%d %H:%M")
        yield event.make_result().message(
            f"下一次执行时间：{next_time_str}\n距离现在还有：{wait_time_str}"
        )

    @command_error_handler
    async def handle_help(
        self, event: AstrMessageEvent
    ) -> AsyncGenerator[MessageEventResult, None]:
        """显示插件帮助信息"""
        help_text = (
            "📅 摸鱼人日历插件 v3.0.0\n"
            "【功能简介】\n"
            "每天定时发送摸鱼人日历图片，支持多群组独立配置。\n"
            "v3.0.0 采用全新分层架构设计，提升稳定性和可维护性。\n"
            "【命令列表】\n"
            "/set_time HH:MM 或 HHMM - 设置定时发送时间(24小时制)\n"
            "- 示例: /set_time 09:30 或 /set_time 0930\n"
            "- 别名: 设置摸鱼时间\n"
            "/clear_time - 清除当前群聊的定时设置\n"
            "- 别名: 清除摸鱼时间\n"
            "/list_time - 查看当前群聊的时间设置\n"
            "- 别名: 查看摸鱼时间\n"
            "/next_time - 查看下一次执行的时间\n"
            "- 别名: 下次摸鱼时间\n"
            "/execute_now - 立即发送摸鱼人日历\n"
            "- 别名: 立即摸鱼, 摸鱼日历\n"
            "/moyuren_help - 显示此帮助信息\n"
            "- 别名: 摸鱼帮助\n"
            "【使用说明】\n"
            "1. 使用 /set_time 设置每日发送时间\n"
            "2. 设置后插件会在每天指定时间自动发送摸鱼日历\n"
            "3. 可随时使用 /execute_now 或别名手动触发发送\n"
            "4. ※群聊中仅管理员/群主可修改设置※\n"
            "【新特性】\n"
            "✨ 分层架构设计 | 🚀 自动配置迁移 | 📦 模块化管理"
        )
        yield event.make_result().message(help_text)
