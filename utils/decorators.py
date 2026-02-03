"""装饰器工具"""

import asyncio
import traceback
import yaml
import os
from functools import wraps
from typing import Callable, AsyncGenerator
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult
import aiohttp


def config_operation_handler(func: Callable):
    """配置操作错误处理装饰器"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except yaml.YAMLError as je:
            logger.error(f"配置文件解析错误: {str(je)}")
            if hasattr(self, "config_file") and os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.bak"
                os.rename(self.config_file, backup_file)
                logger.info(f"已将损坏的配置文件备份为: {backup_file}")
        except (IOError, OSError) as e:
            logger.error(f"文件操作错误: {str(e)}")
        except Exception as e:
            logger.error(f"{func.__name__} 执行出错: {str(e)}")
            logger.error(traceback.format_exc())
        return None

    return wrapper


def image_operation_handler(func):
    """图片操作错误处理装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except aiohttp.ClientError as e:
            logger.error(f"网络请求错误: {str(e)}")
        except asyncio.TimeoutError:
            logger.error("请求超时")
        except Exception as e:
            logger.error(f"{func.__name__} 执行出错: {str(e)}")
            logger.error(traceback.format_exc())
        return None

    return wrapper


def command_error_handler(func):
    """命令错误处理装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> AsyncGenerator[MessageEventResult, None]:
        try:
            async for result in func(*args, **kwargs):
                yield result
        except ValueError as e:
            # 参数验证错误
            event = args[1] if len(args) > 1 else None
            if event and isinstance(event, AstrMessageEvent):
                yield event.plain_result(f"参数错误: {str(e)}")
        except Exception as e:
            # 其他未预期的错误
            logger.error(f"{func.__name__} 执行出错: {str(e)}")
            logger.error(traceback.format_exc())
            event = args[1] if len(args) > 1 else None
            if event and isinstance(event, AstrMessageEvent):
                yield event.plain_result("操作执行失败，请查看日志获取详细信息")

    return wrapper


def scheduler_error_handler(func):
    """调度器错误处理装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"{func.__name__} 执行出错: {str(e)}")
            logger.error(traceback.format_exc())
            # 出错后等待一段时间再继续
            await asyncio.sleep(60)
            return None

    return wrapper


__all__ = [
    "config_operation_handler",
    "image_operation_handler",
    "command_error_handler",
    "scheduler_error_handler",
]
