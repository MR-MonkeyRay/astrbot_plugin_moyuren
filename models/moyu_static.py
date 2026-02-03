"""摸鱼日历静态数据枚举"""
from enum import Enum


class MoyuQuote(Enum):
    """摸鱼语录"""
    QUOTE_1 = "今日宜摸鱼，忌认真工作"
    QUOTE_2 = "摸鱼时记得屏蔽老板，财运+1"
    QUOTE_3 = "适合带薪拉屎，摸鱼指数拉满"
    QUOTE_4 = "小心领导突击检查，建议低调摸鱼"
    QUOTE_5 = "摸鱼虽好，可不要贪杯哦"
    QUOTE_6 = "工资月入一千八,每天笑哈哈"
    QUOTE_7 = "上班摸鱼爽，一直摸鱼一直爽"
    QUOTE_8 = "天天满嘴辞职，月月考核满勤"


class ZodiacFortune(Enum):
    """星座运势"""
    FORTUNE_1 = "灵感爆棚，先摸再说"
    FORTUNE_2 = "摸鱼需谨慎，老板在附近"
    FORTUNE_3 = "适合摸鱼，不宜内卷"
    FORTUNE_4 = "摸鱼效率MAX"
    FORTUNE_5 = "小心摸鱼被抓"
    FORTUNE_6 = "摸鱼不忘干饭"


class Zodiac(Enum):
    """星座"""
    CAPRICORN = "摩羯座"
    AQUARIUS = "水瓶座"
    PISCES = "双鱼座"
    ARIES = "白羊座"
    TAURUS = "金牛座"
    GEMINI = "双子座"
    CANCER = "巨蟹座"
    LEO = "狮子座"
    VIRGO = "处女座"
    LIBRA = "天秤座"
    SCORPIO = "天蝎座"
    SAGITTARIUS = "射手座"


__all__ = ["MoyuQuote", "ZodiacFortune", "Zodiac"]
