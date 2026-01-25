"""摸鱼日历数据模型"""

from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class CountdownItem:
    """倒计时项"""
    name: str  # 名称（如"元旦"、"月初发薪"）
    days: int  # 剩余天数
    is_today: bool = False  # 是否是今天
    start_date: str = ""  # 假期开始日期（如"2026-01-01"）
    end_date: str = ""  # 假期结束日期（如"2026-01-03"）

    def format_date_range(self) -> str:
        """格式化日期区间

        Returns:
            str: 格式化的日期区间（如"2026-01-01 至 2026-01-03"）
        """
        if self.start_date and self.end_date:
            if self.start_date == self.end_date:
                return self.start_date
            return f"{self.start_date} 至 {self.end_date}"
        return ""

    def format_countdown(self) -> str:
        """格式化倒计时文本

        Returns:
            str: 格式化的倒计时文本（如"还有 7 天"或"今天"）
        """
        if self.is_today:
            return "今天"
        else:
            return f"还有 {self.days} 天"


@dataclass
class HoroscopeItem:
    """星座运势项"""
    zodiac: str  # 星座名称
    fortune: str  # 运势文案


@dataclass
class LocalRenderData:
    """本地渲染数据"""
    # 日期信息
    date: datetime
    year_month: str  # 如"2026年1月"
    day: int  # 日期数字
    weekday: str  # 星期（如"星期六"）
    lunar_date: str  # 农历日期（如"腊月廿六"）

    # 摸鱼信息
    moyu_index: int  # 摸鱼指数 (0-100)
    moyu_level: str  # 摸鱼等级（如"鱼鲨"、"老油条"）
    moyu_quote: str  # 摸鱼语录

    # 星座运势
    horoscope: HoroscopeItem

    # 倒计时
    weekend_days: int  # 距离周末天数（0表示今天是周末）
    salary_countdowns: List[CountdownItem]  # 发薪日倒计时
    festival_countdowns: List[CountdownItem]  # 节日倒计时

    # 其他
    greeting: str  # 问候语（如"早上好"）
    greeting_emoji: str  # 问候emoji

    # 摸鱼时间轴（可选字段，放在最后）
    timeline: List[str] = None  # 摸鱼时间轴（如["09:00 伪装上班", "10:30 假装思考"]）


__all__ = ["CountdownItem", "HoroscopeItem", "LocalRenderData"]
