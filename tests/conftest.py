import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import MagicMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_logger():
    """Mock logger"""
    logger = MagicMock()
    return logger

@pytest.fixture
def mock_context():
    """Mock AstrBot context"""
    context = MagicMock()
    context.base_config = {"data_path": "/tmp/test_data"}
    return context
