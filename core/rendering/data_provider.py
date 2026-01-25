"""摸鱼日历数据提供者"""

import random
from datetime import datetime, timedelta
from typing import List
from models.moyu import LocalRenderData, CountdownItem, HoroscopeItem
from models.moyu_static import MoyuQuote, ZodiacFortune, Zodiac
from core.rendering.holiday_fetcher import HolidayFetcher
from utils.paths import DATA_ROOT


class MoyuDataProvider:
    """摸鱼日历数据提供者"""

    def __init__(self):
        """初始化数据提供者"""
        # 初始化节假日获取器
        cache_dir = DATA_ROOT / "holiday_cache"
        self.holiday_fetcher = HolidayFetcher(str(cache_dir))

    def generate_moyu_data(self, date: datetime = None) -> LocalRenderData:
        """生成摸鱼日历数据

        Args:
            date: 指定日期，默认为当前日期

        Returns:
            LocalRenderData: 完整的摸鱼日历数据
        """
        if date is None:
            date = datetime.now()

        # 基于日期生成确定性随机种子
        seed = date.year * 10000 + date.month * 100 + date.day
        random.seed(seed)

        # 日期信息
        year_month = f"{date.year}年{date.month}月"
        day = date.day
        weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][date.weekday()]
        lunar_date = self._get_lunar_date(date)

        # 问候语
        greeting, greeting_emoji = self._get_greeting(date.hour)

        # 摸鱼指数
        moyu_index = random.randint(50, 100)
        moyu_level = self._get_moyu_level(moyu_index)
        moyu_quote = random.choice([q.value for q in MoyuQuote])

        # 星座运势
        zodiac = self._get_zodiac_by_date(date)
        fortune = random.choice([f.value for f in ZodiacFortune])
        horoscope = HoroscopeItem(zodiac=zodiac, fortune=fortune)

        # 距离周末
        weekend_days = self._calculate_weekend_days(date)

        # 发薪日倒计时
        salary_countdowns = self._calculate_salary_countdowns(date)

        # 节日倒计时
        festival_countdowns = self._calculate_festival_countdowns(date)

        # 摸鱼时间轴
        timeline = self._generate_timeline()

        return LocalRenderData(
            date=date,
            year_month=year_month,
            day=day,
            weekday=weekday,
            lunar_date=lunar_date,
            moyu_index=moyu_index,
            moyu_level=moyu_level,
            moyu_quote=moyu_quote,
            horoscope=horoscope,
            weekend_days=weekend_days,
            salary_countdowns=salary_countdowns,
            festival_countdowns=festival_countdowns,
            timeline=timeline,
            greeting=greeting,
            greeting_emoji=greeting_emoji
        )

    def _get_greeting(self, hour: int) -> tuple:
        """获取问候语"""
        if 5 <= hour < 9:
            return "早上好", "🌅"
        elif 9 <= hour < 12:
            return "上午好", "☀️"
        elif 12 <= hour < 14:
            return "中午好", "🍚"
        elif 14 <= hour < 18:
            return "下午好", "🌤️"
        else:
            return "晚上好", "🌙"

    def _get_moyu_level(self, index: int) -> str:
        """获取摸鱼等级"""
        if index >= 90:
            return "鱼鲨"
        elif index >= 80:
            return "老油条"
        elif index >= 70:
            return "熟练工"
        else:
            return "新手"

    def _get_zodiac_by_date(self, date: datetime) -> str:
        """根据日期获取星座

        星座日期区间（按公历）：
        摩羯座: 12/22 - 1/19
        水瓶座: 1/20 - 2/18
        双鱼座: 2/19 - 3/20
        白羊座: 3/21 - 4/19
        金牛座: 4/20 - 5/20
        双子座: 5/21 - 6/21
        巨蟹座: 6/22 - 7/22
        狮子座: 7/23 - 8/22
        处女座: 8/23 - 9/22
        天秤座: 9/23 - 10/23
        天蝎座: 10/24 - 11/22
        射手座: 11/23 - 12/21
        """
        month = date.month
        day = date.day

        if (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return Zodiac.AQUARIUS.value
        elif (month == 2 and day >= 19) or (month == 3 and day <= 20):
            return Zodiac.PISCES.value
        elif (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return Zodiac.ARIES.value
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return Zodiac.TAURUS.value
        elif (month == 5 and day >= 21) or (month == 6 and day <= 21):
            return Zodiac.GEMINI.value
        elif (month == 6 and day >= 22) or (month == 7 and day <= 22):
            return Zodiac.CANCER.value
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return Zodiac.LEO.value
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return Zodiac.VIRGO.value
        elif (month == 9 and day >= 23) or (month == 10 and day <= 23):
            return Zodiac.LIBRA.value
        elif (month == 10 and day >= 24) or (month == 11 and day <= 22):
            return Zodiac.SCORPIO.value
        elif (month == 11 and day >= 23) or (month == 12 and day <= 21):
            return Zodiac.SAGITTARIUS.value
        else:  # (month == 12 and day >= 22) or (month == 1 and day <= 19)
            return Zodiac.CAPRICORN.value

    def _get_lunar_date(self, _date: datetime) -> str:
        """获取农历日期（简化版，暂时返回空）

        TODO: 可以后续集成 lunarcalendar 库
        """
        return ""

    def _calculate_weekend_days(self, date: datetime) -> int:
        """计算距离周末的天数"""
        weekday = date.weekday()
        if weekday >= 5:  # 周六或周日
            return 0
        else:
            return 5 - weekday  # 距离周六的天数

    def _calculate_salary_countdowns(self, date: datetime) -> List[CountdownItem]:
        """计算发薪日倒计时"""
        current_day = date.day
        salary_dates = [
            ("月初", 1),
            ("10号", 10),
            ("15号", 15),
            ("20号", 20),
            ("25号", 25),
            ("月底", self._get_last_day_of_month(date))
        ]

        countdowns = []
        for name, day in salary_dates:
            if current_day <= day:
                diff = day - current_day
            else:
                # 下个月的日期
                next_month = date.replace(day=1) + timedelta(days=32)
                next_month = next_month.replace(day=1)
                if name == "月底":
                    target_day = self._get_last_day_of_month(next_month)
                else:
                    target_day = day
                target_date = next_month.replace(day=target_day)
                diff = (target_date - date).days

            is_today = (diff == 0)
            countdowns.append(CountdownItem(name=name, days=diff, is_today=is_today))

        return countdowns

    def _calculate_festival_countdowns(self, date: datetime) -> List[CountdownItem]:
        """计算节日倒计时（使用动态获取的节假日数据）"""
        countdowns = []
        current_year = date.year
        # 将日期归零到当天 00:00，避免时间部分影响比较
        # 确保 date_only 是 naive datetime（无时区信息）
        if date.tzinfo is not None:
            date_only = date.replace(tzinfo=None)
        else:
            date_only = date
        date_only = date_only.replace(hour=0, minute=0, second=0, microsecond=0)

        # 直接调用同步方法获取节假日数据
        try:
            holidays = self.holiday_fetcher.fetch_holidays([current_year, current_year + 1])
        except Exception as e:
            from astrbot.api import logger
            logger.error(f"获取节假日数据失败: {e}")
            # 使用降级策略
            holidays = self.holiday_fetcher.get_fallback_holidays([current_year, current_year + 1])

        # 处理每个节假日
        for holiday in holidays:
            try:
                # 解析开始和结束日期
                start_date = datetime.strptime(holiday.start_date, "%Y-%m-%d")
                end_date = datetime.strptime(holiday.end_date, "%Y-%m-%d")

                # 如果节假日已过，跳过
                if end_date < date_only:
                    continue

                # 判断是否在假期区间内
                if start_date <= date_only <= end_date:
                    # 今天在假期内
                    is_today = True
                    days = 0
                else:
                    # 计算距离假期开始的天数
                    is_today = False
                    days = (start_date - date_only).days

                countdowns.append(CountdownItem(
                    name=holiday.name,
                    days=days,
                    is_today=is_today,
                    start_date=holiday.start_date,
                    end_date=holiday.end_date
                ))

            except Exception as e:
                from astrbot.api import logger
                logger.warning(f"处理节假日 {holiday.name} 失败: {e}")
                continue

        # 按照天数从小到大排序
        countdowns.sort(key=lambda x: x.days)

        # 只返回前 5 个最近的节假日
        return countdowns[:5]

    def _get_last_day_of_month(self, date: datetime) -> int:
        """获取月份的最后一天"""
        next_month = date.replace(day=28) + timedelta(days=4)
        last_day = (next_month - timedelta(days=next_month.day)).day
        return last_day

    def _generate_timeline(self) -> List[str]:
        """生成摸鱼时间轴"""
        return [
            "09:00 伪装上班",
            "10:30 假装思考",
            "11:30 上午摸鱼",
            "14:00 午后犯困",
            "16:00 深度摸鱼",
            "17:30 准备跑路"
        ]


__all__ = ["MoyuDataProvider"]
