import aiohttp
from datetime import datetime
from astrbot.api import logger
import os
import asyncio
import uuid
import traceback
from typing import List, Optional, Union, Dict
import json
from ..utils.decorators import image_operation_handler


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
                "https://api.monkeyray.net/api/v1/moyuren",
            ],
        )
        self.request_timeout = config.get("request_timeout", 5)
        self.enable_message_template = config.get("enable_message_template", False)
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

        # 缓存无效，需要生成/下载新图片
        async with self._download_lock:
            # 双重检查：可能在等待锁的过程中，其他协程已经完成
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

            # API 模式获取图片
            api_endpoints = list(self.api_endpoints)

            # 逐个尝试API直到成功
            for idx, api_url in enumerate(api_endpoints):
                try:
                    session = self._get_session()
                    # 发起一次请求并处理（避免双重请求）
                    img_path = await self._fetch_and_process_api(session, api_url)

                    if img_path:
                        logger.info(f"成功获取图片，API索引: {idx+1}")
                        # 更新缓存
                        self.cached_image_path = img_path
                        self.cached_date = today
                        return img_path
                    else:
                        logger.error(f"API {api_url} 无法获取有效图片")
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

    async def _fetch_and_process_api(
        self, session: aiohttp.ClientSession, url: str
    ) -> Optional[str]:
        """发起一次请求，自动判断响应类型并处理

        - JSON API：解析 image 字段，再下载图片
        - 图片 API：直接保存响应内容
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
        }

        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as response:
            if response.status != 200:
                logger.error(f"API 请求失败，状态码: {response.status}")
                return None

            content_type = response.headers.get("content-type", "")
            # 先读取全部内容到内存（避免流只能读取一次的问题）
            content = await response.read()

            if not content or len(content) < 100:
                logger.error(f"API 响应内容为空或太小")
                return None

            # 如果返回的是图片，直接保存
            if "image" in content_type:
                return await self._save_image_content(content, content_type)

            # 尝试解析为 JSON
            try:
                data = json.loads(content.decode("utf-8"))
                if isinstance(data, dict) and data.get("image"):
                    image_url = data["image"]
                    if isinstance(image_url, str):
                        logger.info(f"JSON API 返回图片 URL: {image_url}")
                        return await self._download_image(session, image_url)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.debug(f"JSON 解析失败: {str(e)}")

            # 非图片也非有效 JSON，尝试将内容当作图片保存（某些 API 可能不设置正确的 content-type）
            if len(content) > 1000:
                return await self._save_image_content(content, content_type)

            logger.error(f"API {url} 返回了无法识别的内容类型: {content_type}")
            return None

    async def _save_image_content(
        self, content: bytes, content_type: str = ""
    ) -> Optional[str]:
        """将图片内容保存到临时文件"""
        if not content or len(content) < 1000:
            logger.error(f"图片内容太小，可能无效: {len(content) if content else 0} 字节")
            return None

        # 图片魔数校验
        image_format = self._detect_image_format(content)
        if not image_format:
            # 如果 content-type 明确是图片，仍然尝试保存
            if "image" in content_type:
                image_format = "jpg"  # 默认格式
            else:
                logger.error("内容不是有效的图片格式（魔数校验失败）")
                return None

        image_path = os.path.join(
            self.temp_dir, f"moyu_{uuid.uuid4().hex[:8]}.{image_format}"
        )

        with open(image_path, "wb") as f:
            f.write(content)

        return image_path

    def _detect_image_format(self, content: bytes) -> Optional[str]:
        """通过魔数检测图片格式"""
        if len(content) < 8:
            return None

        # JPEG: FF D8 FF
        if content[:3] == b'\xff\xd8\xff':
            return "jpg"
        # PNG: 89 50 4E 47 0D 0A 1A 0A
        if content[:8] == b'\x89PNG\r\n\x1a\n':
            return "png"
        # GIF: 47 49 46 38
        if content[:4] == b'GIF8':
            return "gif"
        # WebP: 52 49 46 46 ... 57 45 42 50
        if content[:4] == b'RIFF' and len(content) > 11 and content[8:12] == b'WEBP':
            return "webp"

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
