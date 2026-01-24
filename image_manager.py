import aiohttp
from datetime import datetime
from astrbot.api import logger
import traceback
import os
import asyncio
import uuid
from typing import List, Optional, Union, Dict
from functools import wraps
import json


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


class ImageManager:
    def __init__(self, temp_dir: str, config: Dict):
        """初始化图片管理器

        Args:
            temp_dir: 临时目录路径
            config: 从_conf_schema.json加载的配置
        """
        self.temp_dir = temp_dir
        self.config = config
        self.templates = config.get("templates", [])
        self.default_template = config.get(
            "default_template",
            {"name": "默认样式", "format": "摸鱼人日历\n当前时间：{time}"},
        )
        self.api_endpoints = config.get(
            "api_endpoints",
            [
                "https://api.52vmy.cn/api/wl/moyu",
            ],
        )
        self.request_timeout = config.get("request_timeout", 5)
        self.current_template_index = 0

        # 缓存相关属性
        self.cached_image_path: Optional[str] = None
        self.cached_date: Optional[str] = None

        # 并发锁
        self._download_lock: asyncio.Lock = asyncio.Lock()

        # aiohttp session 复用
        self._session: Optional[aiohttp.ClientSession] = None

        # 确保模板列表不为空
        if not self.templates:
            self.templates = [self.default_template]

        # 预处理并缓存有效模板
        self._valid_templates = self._preprocess_templates()

        logger.info(f"已加载API端点: {len(self.api_endpoints)}个")
        logger.info(f"已加载消息模板: {len(self._valid_templates)}个")

    def _preprocess_templates(self) -> List[Dict]:
        """预处理并验证模板，返回有效模板列表"""
        valid_templates = []
        for tmpl in self.templates:
            # 解析字符串模板
            if isinstance(tmpl, str):
                try:
                    tmpl_dict = json.loads(tmpl)
                    if isinstance(tmpl_dict, dict) and "format" in tmpl_dict:
                        valid_templates.append(tmpl_dict)
                    else:
                        logger.warning(f"模板缺少format字段: {tmpl}")
                except json.JSONDecodeError:
                    logger.error(f"无法解析模板字符串: {tmpl}")
            # 验证字典模板
            elif isinstance(tmpl, dict) and "format" in tmpl:
                valid_templates.append(tmpl)
            else:
                logger.warning(f"无效的模板格式: {tmpl}")

        if not valid_templates:
            logger.warning("没有有效的模板，使用默认模板")
            return [self.default_template]

        return valid_templates

    def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp ClientSession"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """关闭 aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _get_next_template(self) -> Dict:
        """按顺序获取下一个消息模板"""
        if not self._valid_templates:
            logger.warning("模板列表为空，使用默认模板")
            return self.default_template

        # 按顺序获取模板
        template = self._valid_templates[self.current_template_index]
        # 更新索引，实现循环
        self.current_template_index = (self.current_template_index + 1) % len(self._valid_templates)

        return template

    @image_operation_handler
    async def get_moyu_image(self) -> Optional[str]:
        """获取摸鱼人日历图片"""
        # 获取当前日期
        today = datetime.now().strftime("%Y-%m-%d")

        # 检查缓存是否有效（同一天）
        if self.cached_image_path and self.cached_date == today:
            if os.path.exists(self.cached_image_path):
                logger.info(f"使用缓存的图片: {self.cached_image_path}")
                return self.cached_image_path
            else:
                # 缓存文件不存在，清除缓存
                self.cached_image_path = None
                self.cached_date = None

        # 缓存无效，需要下载新图片
        async with self._download_lock:
            # 双重检查：可能在等待锁的过程中，其他协程已经下载完成
            if self.cached_image_path and self.cached_date == today:
                if os.path.exists(self.cached_image_path):
                    logger.info(f"使用缓存的图片: {self.cached_image_path}")
                    return self.cached_image_path

            # 删除旧的缓存文件
            if self.cached_image_path and os.path.exists(self.cached_image_path):
                try:
                    os.remove(self.cached_image_path)
                    logger.info(f"已删除旧的缓存文件: {self.cached_image_path}")
                except Exception as e:
                    logger.warning(f"删除旧缓存文件失败: {e}")

            api_endpoints = list(self.api_endpoints)

            # 所有API都直接返回图片，逐个尝试直到成功
            for idx, api_url in enumerate(api_endpoints):
                try:
                    session = self._get_session()
                    # 直接下载图片
                    try:
                        img_path = await self._download_image(session, api_url)
                        if img_path:
                            logger.info(f"成功获取图片，API索引: {idx+1}")
                            # 更新缓存
                            self.cached_image_path = img_path
                            self.cached_date = today
                            return img_path
                        else:
                            logger.error(f"API {api_url} 无法获取有效图片")
                            continue
                    except Exception as e:
                        logger.error(f"下载 {api_url} 失败: {str(e)}")
                        continue

                except asyncio.TimeoutError:
                    logger.error(f"API {api_url} 请求超时")
                    continue
                except Exception as e:
                    logger.error(f"处理API {api_url} 时出错: {str(e)}")
                    continue

            # 所有API都失败了，尝试使用本地备用图片
            logger.error("所有API都失败了，尝试使用本地备用图片")
            local_backup = os.path.join(os.path.dirname(__file__), "backup_moyu.jpg")
            if os.path.exists(local_backup):
                # 复制备用图片到临时目录
                temp_path = os.path.join(
                    self.temp_dir, f"moyu_backup_{uuid.uuid4().hex[:8]}.jpg"
                )
                try:
                    import shutil

                    shutil.copy(local_backup, temp_path)
                    logger.info(f"使用本地备用图片")
                    # 更新缓存
                    self.cached_image_path = temp_path
                    self.cached_date = today
                    return temp_path
                except Exception as e:
                    logger.error(f"复制本地备用图片失败: {str(e)}")

            return None

    async def _download_image(
        self, session: aiohttp.ClientSession, url: str
    ) -> Optional[str]:
        """下载图片并保存到临时文件"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "image/jpeg,image/png,image/webp,image/*,*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

            async with session.get(url, headers=headers) as response:
                # 检查状态码
                if response.status != 200:
                    logger.error(f"下载图片失败，状态码: {response.status}")
                    return None

                # 检查内容类型
                content_type = response.headers.get("content-type", "")

                # 读取响应内容
                content = await response.read()
                content_size = len(content)

                if not content or content_size < 1000:  # 图片通常大于1KB
                    logger.error(
                        f"下载的内容太小，可能不是有效图片: {content_size} 字节"
                    )
                    return None

                # 尝试检测图片格式
                image_format = "jpg"  # 默认格式
                if content_type:
                    if "png" in content_type:
                        image_format = "png"
                    elif "webp" in content_type:
                        image_format = "webp"
                    elif "gif" in content_type:
                        image_format = "gif"

                # 生成临时文件路径
                image_path = os.path.join(
                    self.temp_dir, f"moyu_{uuid.uuid4().hex[:8]}.{image_format}"
                )

                # 保存图片
                with open(image_path, "wb") as f:
                    f.write(content)

                return image_path

        except asyncio.TimeoutError:
            logger.error(f"下载图片超时: {url}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败 {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"下载图片时出错: {str(e)}")
            logger.error(traceback.format_exc())
            raise
