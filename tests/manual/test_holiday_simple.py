"""简化的节假日获取器测试（同步版本）"""

import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parents[2]))


def test_holiday_api():
    """测试节假日 API 数据格式"""
    print("=" * 60)
    print("测试节假日 API 数据格式")
    print("=" * 60)

    import requests

    url = "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/2026.json"
    print(f"\n正在获取: {url}")

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 成功获取数据")
            print(f"  年份: {data.get('year')}")
            print(f"  天数: {len(data.get('days', []))}")

            # 显示前 10 个节假日
            print("\n前 10 个节假日:")
            for i, day in enumerate(data.get('days', [])[:10]):
                if day.get('isOffDay'):
                    print(f"  {i+1}. {day.get('name')} - {day.get('date')}")

            # 测试解析逻辑
            print("\n测试解析逻辑:")
            holidays_dict = {}
            for day in data.get("days", []):
                if day.get("isOffDay"):
                    name = day.get("name")
                    date = day.get("date")
                    if name and date:
                        if name not in holidays_dict:
                            holidays_dict[name] = []
                        holidays_dict[name].append(date)

            print(f"\n解析出 {len(holidays_dict)} 个节假日:")
            for name, dates in list(holidays_dict.items())[:5]:
                dates.sort()
                print(f"  - {name}: {dates[0]} 至 {dates[-1]} (共 {len(dates)} 天)")

        else:
            print(f"\n❌ API 返回错误状态码: {response.status_code}")

    except Exception as e:
        print(f"\n❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()


def test_countdown_item():
    """测试 CountdownItem 数据模型"""
    print("\n" + "=" * 60)
    print("测试 CountdownItem 数据模型")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent))
    from models.moyu import CountdownItem

    # 测试普通节假日
    item1 = CountdownItem(
        name="春节",
        days=30,
        is_today=False,
        start_date="2026-02-17",
        end_date="2026-02-23"
    )

    print(f"\n测试 1: 普通节假日")
    print(f"  名称: {item1.name}")
    print(f"  日期区间: {item1.format_date_range()}")
    print(f"  倒计时: {item1.format_countdown()}")

    # 测试今天的节假日
    item2 = CountdownItem(
        name="元旦",
        days=0,
        is_today=True,
        start_date="2026-01-01",
        end_date="2026-01-03"
    )

    print(f"\n测试 2: 今天的节假日")
    print(f"  名称: {item2.name}")
    print(f"  日期区间: {item2.format_date_range()}")
    print(f"  倒计时: {item2.format_countdown()}")

    # 测试单天节假日
    item3 = CountdownItem(
        name="清明",
        days=70,
        is_today=False,
        start_date="2026-04-05",
        end_date="2026-04-05"
    )

    print(f"\n测试 3: 单天节假日")
    print(f"  名称: {item3.name}")
    print(f"  日期区间: {item3.format_date_range()}")
    print(f"  倒计时: {item3.format_countdown()}")

    print("\n✅ CountdownItem 测试通过")


if __name__ == "__main__":
    # 测试 API 数据格式
    test_holiday_api()

    # 测试数据模型
    test_countdown_item()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
