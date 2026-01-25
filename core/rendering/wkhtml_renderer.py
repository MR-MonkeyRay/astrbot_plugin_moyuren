"""HTML 渲染器 - 使用 wkhtmltoimage 将 HTML 转换为图片"""

import os
import uuid
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import imgkit
    IMGKIT_AVAILABLE = True
except ImportError:
    IMGKIT_AVAILABLE = False

from astrbot.api import logger
from models.moyu import LocalRenderData


class WkhtmlMoyuRenderer:
    """使用 wkhtmltoimage 的摸鱼日历渲染器"""

    # 固定配置常量
    IMAGE_FORMAT = "png"
    ZOOM_FACTOR = 3.0

    def __init__(self, temp_dir: str):
        """初始化渲染器

        Args:
            temp_dir: 临时文件目录

        Raises:
            ImportError: imgkit 未安装
            RuntimeError: wkhtmltoimage 二进制未找到
        """
        if not IMGKIT_AVAILABLE:
            raise ImportError(
                "imgkit 未安装。请运行: pip install imgkit\n"
                "同时需要安装 wkhtmltoimage: https://wkhtmltopdf.org/downloads.html"
            )

        # 检查 wkhtmltoimage 二进制是否可用
        self._verify_wkhtmltoimage()

        self.temp_dir = temp_dir
        self.template_path = Path(__file__).parent / "moyu_template.html"

        # 使用类常量初始化
        self.image_format = self.IMAGE_FORMAT
        self.zoom_factor = self.ZOOM_FACTOR

    def _verify_wkhtmltoimage(self):
        """验证 wkhtmltoimage 二进制是否可用"""
        wkhtmltoimage_path = shutil.which("wkhtmltoimage")
        if not wkhtmltoimage_path:
            raise RuntimeError(
                "wkhtmltoimage 未找到。请安装 wkhtmltoimage:\n"
                "Ubuntu/Debian: sudo apt-get install wkhtmltopdf\n"
                "macOS: brew install wkhtmltopdf\n"
                "或访问: https://wkhtmltopdf.org/downloads.html"
            )

        # 验证版本
        try:
            result = subprocess.run(
                ["wkhtmltoimage", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            logger.info(f"wkhtmltoimage 版本: {result.stdout.strip()}")
        except Exception as e:
            logger.warning(f"无法获取 wkhtmltoimage 版本: {e}")

    def render(self, data: LocalRenderData) -> Optional[str]:
        """渲染摸鱼日历图片

        Args:
            data: 摸鱼日历数据

        Returns:
            str: 图片文件路径，失败返回 None
        """
        html_file = None
        try:
            logger.info("开始使用 wkhtmltoimage 渲染摸鱼日历...")

            # 性能提示
            if self.zoom_factor >= 4.0:
                logger.warning(f"当前 zoom_factor={self.zoom_factor}，渲染可能需要较长时间并产生较大文件")

            # 读取模板
            with open(self.template_path, "r", encoding="utf-8") as f:
                html_template = f.read()

            # 填充数据
            html_content = self._fill_template(html_template, data)

            # 保存临时 HTML 文件
            html_file = self._save_temp_html(html_content)

            # 使用 wkhtmltoimage 转换
            image_path = self._html_to_image(html_file, data.date)

            logger.info(f"wkhtmltoimage 渲染完成: {image_path}")
            return image_path

        except Exception as e:
            logger.error(f"wkhtmltoimage 渲染失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

        finally:
            # 确保清理临时文件
            if html_file and os.path.exists(html_file):
                try:
                    os.remove(html_file)
                    logger.debug(f"已清理临时文件: {html_file}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

    def _fill_template(self, template: str, data: LocalRenderData) -> str:
        """填充 HTML 模板"""
        # 周末信息
        if data.weekend_days == 0:
            weekend_title = "周末"
            weekend_text = "今天"
        elif data.weekend_days == 1:
            weekend_title = "周末"
            weekend_text = "明天"
        else:
            weekend_title = "距周末"
            weekend_text = f"{data.weekend_days}天"

        # 摸鱼指数颜色
        if data.moyu_index >= 80:
            fish_color = "#10b981"
            fish_text = f"{data.moyu_index}% 🐟 {data.moyu_level}"
        elif data.moyu_index >= 60:
            fish_color = "#f59e0b"
            fish_text = f"{data.moyu_index}% 🐠 {data.moyu_level}"
        else:
            fish_color = "#ef4444"
            fish_text = f"{data.moyu_index}% 🦈 {data.moyu_level}"

        # 星座运势
        zodiac_text = f"{data.horoscope.zodiac}：{data.horoscope.fortune}"

        # 时间轴
        timeline_items = ""
        if data.timeline:
            for item in data.timeline:
                timeline_items += f'<div class="timeline-item">{item}</div>\n'

        # 发薪日倒计时
        salary_items = ""
        for item in data.salary_countdowns:
            if item.is_today:
                salary_items += f'<div class="salary-item today">{item.name}<span class="salary-days">今日发工资啦! 🎉</span></div>\n'
            else:
                salary_items += f'<div class="salary-item">{item.name}<span class="salary-days">{item.days}天</span></div>\n'

        # 节日倒计时
        festival_items = ""
        for item in data.festival_countdowns:
            date_range = item.format_date_range()
            countdown_text = item.format_countdown()

            # 根据剩余天数判断紧急程度
            days = item.days
            if days < 0:
                urgency_class = "urgency-past"
                icon = "⚫"
                info_text = f"{date_range} · 已结束"
            elif days == 0:
                urgency_class = "urgency-today"
                icon = "🔴"
                info_text = f"{date_range} · 今天 🎊"
            elif 0 < days <= 7:
                urgency_class = "urgency-week"
                icon = "🟠"
                info_text = f"{date_range} · <strong>{countdown_text}</strong>"
            elif 7 < days <= 30:
                urgency_class = "urgency-month"
                icon = "🟡"
                info_text = f"{date_range} · <strong>{countdown_text}</strong>"
            else:
                urgency_class = "urgency-normal"
                icon = "⚪"
                info_text = f"{date_range} · <strong>{countdown_text}</strong>"

            festival_items += f'''<div class="festival-item {urgency_class}">
    <div class="festival-item-icon">{icon}</div>
    <div class="festival-content">
        <div class="festival-name">{item.name}</div>
        <div class="festival-info">{info_text}</div>
    </div>
</div>
'''

        # 替换模板变量
        replacements = {
            "{{year}}": str(data.date.year),
            "{{month}}": str(data.date.month),
            "{{day}}": str(data.day),
            "{{weekday}}": data.weekday,
            "{{weekend_title}}": weekend_title,
            "{{weekend_text}}": weekend_text,
            "{{greeting}}": data.greeting,
            "{{greeting_emoji}}": data.greeting_emoji,
            "{{moyu_quote}}": data.moyu_quote,
            "{{fish_color}}": fish_color,
            "{{fish_text}}": fish_text,
            "{{zodiac_text}}": zodiac_text,
            "{{timeline_items}}": timeline_items,
            "{{salary_items}}": salary_items,
            "{{festival_items}}": festival_items,
            "{{quote_text}}": data.moyu_quote
        }

        html_content = template
        for key, value in replacements.items():
            html_content = html_content.replace(key, value)

        return html_content

    def _save_temp_html(self, html_content: str) -> str:
        """保存临时 HTML 文件"""
        temp_html = os.path.join(self.temp_dir, f"moyu_{uuid.uuid4().hex[:8]}.html")
        with open(temp_html, "w", encoding="utf-8") as f:
            f.write(html_content)
        return temp_html

    def _html_to_image(self, html_file: str, date: datetime) -> str:
        """使用 wkhtmltoimage 将 HTML 转换为图片

        优化项：
        1. 使用 zoom 提升清晰度（3x 超高清）
        2. 禁用智能宽度，使用固定宽度
        3. 自动计算高度，避免裁剪
        """
        logger.info("使用 wkhtmltoimage 转换...")

        # 生成输出文件名
        date_str = date.strftime("%Y%m%d")
        filename = f"moyu_{date_str}_{uuid.uuid4().hex[:8]}.{self.image_format}"
        image_path = os.path.join(self.temp_dir, filename)

        # wkhtmltoimage 高清选项
        options = {
            'format': self.image_format,
            'width': 600,  # 固定宽度（提高基础分辨率）
            'quality': 100,  # 最高质量
            'enable-local-file-access': None,  # 允许访问本地文件
            'encoding': 'UTF-8',

            # 清晰度优化（使用 zoom 提升清晰度）
            'zoom': self.zoom_factor,  # 支持最高 5x 缩放，超高清

            # 避免裁剪
            'disable-smart-width': None,  # 禁用智能宽度

            # 渲染优化
            'no-stop-slow-scripts': None,  # 不停止慢脚本
            'javascript-delay': 100,  # JS 延迟 100ms
        }

        try:
            # 转换 HTML 到图片
            imgkit.from_file(html_file, image_path, options=options)

            # 获取生成的图片信息
            if os.path.exists(image_path):
                file_size = os.path.getsize(image_path) / 1024
                logger.info(f"转换完成: {image_path} ({file_size:.2f} KB)")

            return image_path

        except Exception as e:
            logger.error(f"wkhtmltoimage 转换失败: {e}")
            raise


__all__ = ["WkhtmlMoyuRenderer"]
