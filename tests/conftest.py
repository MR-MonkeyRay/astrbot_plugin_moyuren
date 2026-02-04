import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 测试临时目录
TEST_TMP_DIR = project_root / "tmp"

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    TEST_TMP_DIR.mkdir(parents=True, exist_ok=True)
    yield TEST_TMP_DIR

@pytest.fixture
def mock_logger():
    """Mock logger"""
    logger = MagicMock()
    return logger

@pytest.fixture
def mock_context():
    """Mock AstrBot context"""
    context = MagicMock()
    context.base_config = {"data_path": str(TEST_TMP_DIR)}
    return context
