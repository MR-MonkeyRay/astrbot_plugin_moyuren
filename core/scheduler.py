import asyncio
from datetime import datetime, timedelta
import heapq
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.api.event import MessageChain
from typing import List, Tuple, Optional
from ..utils.decorators import scheduler_error_handler


class Scheduler:
    def __init__(self, config_manager, image_manager, context):
        self.config_manager = config_manager
        self.image_manager = image_manager
        self.context = context
        self.task_queue: List[Tuple[datetime, str]] = []
        self.wakeup_event = asyncio.Event()
        self.scheduled_task_ref: Optional[asyncio.Task] = None

    def update_task_queue(self) -> None:
        """更新任务队列"""
        # 清空当前队列
        self.task_queue = []

        # 获取当前时间
        now = datetime.now()

        # 遍历所有群组设置
        for target, settings in self.config_manager.group_settings.items():
            try:
                # 检查是否有自定义时间设置
                if not isinstance(settings, dict) or "custom_time" not in settings:
                    continue

                # 解析时间设置
                time_str = settings["custom_time"]
                try:
                    hour, minute = map(int, time_str.split(":"))
                except ValueError:
                    logger.error(f"无效的时间格式: {time_str}")
                    continue

                # 计算今天的执行时间点
                today_exec_time = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                # 如果今天的时间已经过去，调整到明天
                if today_exec_time <= now:
                    today_exec_time = (now + timedelta(days=1)).replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )

                # 添加到优先队列
                heapq.heappush(self.task_queue, (today_exec_time, target))
            except ValueError as e:
                logger.error(f"解析群 {target} 的时间设置出错: {str(e)}")
            except Exception as e:
                logger.error(f"处理群 {target} 的任务时出错: {str(e)}")
                logger.error(traceback.format_exc())

    async def _send_moyu_message(self, target: str) -> bool:
        """发送摸鱼人日历消息

        Args:
            target: 目标会话ID

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        try:
            # 获取摸鱼图片
            image_path = await self.image_manager.get_moyu_image()
            if not image_path:
                logger.error("获取摸鱼图片失败")
                return False

            # 获取当前时间
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

            # 获取模板
            template = self.image_manager._get_next_template()

            # 确保模板是字典类型并包含必要的键
            if not isinstance(template, dict) or "format" not in template:
                logger.error("模板格式不正确")
                template = self.image_manager.default_template

            # 格式化文本
            try:
                text = template["format"].format(time=current_time)
                logger.info(f"使用模板: {template.get('name', '未命名模板')}")
            except Exception as e:
                logger.error(f"格式化模板时出错: {str(e)}")
                text = f"摸鱼人日历\n当前时间：{current_time}"

            # 根据配置决定是否发送提示语
            if self.image_manager.enable_message_template:
                # 发送图片 + 提示语
                message_chain = MessageChain([
                    Comp.Plain(text + "\n"),
                    Comp.Image.fromFileSystem(image_path)
                ])
            else:
                # 仅发送图片
                message_chain = MessageChain([Comp.Image.fromFileSystem(image_path)])

            # 发送消息
            await self.context.send_message(target, message_chain)
            logger.info(f"已向 {target} 发送摸鱼人日历")
            return True

        except Exception as e:
            logger.error(f"发送摸鱼消息失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    @scheduler_error_handler
    async def _execute_task(self, target: str, scheduled_time: datetime) -> None:
        """执行定时任务"""
        now = datetime.now()

        # 获取群组设置
        settings = None
        try:
            if target not in self.config_manager.group_settings:
                return

            settings = self.config_manager.group_settings[target]
            if not isinstance(settings, dict) or "custom_time" not in settings:
                return
        except Exception as e:
            logger.error(f"检查群组设置时出错: {str(e)}")
            return

        # 发送消息
        await self._send_moyu_message(target)

        # 无论成功或失败，都安排下一次任务
        try:
            if settings:
                hour, minute = map(int, settings["custom_time"].split(":"))
                next_time = (now + timedelta(days=1)).replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                # 添加下一次定时任务到队列
                heapq.heappush(self.task_queue, (next_time, target))
                logger.info(f"已添加下一次定时任务，执行时间：{next_time.strftime('%Y-%m-%d %H:%M')}")
        except Exception as e:
            logger.error(f"更新下一次执行时间失败: {str(e)}")
            logger.error(traceback.format_exc())

    @scheduler_error_handler
    async def scheduled_task(self) -> None:
        """定时任务主循环"""
        while True:
            try:
                # 如果任务队列为空，等待唤醒
                if not self.task_queue:
                    logger.info("任务队列为空，等待唤醒")
                    self.wakeup_event.clear()
                    await self.wakeup_event.wait()
                    continue

                # 获取下一个任务
                next_time, target = self.task_queue[0]

                # 计算等待时间
                now = datetime.now()
                if next_time > now:
                    wait_seconds = (next_time - now).total_seconds()

                    # 设置唤醒事件的超时
                    try:
                        # 等待唤醒事件或超时
                        await asyncio.wait_for(
                            self.wakeup_event.wait(), timeout=wait_seconds
                        )

                        # 如果被唤醒，重新计算任务
                        self.wakeup_event.clear()
                        continue
                    except asyncio.TimeoutError:
                        # 超时，执行任务
                        pass

                # 弹出当前任务
                next_time, target = heapq.heappop(self.task_queue)

                # 执行任务
                await self._execute_task(target, next_time)

                # 记录任务队列状态
                queue_info = [(dt.strftime("%Y-%m-%d %H:%M"), tgt) for dt, tgt in self.task_queue]
                logger.info(f"执行任务后的队列状态: {queue_info}")

            except asyncio.CancelledError:
                # 任务被取消
                logger.info("定时任务被取消")
                break
            except Exception as e:
                logger.error(f"定时任务循环出错: {str(e)}")
                logger.error(traceback.format_exc())
                # 出错后等待一段时间再继续
                await asyncio.sleep(60)

    def start(self) -> None:
        """启动定时任务"""
        if not self.scheduled_task_ref:
            logger.info("创建定时任务...")
            self.scheduled_task_ref = asyncio.get_event_loop().create_task(
                self.scheduled_task()
            )
            logger.info("定时任务已创建并启动")
        else:
            logger.info("定时任务已经在运行中")

    async def stop(self) -> None:
        """停止定时任务"""
        if self.scheduled_task_ref:
            self.scheduled_task_ref.cancel()
            try:
                await self.scheduled_task_ref
            except asyncio.CancelledError:
                logger.info("定时任务已被取消")
            self.scheduled_task_ref = None

    def remove_task(self, target: str) -> bool:
        """从任务队列中删除特定目标的任务

        Args:
            target: 目标会话ID

        Returns:
            bool: 是否成功删除任务
        """
        try:
            # 创建新的任务队列，排除指定目标的任务
            new_queue = []
            removed = False

            # 遍历当前任务队列
            while self.task_queue:
                task = heapq.heappop(self.task_queue)
                time, task_target = task

                # 如果不是要删除的目标，则保留
                if task_target != target:
                    new_queue.append(task)
                else:
                    removed = True

            # 重建任务队列
            self.task_queue = []
            for task in new_queue:
                heapq.heappush(self.task_queue, task)

            return removed
        except Exception as e:
            logger.error(f"删除任务时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return False
