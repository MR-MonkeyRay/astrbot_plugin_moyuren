"""调度器工具函数

提取为独立模块以便测试和复用
"""

import random
from datetime import datetime
from typing import List, Tuple


def should_delay_for_same_minute(
    task_queue: List[Tuple[datetime, str]],
    current_task_time: datetime
) -> bool:
    """
    判断是否需要为同一分钟内的后续任务添加延迟

    Args:
        task_queue: 任务队列 [(datetime, target), ...]，按时间排序
        current_task_time: 当前执行任务的计划时间

    Returns:
        bool: 如果队列中下一个任务与当前任务在同一分钟内，返回 True
    """
    if not task_queue:
        return False

    next_task_time, _ = task_queue[0]
    current_minute = current_task_time.replace(second=0, microsecond=0)
    next_minute = next_task_time.replace(second=0, microsecond=0)

    return current_minute == next_minute


def get_random_delay(min_delay: float = 1.0, max_delay: float = 5.0) -> float:
    """
    获取随机延迟值

    Args:
        min_delay: 最小延迟秒数，默认 1.0
        max_delay: 最大延迟秒数，默认 5.0

    Returns:
        float: 随机延迟秒数
    """
    return random.uniform(min_delay, max_delay)
