# AstrBot 摸鱼人日历插件

---

## 架构总览

### 技术栈
- **语言**：Python 3.11+
- **框架**：AstrBot Plugin API
- **依赖**：aiohttp, PyYAML, imgkit (可选)
- **测试**：pytest, pytest-cov, pytest-asyncio

---

## 模块索引

| 模块路径 | 职责 | 关键文件 |
|---------|------|---------|
| `/` | 插件入口与注册 | `main.py`, `__init__.py` |
| `core/` | 核心业务逻辑层 | `config.py`, `image.py`, `scheduler.py` |
| `core/rendering/` | 本地渲染子模块 | `wkhtml_renderer.py`, `data_provider.py` |
| `handlers/` | 命令处理层 | `command.py` |
| `models/` | 数据模型层 | `config_schema.py`, `moyu.py`, `moyu_static.py` |
| `utils/` | 工具模块层 | `paths.py`, `constants.py`, `decorators.py` |
| `tests/` | 单元测试 | `test_*.py`, `conftest.py` |
| `data/` | 数据与模板 | `t2i_templates/*.html` |

---

## 运行与开发

### python环境

`~/miniconda3/bin/python`

### 安装依赖

```bash
# 基础依赖
pip install -r requirements.txt

# 本地渲染模式（可选）
pip install imgkit
# 并安装 wkhtmltoimage: https://wkhtmltopdf.org/downloads.html
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest -m unit

# 生成覆盖率报告
pytest --cov=core --cov=handlers --cov=utils --cov=models --cov-report=html
```

### 配置文件

- **插件配置**：`_conf_schema.json` (AstrBot 配置界面可编辑)
- **数据存放路径**：`{AstrBot数据目录}/plugin_data/astrbot_plugin_moyuren/`
- **测试配置**：`pytest.ini`, `.coveragerc`

### 关键路径

```python
# 插件根目录
PLUGIN_ROOT = Path(__file__).parents[1]

# AstrBot 数据目录
DATA_ROOT = Path(get_astrbot_data_path()) / "plugin_data" / "astrbot_plugin_moyuren"
CONFIG_DIR = DATA_ROOT
CACHE_DIR = DATA_ROOT / "cache"
```

---

## 测试策略

### 测试框架
- **工具**：pytest + pytest-asyncio + pytest-cov
- **标记**：`@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.asyncio`
- **覆盖率目标**：核心模块 > 80%

### 测试结构

```
tests/
├── conftest.py              # 测试夹具（temp_dir, mock_logger, mock_context）
├── unit/                    # 单元测试
│   ├── __init__.py
│   ├── test_constants.py   # 常量测试
│   ├── test_models.py      # 数据模型测试
│   ├── test_paths.py       # 路径工具测试
│   ├── test_holiday_fetcher.py  # 节假日获取器测试
│   └── test_fallback_logic.py   # 降级逻辑测试
├── integration/             # 集成测试
│   ├── __init__.py
│   └── test_wkhtml_render.py    # 渲染器集成测试
└── manual/                  # 手动测试
    ├── __init__.py
    └── test_holiday_simple.py   # 节假日数据简单测试
```

### 运行测试

```bash
# 先导入环境变量,再运行测试
PYTHONPATH=$(pwd)

# 运行所有单元测试
pytest tests/unit/ -v

# 运行图片渲染测试
python tests/integration/test_wkhtml_render.py

# 运行节假日数据简单测试
python tests/manual/test_holiday_simple.py

# 运行所有测试（包括覆盖率）
pytest tests/ -v --cov=. --cov-report=html
```

---

## 编码规范

### 代码风格
- **格式化**：遵循 PEP 8
- **类型注解**：使用 Python 3.10+ 类型提示（如 `tuple[int, int]`）
- **文档字符串**：所有公共函数/类必须有 docstring

### 架构原则
1. **分层清晰**：业务逻辑（core）、命令处理（handlers）、数据模型（models）严格分离
2. **依赖注入**：通过构造函数传递依赖（如 `ConfigManager`, `ImageManager`）
3. **错误处理**：使用装饰器统一处理错误（`@config_operation_handler`, `@command_error_handler`）
4. **异步优先**：所有 I/O 操作使用 `async/await`

### 命名约定
- **类名**：PascalCase（如 `ConfigManager`）
- **函数名**：snake_case（如 `load_config`）
- **常量**：UPPER_SNAKE_CASE（如 `PLUGIN_VERSION`）
- **私有方法**：前缀 `_`（如 `_get_session`）

---

## AI 使用指引

### 代码修改流程
1. **理解架构**：先阅读本文档的"架构总览"和"模块索引"
2. **定位模块**：根据需求找到对应的层（core/handlers/models/utils）
3. **查看依赖**：检查模块间的依赖关系（通过 import 语句）
4. **修改代码**：遵循"编码规范"进行修改
5. **运行测试**：确保现有测试通过，必要时添加新测试

### 常见任务指引

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
2. `core/image.py` 的 `_download_from_api` 会自动故障转移

#### 扩展本地渲染
1. 修改 `core/rendering/data_provider.py` 生成数据
2. 更新 `core/rendering/moyu_template.html` 模板
3. 调整 `core/rendering/wkhtml_renderer.py` 渲染参数

### 关键文件速查

| 需求 | 文件路径 |
|------|---------|
| 插件入口与生命周期 | `main.py` |
| 命令处理逻辑 | `handlers/command.py` |
| 配置管理 | `core/config.py` |
| 图片获取与缓存 | `core/image.py` |
| 定时任务调度 | `core/scheduler.py` |
| 本地渲染 | `core/rendering/wkhtml_renderer.py` |
| 数据模型 | `models/moyu.py`, `models/config_schema.py` |
| 路径管理 | `utils/paths.py` |
| 错误处理装饰器 | `utils/decorators.py` |

### 调试技巧
- **日志**：使用 `from astrbot.api import logger`，统一日志输出
- **测试**：使用 `pytest -v -s` 查看详细输出
- **Mock**：参考 `tests/conftest.py` 的 fixture 定义

---

## 贡献指南

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

**注意**：提交前请确保：
- 所有测试通过（`pytest`）
- 代码符合 PEP 8 规范
- 添加了必要的测试用例
- 更新了相关文档