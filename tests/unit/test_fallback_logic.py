"""测试降级逻辑（部分失败场景）"""

import sys
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


def test_partial_failure():
    """测试部分年份失败的降级逻辑"""
    print("=" * 60)
    print("测试部分年份失败的降级逻辑")
    print("=" * 60)

    # 创建节假日获取器
    fetcher = HolidayFetcher("./test_cache_partial")

    # 测试：2026 年成功，9999 年失败（不存在的年份）
    print("\n测试场景：2026 年成功，9999 年失败")
    print("-" * 60)

    holidays = fetcher.fetch_holidays([2026, 9999])

    print(f"\n✅ 获取到 {len(holidays)} 个节假日")

    # 统计各年份的节假日数量
    year_2026_count = sum(1 for h in holidays if h.start_date.startswith("2026"))
    year_9999_count = sum(1 for h in holidays if h.start_date.startswith("9999"))

    print(f"\n2026 年节假日数量: {year_2026_count}")
    print(f"9999 年节假日数量: {year_9999_count}")

    if year_9999_count > 0:
        print("\n✅ 降级逻辑正确触发：失败年份补充了基本节假日")
        print("\n9999 年的基本节假日:")
        for h in holidays:
            if h.start_date.startswith("9999"):
                print(f"  - {h.name}: {h.start_date}")
    else:
        print("\n❌ 降级逻辑未触发：失败年份没有节假日")


def test_all_failure():
    """测试所有年份失败的降级逻辑"""
    print("\n" + "=" * 60)
    print("测试所有年份失败的降级逻辑")
    print("=" * 60)

    # 创建节假日获取器
    fetcher = HolidayFetcher("./test_cache_all_fail")

    # 测试：所有年份都失败
    print("\n测试场景：8888 年和 9999 年都失败")
    print("-" * 60)

    holidays = fetcher.fetch_holidays([8888, 9999])

    print(f"\n✅ 获取到 {len(holidays)} 个节假日")

    # 统计各年份的节假日数量
    year_8888_count = sum(1 for h in holidays if h.start_date.startswith("8888"))
    year_9999_count = sum(1 for h in holidays if h.start_date.startswith("9999"))

    print(f"\n8888 年节假日数量: {year_8888_count}")
    print(f"9999 年节假日数量: {year_9999_count}")

    if year_8888_count > 0 and year_9999_count > 0:
        print("\n✅ 降级逻辑正确触发：所有失败年份都补充了基本节假日")
    else:
        print("\n❌ 降级逻辑未触发：失败年份没有节假日")


def test_public_method():
    """测试公共方法 get_fallback_holidays"""
    print("\n" + "=" * 60)
    print("测试公共方法 get_fallback_holidays")
    print("=" * 60)

    # 创建节假日获取器
    fetcher = HolidayFetcher("./test_cache_public")

    # 直接调用公共方法
    print("\n直接调用 get_fallback_holidays([2026, 2027])")
    print("-" * 60)

    holidays = fetcher.get_fallback_holidays([2026, 2027])

    print(f"\n✅ 获取到 {len(holidays)} 个基本节假日")

    # 统计各年份的节假日数量
    year_2026_count = sum(1 for h in holidays if h.start_date.startswith("2026"))
    year_2027_count = sum(1 for h in holidays if h.start_date.startswith("2027"))

    print(f"\n2026 年节假日数量: {year_2026_count}")
    print(f"2027 年节假日数量: {year_2027_count}")

    print("\n2026 年的基本节假日:")
    for h in holidays:
        if h.start_date.startswith("2026"):
            print(f"  - {h.name}: {h.start_date}")


if __name__ == "__main__":
    # 测试部分失败场景
    test_partial_failure()

    # 测试所有失败场景
    test_all_failure()

    # 测试公共方法
    test_public_method()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
