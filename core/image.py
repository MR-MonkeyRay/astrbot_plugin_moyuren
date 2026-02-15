import aiohttp
from astrbot.api import logger
import os
import asyncio
import uuid
import traceback
from typing import List, Optional, Dict
import json
from urllib.parse import urlparse
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

        # 并发锁
        self._download_lock: asyncio.Lock = asyncio.Lock()

        # aiohttp session 复用
        self._session: Optional[aiohttp.ClientSession] = None

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
            logger.warning("没有有效的模板，将仅发送图片")
            return []

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

    def get_next_template(self) -> Optional[Dict]:
        """按顺序获取下一个消息模板

        Returns:
            模板字典，如果没有有效模板则返回 None
        """
        if not self._valid_templates:
            logger.debug("模板列表为空，将仅发送图片")
            return None

        # 按顺序获取模板
        template = self._valid_templates[self.current_template_index]
        # 更新索引，实现循环
        self.current_template_index = (self.current_template_index + 1) % len(self._valid_templates)

        return template

    @image_operation_handler
    async def get_moyu_image(self) -> Optional[str]:
        """获取摸鱼人日历图片"""
        async with self._download_lock:
            api_endpoints = list(self.api_endpoints)

            for idx, api_url in enumerate(api_endpoints):
                try:
                    session = self._get_session()
                    # 获取图片 URL
                    image_url = await self._fetch_image_url(session, api_url)
                    if not image_url:
                        continue

                    # 从 URL 提取文件名
                    filename = os.path.basename(urlparse(image_url).path)
                    if not filename or "." not in filename:
                        logger.warning(f"无法从 URL 提取有效文件名: {image_url}")
                        filename = None

                    # 构造缓存路径
                    cache_path = (
                        os.path.join(self.temp_dir, filename) if filename else None
                    )

                    # 检查缓存是否命中（文件存在且大小有效）
                    if cache_path and os.path.exists(cache_path):
                        if os.path.getsize(cache_path) >= 1000:
                            logger.info(f"缓存命中: {cache_path}")
                            self.cached_image_path = cache_path
                            return cache_path
                        else:
                            # 缓存文件无效（可能是半文件），删除后重新下载
                            logger.warning(f"缓存文件无效，将重新下载: {cache_path}")
                            try:
                                os.remove(cache_path)
                            except Exception as e:
                                logger.warning(f"删除无效缓存文件失败: {cache_path}, {e}")

                    # 缓存未命中，下载图片
                    img_path = await self._download_image(session, image_url, filename)
                    if img_path:
                        logger.info(f"成功获取图片，API索引: {idx+1}")
                        self.cached_image_path = img_path
                        return img_path

                except asyncio.TimeoutError:
                    logger.error(f"API {api_url} 请求超时")
                    continue
                except Exception as e:
                    logger.error(f"处理API {api_url} 时出错: {str(e)}")
                    continue

            # 所有 API 失败，尝试返回旧缓存
            if self.cached_image_path and os.path.exists(self.cached_image_path):
                logger.warning(f"所有API失败，使用旧缓存: {self.cached_image_path}")
                return self.cached_image_path

            logger.error("所有API都失败了，无法获取摸鱼日历图片")
            return None

    async def _fetch_image_url(
        self, session: aiohttp.ClientSession, url: str
    ) -> Optional[str]:
        """请求 API 并返回图片 URL

        API 返回 JSON 格式：{"date": "...", "image": "https://..."}
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
        }

        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as response:
            if response.status != 200:
                logger.error(f"API 请求失败，状态码: {response.status}")
                return None

            content = await response.read()
            if not content:
                logger.error("API 响应内容为空")
                return None

            try:
                data = json.loads(content.decode("utf-8"))

                if not isinstance(data, dict):
                    logger.error("API 返回的不是有效的 JSON 对象")
                    return None

                image_url = data.get("image")
                if not image_url:
                    logger.error("API 响应中缺少 image 字段")
                    return None

                if not isinstance(image_url, str):
                    logger.error(f"API 响应中的 image 字段不是字符串: {type(image_url)}")
                    return None

                if not (image_url.startswith("http://") or image_url.startswith("https://")):
                    logger.error(f"API 响应中的 image 字段不是有效的 HTTP(S) URL: {image_url}")
                    return None

                logger.info(f"从 API 获取到图片 URL: {image_url}")
                return image_url

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"JSON 解析失败: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"处理 API 响应时出错: {str(e)}")
                return None

    async def _download_image(
        self, session: aiohttp.ClientSession, url: str, filename: Optional[str] = None
    ) -> Optional[str]:
        """下载图片并保存到临时文件

        Args:
            session: aiohttp 会话
            url: 图片 URL
            filename: 指定的文件名，如果为 None 则使用 UUID 生成
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "image/jpeg,image/png,image/webp,image/*,*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"下载图片失败，状态码: {response.status}")
                    return None

                content_type = response.headers.get("content-type", "")
                content = await response.read()
                content_size = len(content)

                if not content or content_size < 1000:
                    logger.error(
                        f"下载的内容太小，可能不是有效图片: {content_size} 字节"
                    )
                    return None

                # 使用指定文件名或生成 UUID 文件名
                if filename:
                    image_path = os.path.join(self.temp_dir, filename)
                else:
                    # 检测图片格式
                    image_format = "jpg"
                    if content_type:
                        if "png" in content_type:
                            image_format = "png"
                        elif "webp" in content_type:
                            image_format = "webp"
                        elif "gif" in content_type:
                            image_format = "gif"
                    image_path = os.path.join(
                        self.temp_dir, f"moyu_{uuid.uuid4().hex[:8]}.{image_format}"
                    )

                # 原子写入：先写临时文件，再替换
                tmp_path = image_path + ".tmp"
                with open(tmp_path, "wb") as f:
                    f.write(content)
                os.replace(tmp_path, image_path)

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
