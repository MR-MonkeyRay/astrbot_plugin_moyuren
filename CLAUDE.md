# AstrBot 摸鱼人日历插件

## 架构总览

### 技术栈
- **语言**：Python 3.11+
- **框架**：AstrBot Plugin API
- **依赖**：aiohttp, PyYAML
- **测试**：pytest, pytest-cov, pytest-asyncio

## 模块索引

| 模块路径 | 职责 | 关键文件 |
|---------|------|---------|
| `/` | 插件入口与注册 | `main.py`, `__init__.py` |
| `core/` | 核心业务逻辑层 | `config.py`, `image.py`, `scheduler.py` |
| `handlers/` | 命令处理层 | `command.py` |
| `models/` | 数据模型层 | `config_schema.py`, `moyu.py`, `moyu_static.py` |
| `utils/` | 工具模块层 | `paths.py`, `decorators.py`, `scheduler_utils.py` |
| `tests/` | 单元测试 | `test_*.py`, `conftest.py` |
| `data/` | 数据与模板 | `cmd_config.json`, `t2i_templates/*.html` |

## 运行与开发

### python环境

`~/miniconda3/bin/python`

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
# 运行所有测试
pytest

# 生成覆盖率报告
pytest --cov=core --cov=handlers --cov=utils --cov=models --cov-report=html

# 运行所有测试（包括覆盖率）
pytest tests/ -v --cov=. --cov-report=html
```

### 配置文件

- 插件配置：`_conf_schema.json` (AstrBot 配置界面可编辑)
- 数据存放路径：`{AstrBot数据目录}/plugin_data/astrbot_plugin_moyuren/`
- 测试配置：`pytest.ini`, `.coveragerc`

### 关键路径

```python
# 插件根目录
PLUGIN_ROOT = Path(__file__).parents[1]

# AstrBot 数据目录
DATA_ROOT = Path(get_astrbot_data_path()) / "plugin_data" / "astrbot_plugin_moyuren"
CONFIG_DIR = DATA_ROOT
CACHE_DIR = DATA_ROOT / "cache"
```

## 测试策略

- 工具：pytest + pytest-asyncio + pytest-cov
- 标记：`@pytest.mark.asyncio`
- 覆盖率目标：核心模块 > 80%

### 测试结构

```
tests/
├── conftest.py              # 测试夹具
├── test_paths.py            # 路径工具测试
├── test_models.py           # 数据模型测试
├── test_image_template.py   # 图片模板测试
└── test_scheduler_delay.py  # 调度延迟测试
```

## 编码规范

- 格式化：遵循 PEP 8
- 类型注解：使用 Python 3.10+ 类型提示（如 `tuple[int, int]`）
- 文档字符串：所有公共函数/类必须有 docstring

### 架构原则

1. 分层清晰：业务逻辑（core）、命令处理（handlers）、数据模型（models）严格分离
2. 依赖注入：通过构造函数传递依赖（如 `ConfigManager`, `ImageManager`）
3. 错误处理：使用装饰器统一处理错误（`@config_operation_handler`, `@command_error_handler`）
4. 异步优先：网络 I/O 使用 `async/await`，文件 I/O 使用同步操作

## AI 使用指引

#### 添加新命令
1. 在 `handlers/command.py` 的 `CommandHelper` 类中添加处理方法
2. 在 `main.py` 的 `MoyuRenPlugin` 类中添加 `@filter.command` 装饰的方法
3. 更新 `metadata.yaml` 的 help 文档

#### 修改配置项
1. 更新 `_conf_schema.json` 添加新配置项
2. 在 `core/config.py` 或 `core/image.py` 中读取配置
3. 更新 README.md 的配置说明

#### 添加新 API 源
1. 在 `_conf_schema.json` 的 `api_endpoints` 数组中添加
2. `core/image.py` 的 `get_moyu_image` 会按顺序尝试各端点，自动故障转移

### 调试技巧

- 日志：使用 `from astrbot.api import logger`，统一日志输出
- 测试：使用 `pytest -v -s` 查看详细输出
- Mock：参考 `tests/conftest.py` 的 fixture 定义
