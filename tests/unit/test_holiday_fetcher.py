"""测试节假日获取器"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parents[2]))

# 模拟 astrbot 模块
class MockLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARNING] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def debug(self, msg): print(f"[DEBUG] {msg}")

def mock_get_astrbot_data_path():
    return str(Path(__file__).parent / "test_data")

# 创建模拟模块
sys.modules['astrbot'] = type('Module', (), {})()
sys.modules['astrbot.api'] = type('Module', (), {'logger': MockLogger()})()
sys.modules['astrbot.core'] = type('Module', (), {})()
sys.modules['astrbot.core.utils'] = type('Module', (), {})()
sys.modules['astrbot.core.utils.astrbot_path'] = type('Module', (), {
    'get_astrbot_data_path': mock_get_astrbot_data_path
})()

from core.rendering.holiday_fetcher import HolidayFetcher
from core.rendering.data_provider import MoyuDataProvider


async def test_holiday_fetcher():
    """测试节假日获取器"""
    print("=" * 60)
    print("测试节假日获取器")
    print("=" * 60)

    # 创建节假日获取器
    fetcher = HolidayFetcher("./test_cache")

    try:
        # 获取 2026 年和 2027 年的节假日
        print("\n正在获取 2026-2027 年节假日数据...")
        holidays = await fetcher.fetch_holidays([2026, 2027])

        print(f"\n成功获取 {len(holidays)} 个节假日：")
        for holiday in holidays[:10]:  # 只显示前 10 个
            print(f"  - {holiday.name}: {holiday.start_date} 至 {holiday.end_date}")

        if len(holidays) > 10:
            print(f"  ... 还有 {len(holidays) - 10} 个节假日")

    except Exception as e:
        print(f"\n❌ 获取节假日失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await fetcher.close()


def test_data_provider():
    """测试数据提供者"""
    print("\n" + "=" * 60)
    print("测试数据提供者")
    print("=" * 60)

    try:
        # 创建数据提供者
        provider = MoyuDataProvider()

        # 生成摸鱼日历数据
        print("\n正在生成摸鱼日历数据...")
        data = provider.generate_moyu_data(datetime(2026, 1, 25))

        print(f"\n✅ 成功生成摸鱼日历数据")
        print(f"  日期: {data.date.strftime('%Y-%m-%d')}")
        print(f"  摸鱼指数: {data.moyu_index}%")
        print(f"  摸鱼等级: {data.moyu_level}")

        print(f"\n节日倒计时 ({len(data.festival_countdowns)} 个):")
        for item in data.festival_countdowns:
            date_range = item.format_date_range()
            countdown = item.format_countdown()
            print(f"  - {item.name}: {date_range} ({countdown})")

    except Exception as e:
        print(f"\n❌ 生成数据失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 测试节假日获取器
    asyncio.run(test_holiday_fetcher())

    # 测试数据提供者
    test_data_provider()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
