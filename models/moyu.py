"""摸鱼日历数据模型"""

from dataclasses import dataclass


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


__all__ = ["CountdownItem", "HoroscopeItem"]
