from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import traceback

from .core.config import ConfigManager
from .core.image import ImageManager
from .core.scheduler import Scheduler
from .handlers.command import CommandHelper
from .utils.paths import migrate_legacy_config, CONFIG_DIR, CACHE_DIR


@register(
    "moyuren",
    "MonkeyRay",
    "一个功能完善的摸鱼人日历插件",
    "3.1.2",
    "https://github.com/MR-MonkeyRay/astrbot_plugin_moyuren",
)
class MoyuRenPlugin(Star):
    """摸鱼人日历插件

    功能：
    - 在指定时间自动发送摸鱼人日历
    - 支持精确定时，无需轮询检测
    - 支持多群组不同时间设置
    - 每次按顺序选择不同的排版样式
    - 支持自定义API端点和消息模板

    命令：
    - /set_time HH:MM - 设置发送时间，格式为24小时制
    - /clear_time - 清除当前群聊的时间设置
    - /list_time - 查看当前群聊的时间设置
    - /execute_now - 立即发送摸鱼人日历
    - /next_time - 查看下一次执行的时间
    - /moyuren_help - 显示帮助信息
    """

    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.cache_dir = CACHE_DIR

        # ⚠️ 重要：显式调用配置迁移
        migrate_legacy_config()

        # 初始化各个管理器
        logger.info("开始初始化摸鱼人插件...")
        self.config_manager = ConfigManager(CONFIG_DIR)

        # 使用从AstrBot获取的配置（通过_conf_schema.json）
        self.plugin_config = config or {}
        logger.info(f"加载插件配置: {self.plugin_config}")

        self.image_manager = ImageManager(str(self.cache_dir), self.plugin_config)
        self.scheduler = Scheduler(self.config_manager, self.image_manager, context)
        self.command_helper = CommandHelper(
            self.config_manager, self.image_manager, context, self.scheduler
        )

        # 加载配置
        logger.info("加载摸鱼人插件配置...")
        self.config_manager.load_config()
        logger.info(f"已加载 {len(self.config_manager.group_settings)} 个群聊配置")

        # 初始化任务队列并启动定时任务
        logger.info("启动摸鱼人插件定时任务...")
        self.scheduler.init_queue()
        self.scheduler.start()

        # 记录任务队列初始状态
        if hasattr(self.scheduler, 'task_queue') and self.scheduler.task_queue:
            queue_info = [(dt.strftime("%Y-%m-%d %H:%M"), tgt) for dt, tgt in self.scheduler.task_queue]
            logger.info(f"初始任务队列状态: {queue_info}")
        else:
            logger.info("初始任务队列为空")
        
        logger.info("摸鱼人插件初始化完成")

        # 保存实例引用
        MoyuRenPlugin._instance = self

    @filter.command("set_time", alias=("设置摸鱼时间",))
    async def set_time(self, event: AstrMessageEvent, time: str):
        """设置发送摸鱼图片的时间 格式为 HH:MM或HHMM"""
        async for result in self.command_helper.handle_set_time(event, time):
            yield result

    @filter.command("clear_time", alias=("清除摸鱼时间",))
    async def clear_time(self, event: AstrMessageEvent):
        """清除当前群聊的定时设置"""
        async for result in self.command_helper.handle_clear_time(event):
            yield result

    @filter.command("list_time", alias=("查看摸鱼时间",))
    async def list_time(self, event: AstrMessageEvent):
        """列出当前群聊的时间设置"""
        async for result in self.command_helper.handle_list_time(event):
            yield result

    @filter.command("execute_now", alias=("立即摸鱼", "摸鱼日历"))
    async def execute_now(self, event: AstrMessageEvent):
        """立即发送摸鱼人日历"""
        async for result in self.command_helper.handle_execute_now(event):
            yield result

    @filter.command("next_time", alias=("下次摸鱼时间",))
    async def next_time(self, event: AstrMessageEvent):
        """查看下一次执行时间"""
        async for result in self.command_helper.handle_next_time(event):
            yield result

    @filter.command("moyuren_help", alias=("摸鱼帮助",))
    async def moyuren_help(self, event: AstrMessageEvent):
        """显示摸鱼人日历插件帮助信息"""
        async for result in self.command_helper.handle_help(event):
            yield result

    async def terminate(self):
        """终止插件的所有活动"""
        try:
            # 获取实例
            instance = getattr(self, "_instance", None)
            if not instance:
                logger.error("找不到摸鱼人插件实例，无法正常终止")
                return

            # 停止定时任务
            await instance.scheduler.stop()
            logger.info("摸鱼人日历定时任务已停止")

            # 关闭 image_manager 的 session
            if hasattr(instance, "image_manager"):
                await instance.image_manager.close()
                logger.info("已关闭图片管理器网络会话")

            # 清理缓存文件
            if hasattr(instance, "cache_dir") and instance.cache_dir.exists():
                for file in instance.cache_dir.iterdir():
                    try:
                        if file.is_file():
                            file.unlink()
                    except Exception as e:
                        logger.error(f"删除缓存文件失败: {str(e)}")
                logger.info("已清理摸鱼人插件缓存文件")
        except Exception as e:
            logger.error(f"终止插件时出错: {str(e)}")
            logger.error(traceback.format_exc())
