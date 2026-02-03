"""测试 utils/scheduler_utils.py 的延迟判断逻辑

直接导入真实函数进行测试，确保测试与实现保持同步
"""

import pytest
from datetime import datetime

from utils.scheduler_utils import should_delay_for_same_minute, get_random_delay


@pytest.mark.unit
class TestShouldDelayForSameMinute:
    """测试 should_delay_for_same_minute 函数"""

    def test_should_delay_same_minute_tasks(self):
        """同一分钟内有多个任务时应该延迟"""
        base_time = datetime(2024, 1, 15, 9, 0, 0)
        task1_time = base_time.replace(second=0)
        task2_time = base_time.replace(second=30)

        task_queue = [(task2_time, "group2")]

        result = should_delay_for_same_minute(task_queue, task1_time)
        assert result is True, "同一分钟内的任务应该触发延迟"

    def test_should_not_delay_different_minute_tasks(self):
        """不同分钟的任务不应该延迟"""
        task1_time = datetime(2024, 1, 15, 9, 0, 0)
        task2_time = datetime(2024, 1, 15, 9, 1, 0)

        task_queue = [(task2_time, "group2")]

        result = should_delay_for_same_minute(task_queue, task1_time)
        assert result is False, "不同分钟的任务不应该触发延迟"

    def test_should_not_delay_when_queue_empty(self):
        """队列为空时不应该延迟"""
        task1_time = datetime(2024, 1, 15, 9, 0, 0)
        task_queue = []

        result = should_delay_for_same_minute(task_queue, task1_time)
        assert result is False, "队列为空时不应该触发延迟"

    def test_should_delay_same_minute_different_seconds(self):
        """同一分钟不同秒数应该延迟"""
        base_time = datetime(2024, 1, 15, 9, 30, 0)

        test_cases = [
            (base_time.replace(second=0), base_time.replace(second=59)),
            (base_time.replace(second=15), base_time.replace(second=45)),
            (base_time.replace(second=59), base_time.replace(second=0)),
        ]

        for task1_time, task2_time in test_cases:
            task_queue = [(task2_time, "group2")]
            result = should_delay_for_same_minute(task_queue, task1_time)
            assert result is True, f"同分钟任务 {task1_time.second}s -> {task2_time.second}s 应该延迟"

    def test_should_not_delay_cross_minute_boundary(self):
        """跨分钟边界不应该延迟（59秒 -> 下一分钟00秒）"""
        task1_time = datetime(2024, 1, 15, 9, 0, 59)
        task2_time = datetime(2024, 1, 15, 9, 1, 0)

        task_queue = [(task2_time, "group2")]

        result = should_delay_for_same_minute(task_queue, task1_time)
        assert result is False, "跨分钟边界不应该触发延迟"

    def test_should_not_delay_cross_hour_boundary(self):
        """跨小时边界不应该延迟"""
        task1_time = datetime(2024, 1, 15, 8, 59, 30)
        task2_time = datetime(2024, 1, 15, 9, 0, 0)

        task_queue = [(task2_time, "group2")]

        result = should_delay_for_same_minute(task_queue, task1_time)
        assert result is False, "跨小时边界不应该触发延迟"

    def test_should_not_delay_cross_day_boundary(self):
        """跨天边界不应该延迟"""
        task1_time = datetime(2024, 1, 15, 23, 59, 30)
        task2_time = datetime(2024, 1, 16, 0, 0, 0)

        task_queue = [(task2_time, "group2")]

        result = should_delay_for_same_minute(task_queue, task1_time)
        assert result is False, "跨天边界不应该触发延迟"


@pytest.mark.unit
class TestGetRandomDelay:
    """测试 get_random_delay 函数"""

    def test_delay_value_in_default_range(self):
        """默认延迟值应该在 1.0-5.0 范围内"""
        for _ in range(100):
            delay = get_random_delay()
            assert 1.0 <= delay <= 5.0, f"延迟值 {delay} 不在默认 [1.0, 5.0] 范围内"

    def test_delay_value_in_custom_range(self):
        """自定义范围的延迟值应该在指定范围内"""
        for _ in range(100):
            delay = get_random_delay(min_delay=2.0, max_delay=3.0)
            assert 2.0 <= delay <= 3.0, f"延迟值 {delay} 不在 [2.0, 3.0] 范围内"

    def test_delay_returns_float(self):
        """延迟值应该是浮点数"""
        delay = get_random_delay()
        assert isinstance(delay, float), "延迟值应该是浮点数"


@pytest.mark.unit
class TestDelaySequence:
    """测试多任务延迟序列"""

    def test_multiple_same_minute_tasks_all_need_delay(self):
        """多个同分钟任务，除最后一个外都需要延迟"""
        base_time = datetime(2024, 1, 15, 9, 0, 0)

        tasks = [
            (base_time.replace(second=0), "group1"),
            (base_time.replace(second=20), "group2"),
            (base_time.replace(second=40), "group3"),
        ]

        delay_needed = []

        for i, (task_time, _) in enumerate(tasks):
            remaining_queue = tasks[i + 1:]
            if remaining_queue:
                result = should_delay_for_same_minute(remaining_queue, task_time)
                delay_needed.append(result)

        assert delay_needed == [True, True], "前两个任务执行后都应该需要延迟"

    def test_mixed_minute_tasks(self):
        """混合分钟任务的延迟判断"""
        tasks = [
            (datetime(2024, 1, 15, 9, 0, 0), "group1"),
            (datetime(2024, 1, 15, 9, 0, 30), "group2"),
            (datetime(2024, 1, 15, 9, 1, 0), "group3"),
            (datetime(2024, 1, 15, 9, 1, 30), "group4"),
        ]

        delay_needed = []

        for i, (task_time, _) in enumerate(tasks):
            remaining_queue = tasks[i + 1:]
            if remaining_queue:
                result = should_delay_for_same_minute(remaining_queue, task_time)
                delay_needed.append(result)

        expected = [True, False, True]
        assert delay_needed == expected, f"延迟判断结果应为 {expected}，实际为 {delay_needed}"
