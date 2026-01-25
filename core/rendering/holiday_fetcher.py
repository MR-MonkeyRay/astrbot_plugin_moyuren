"""节假日数据获取器 - 从 holiday-cn API 获取节假日信息（同步版本）"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

import requests
from astrbot.api import logger


@dataclass
class HolidayInfo:
    """节假日信息"""
    name: str  # 节假日名称
    start_date: str  # 开始日期 (YYYY-MM-DD)
    end_date: str  # 结束日期 (YYYY-MM-DD)


class HolidayFetcher:
    """节假日数据获取器（同步版本）"""

    API_URL_TEMPLATE = "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json"
    CACHE_EXPIRY_HOURS = 24  # 缓存过期时间（小时）
    REQUEST_TIMEOUT = 10  # 请求超时时间（秒）

    def __init__(self, cache_dir: str):
        """初始化节假日获取器

        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_holidays(self, years: List[int]) -> List[HolidayInfo]:
        """获取指定年份的节假日数据（同步方法）

        Args:
            years: 年份列表（如 [2026, 2027]）

        Returns:
            List[HolidayInfo]: 节假日信息列表
        """
        all_holidays = []
        failed_years = []

        for year in years:
            try:
                holidays = self._fetch_year_holidays(year)
                all_holidays.extend(holidays)
            except Exception as e:
                logger.warning(f"获取 {year} 年节假日数据失败: {e}")
                failed_years.append(year)

        # 对失败的年份补充基本节假日
        if failed_years:
            logger.warning(f"为失败的年份 {failed_years} 补充基本节假日")
            fallback_holidays = self.get_fallback_holidays(failed_years)
            all_holidays.extend(fallback_holidays)

        return all_holidays

    def _fetch_year_holidays(self, year: int) -> List[HolidayInfo]:
        """获取单个年份的节假日数据（同步方法）

        Args:
            year: 年份

        Returns:
            List[HolidayInfo]: 节假日信息列表
        """
        cache_file = self.cache_dir / f"{year}.json"

        # 检查缓存
        if self._is_cache_valid(cache_file):
            logger.info(f"使用缓存的 {year} 年节假日数据")
            holidays = self._load_from_cache(cache_file)
            # 如果缓存有效但内容为空或损坏，删除缓存并重新获取
            if not holidays:
                logger.warning(f"缓存文件 {cache_file} 内容为空或损坏，删除并重新获取")
                cache_file.unlink(missing_ok=True)
            else:
                return holidays

        # 从 API 获取
        logger.info(f"从 API 获取 {year} 年节假日数据...")
        url = self.API_URL_TEMPLATE.format(year=year)

        try:
            response = requests.get(url, timeout=self.REQUEST_TIMEOUT)
            if response.status_code == 200:
                # GitHub raw 返回 text/plain，需要手动解析 JSON
                data = response.json()
                holidays = self._parse_api_data(data)

                # 保存到缓存
                self._save_to_cache(cache_file, holidays)

                logger.info(f"成功获取 {year} 年节假日数据，共 {len(holidays)} 个节假日")
                return holidays
            else:
                logger.warning(f"API 返回错误状态码: {response.status_code}")
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"从 API 获取 {year} 年节假日数据失败: {e}")
            # 尝试使用过期缓存
            if cache_file.exists():
                logger.info(f"使用过期缓存的 {year} 年节假日数据")
                holidays = self._load_from_cache(cache_file)
                if holidays:
                    return holidays
            raise

    def _parse_api_data(self, data: dict) -> List[HolidayInfo]:
        """解析 holiday-cn API 数据

        API 数据格式示例：
        {
            "year": 2026,
            "days": [
                {"name": "元旦", "date": "2026-01-01", "isOffDay": true},
                {"name": "元旦", "date": "2026-01-02", "isOffDay": true},
                ...
            ]
        }

        Args:
            data: API 返回的 JSON 数据

        Returns:
            List[HolidayInfo]: 节假日信息列表
        """
        holidays_dict: Dict[str, List[str]] = {}

        # 按节假日名称分组日期
        for day in data.get("days", []):
            if day.get("isOffDay"):
                name = day.get("name")
                date = day.get("date")
                if name and date:
                    if name not in holidays_dict:
                        holidays_dict[name] = []
                    holidays_dict[name].append(date)

        # 转换为 HolidayInfo 对象
        holidays = []
        for name, dates in holidays_dict.items():
            if dates:
                dates.sort()
                holidays.append(HolidayInfo(
                    name=name,
                    start_date=dates[0],
                    end_date=dates[-1]
                ))

        return holidays

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """检查缓存是否有效

        Args:
            cache_file: 缓存文件路径

        Returns:
            bool: 缓存是否有效
        """
        if not cache_file.exists():
            return False

        # 检查缓存是否过期
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        expiry_time = mtime + timedelta(hours=self.CACHE_EXPIRY_HOURS)
        return datetime.now() < expiry_time

    def _load_from_cache(self, cache_file: Path) -> List[HolidayInfo]:
        """从缓存加载节假日数据

        Args:
            cache_file: 缓存文件路径

        Returns:
            List[HolidayInfo]: 节假日信息列表
        """
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not data:  # 空列表或空字典
                    logger.warning(f"缓存文件 {cache_file} 内容为空")
                    return []
                return [HolidayInfo(**item) for item in data]
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return []

    def _save_to_cache(self, cache_file: Path, holidays: List[HolidayInfo]):
        """保存节假日数据到缓存

        Args:
            cache_file: 缓存文件路径
            holidays: 节假日信息列表
        """
        try:
            data = [
                {
                    "name": h.name,
                    "start_date": h.start_date,
                    "end_date": h.end_date
                }
                for h in holidays
            ]
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"节假日数据已缓存到: {cache_file}")
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def get_fallback_holidays(self, years: List[int]) -> List[HolidayInfo]:
        """获取降级节假日数据（基本节假日）

        Args:
            years: 年份列表

        Returns:
            List[HolidayInfo]: 基本节假日信息列表
        """
        basic_holidays = [
            ("元旦", 1, 1),
            ("春节", 2, 10),  # 近似日期
            ("清明节", 4, 4),
            ("劳动节", 5, 1),
            ("端午节", 6, 10),  # 近似日期
            ("中秋节", 9, 15),  # 近似日期
            ("国庆节", 10, 1),
        ]

        holidays = []
        for year in years:
            for name, month, day in basic_holidays:
                date_str = f"{year}-{month:02d}-{day:02d}"
                holidays.append(HolidayInfo(
                    name=name,
                    start_date=date_str,
                    end_date=date_str
                ))

        return holidays


__all__ = ["HolidayFetcher", "HolidayInfo"]
