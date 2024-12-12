# 🌏 TransX

[English](README.md) | 简体中文

🚀 一个轻量级、零依赖的 Python 国际化库，支持 Python 2.7 到 3.12 版本。

该 API 专为 [DCC](https://en.wikipedia.org/wiki/Digital_content_creation) 工具设计，例如可与 [Maya](https://www.autodesk.com/products/maya/overview)、[3DsMax](https://www.autodesk.com/products/3ds-max/overview)、[Houdini](https://www.sidefx.com/products/houdini/) 等软件完美配合。

<div align="center">

[![Python Version](https://img.shields.io/pypi/pyversions/transx)](https://img.shields.io/pypi/pyversions/transx)
[![Nox](https://img.shields.io/badge/%F0%9F%A6%8A-Nox-D85E00.svg)](https://github.com/wntrblm/nox)
[![PyPI Version](https://img.shields.io/pypi/v/transx?color=green)](https://pypi.org/project/transx/)
[![Downloads](https://static.pepy.tech/badge/transx)](https://pepy.tech/project/transx)
[![Downloads](https://static.pepy.tech/badge/transx/month)](https://pepy.tech/project/transx)
[![Downloads](https://static.pepy.tech/badge/transx/week)](https://pepy.tech/project/transx)
[![License](https://img.shields.io/pypi/l/transx)](https://pypi.org/project/transx/)
[![PyPI Format](https://img.shields.io/pypi/format/transx)](https://pypi.org/project/transx/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/loonghao/transx/graphs/commit-activity)
![Codecov](https://img.shields.io/codecov/c/github/loonghao/transx)
[![性能测试](https://img.shields.io/badge/benchmarks-查看性能-blue)](https://loonghao.github.io/transx-benchmarks/)
</div>

---

## ✨ 特性

TransX 提供了全面的国际化功能：

- 🚀 **零依赖**: 无需任何外部依赖
- 🐍 **Python 支持**: 完全支持 Python 2.7-3.12
- 🌍 **上下文支持**: 基于上下文的精确翻译
- 📦 **标准格式**: 兼容 gettext .po/.mo 文件
- 🎯 **简洁 API**: 清晰直观的接口
- 🔄 **自动管理**: 自动处理翻译文件
- 🔍 **字符串提取**: 内置源代码字符串提取
- 🌐 **Unicode**: 完整的 Unicode 支持
- 🔠 **参数支持**: 支持命名、位置和 ${var} 风格的参数
- 💫 **变量支持**: 支持环境变量展开
- ⚡ **高性能**: 高速且线程安全的操作
- 🛡️ **错误处理**: 全面的错误管理和回退机制
- 🧪 **测试覆盖**: 100% 测试覆盖率
- 🌐 **自动翻译**: 内置 Google 翻译 API 支持
- 🎥 **DCC 支持**: 已在 Maya、3DsMax、Houdini 等软件中测试
- 🔌 **可扩展**: 可插拔的自定义文本解释器
- 🎨 **灵活格式**: 支持多种字符串格式化风格
- 🔄 **运行时切换**: 支持运行时动态切换语言
- 🔧 **Qt 集成**: 内置 Qt 翻译支持
- 📝 **消息提取**: 高级源代码消息提取（支持上下文）
- 🌐 **多应用支持**: 支持多应用的翻译实例管理

## GNU gettext 兼容性

TransX 完全兼容 GNU gettext 标准，可与现有翻译工作流无缝集成：

- **标准格式**: 完全支持 `.po` 和 `.mo` 文件格式
- **文件结构**: 遵循标准的语言目录结构 (`LC_MESSAGES/domain.{po,mo}`)
- **头部支持**: 完整支持 gettext 头部和元数据
- **复数形式**: 兼容 gettext 复数形式表达式和处理
- **上下文支持**: 使用 gettext 标准分隔符完全支持 msgctxt（消息上下文）
- **编码处理**: 按照 PO/MO 头部规范正确处理字符编码
- **工具集成**: 可与标准 gettext 工具（msgfmt、msginit、msgmerge 等）配合使用
- **二进制格式**: 实现官方 MO 文件格式规范，支持大小端序

这意味着您可以：
- 使用现有的 PO 编辑器，如 Poedit、Lokalize 或 GTranslator
- 与已建立的翻译工作流程集成
- 无缝迁移现有的基于 gettext 的翻译
- 与 TransX 一起使用标准 gettext 工具
- 保持与其他基于 gettext 的系统的兼容性

## 🚀 快速开始

### 📥 安装

```bash
pip install transx
```

### 📝 基本使用

```python
from transx import TransX

# 初始化翻译实例
tx = TransX(locales_root="./locales")

# 基本翻译
print(tx.tr("Hello"))  # 输出：你好

# 带参数的翻译
print(tx.tr("Hello {name}!", name="张三"))  # 输出：你好 张三！

# 基于上下文的翻译
print(tx.tr("Open", context="button"))  # 输出：打开
print(tx.tr("Open", context="menu"))    # 输出：打开文件

# 运行时切换语言
tx.switch_locale("ja_JP")
print(tx.tr("Hello"))  # 输出：こんにちは
```

### 🔄 翻译 API

TransX 提供两种主要的翻译方法，具有不同级别的功能：

#### tr() - 高级翻译 API

`tr()` 方法是推荐的高级 API，提供所有翻译功能：

```python
# 基本翻译
tx.tr("Hello")  # 你好

# 带参数的翻译
tx.tr("Hello {name}!", name="张三")  # 你好 张三！

# 基于上下文的翻译
tx.tr("Open", context="button")  # 打开
tx.tr("Open", context="menu")    # 打开文件

# 环境变量展开
tx.tr("Home: $HOME")  # Home: /Users/username

# 美元符号转义
tx.tr("Price: $$99.99")  # Price: $99.99

# 复杂参数替换
tx.tr("Welcome to ${city}, {country}!", city="北京", country="中国")
```

#### translate() - 低级翻译 API

`translate()` 方法是一个低级 API，提供基本的翻译和参数替换：

```python
# 基本翻译
tx.translate("Hello")  # 你好

# 基于上下文的翻译
tx.translate("Open", context="button")  # 打开

# 简单参数替换
tx.translate("Hello {name}!", name="张三")  # 你好 张三！
```

`tr()` 和 `translate()` 的主要区别：

| 特性 | tr() | translate() |
|---------|------|------------|
| 基本翻译 | ✅ | ✅ |
| 上下文支持 | ✅ | ✅ |
| 参数替换 | ✅ | ✅ |
| 环境变量展开 | ✅ | ❌ |
| ${var} 风格变量 | ✅ | ❌ |
| 美元符号转义 | ✅ | ❌ |
| 解释器链 | ✅ | ❌ |

选择 `tr()` 获取完整功能，或选择 `translate()` 用于仅需基本翻译和参数替换的简单场景。

### 🔄 高级参数替换

```python
# 命名参数
tx.tr("Welcome to {city}, {country}!", city="北京", country="中国")

# 位置参数
tx.tr("File {0} of {1}", 1, 10)

# 美元符号变量（在 shell-like 环境中有用）
tx.tr("Current user: ${USER}")  # 支持 ${var} 语法
tx.tr("Path: $HOME/documents")  # 支持 $var 语法

# 美元符号转义
tx.tr("Price: $$99.99")  # 输出：Price: $99.99
```

## 🌐 可用语言环境

TransX 提供了一个便捷的方式来获取项目中可用的语言环境列表：

```python
from transx import TransX

tx = TransX(locales_root="./locales")

# 获取可用语言环境列表
print(f"可用语言环境：{tx.available_locales}")  # 例如：['en_US', 'zh_CN', 'ja_JP']

# 检查语言环境是否可用
if "zh_CN" in tx.available_locales:
    tx.current_locale = "zh_CN"

# 检查当前语言环境
print(f"当前语言环境：{tx.current_locale}")  # 当前语言环境：zh_CN

# 获取语言环境信息
print(f"语言环境信息：{tx.locale_info}")  # 显示详细语言环境信息
```

## 🎯 语言代码支持

TransX 提供灵活的语言代码处理，支持自动规范化。该库支持多种格式的语言代码，使其在不同场景下易于使用：

```python
from transx import TransX

tx = TransX()

# 所有这些格式都是有效的，并且会自动规范化：
tx.current_locale = "zh-CN"    # 连字符格式
tx.current_locale = "zh_CN"    # 下划线格式
tx.current_locale = "zh"       # 仅语言代码
tx.current_locale = "Chinese"  # 语言名称
```

支持的语言代码示例：

| 语言 | 标准代码 | 替代格式 |
|----------|--------------|-------------------|
| 简体中文 | `zh_CN` | `zh-CN`, `zh_Hans`, `Chinese`, `Chinese Simplified` |
| 日语 | `ja_JP` | `ja`, `Japanese` |
| 韩语 | `ko_KR` | `ko`, `Korean` |
| 英语 | `en_US` | `en`, `English` |
| 法语 | `fr_FR` | `fr`, `French` |
| 西班牙语 | `es_ES` | `es`, `Spanish` |
| 德语 | `de_DE` | `de`, `German` |
| 意大利语 | `it_IT` | `it`, `Italian` |
| 俄语 | `ru_RU` | `ru`, `Russian` |

## 🛠️ 命令行界面

TransX 提供了命令行界面来处理常见的翻译任务。当没有提供命令参数时，TransX 将使用当前工作目录下的 `./locales` 作为默认路径。

```bash
# 从源文件提取消息
# 默认：将在当前目录中查找源文件并输出到 ./locales
transx extract

# 等同于：
transx extract . --output ./locales/messages.pot

# 更新 .po 文件的新翻译
# 默认：将更新 ./locales 中的 .po 文件
transx update

# 等同于：
transx update ./locales

# 将 .po 文件编译为 .mo 文件
# 默认：将编译 ./locales 中的 .po 文件
transx compile

# 等同于：
transx compile ./locales
```

默认的工作目录结构：
```
./
└── locales/           # 默认翻译目录
    ├── messages.pot   # 提取的消息模板
    ├── en/           # 英语翻译
    │   └── LC_MESSAGES/
    │       ├── messages.po
    │       └── messages.mo
    └── zh_CN/        # 中文翻译
        └── LC_MESSAGES/
            ├── messages.po
            └── messages.mo
```

### 提取消息
```bash
# 从单个文件提取
transx extract app.py -o messages.pot

# 从目录提取并包含项目信息
transx extract ./src -o messages.pot -p "MyProject" -v "1.0"

# 提取并指定语言
transx extract ./src -l "en_US,zh_CN,ja_JP"
```

### 更新 PO 文件
```bash
# 为特定语言更新或创建 PO 文件
transx update messages.pot -l "zh_CN,ja_JP,ko_KR"

# 自动发现并更新所有语言文件
transx update messages.pot

# 使用自定义输出目录更新
transx update messages.pot -o ./locales
```

### 编译 MO 文件
```bash
# 编译单个 PO 文件
transx compile path/to/messages.po

# 编译目录中的所有 PO 文件
transx compile -d ./locales

# 编译多个指定文件
transx compile file1.po file2.po
```

### 列出可用语言环境
```bash
# 列出默认目录中的所有可用语言环境
transx list

# 列出特定目录中的语言环境
transx list -d /path/to/locales
```

### 常用选项
- `-d, --directory`: 指定工作目录
- `-o, --output`: 指定输出文件/目录
- `-l, --languages`: 以逗号分隔的语言代码列表
- `-p, --project`: 项目名称（用于 POT 生成）
- `-v, --version`: 项目版本（用于 POT 生成）

获取任何命令的详细帮助：
```bash
transx <command> --help
```

## 🚀 高级特性

### 🖥️ Qt 使用

TransX 支持以下两种方式与 Qt 应用程序集成：

#### 基础集成方式

在 Qt 应用程序中直接使用 TransX：

```python
from PySide2.QtWidgets import QMainWindow
from transx import get_transx_instance

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tx = get_transx_instance("myapp")

        # 翻译窗口标题
        self.setWindowTitle(self.tx.tr("My Application"))

        # 翻译菜单项
        file_menu = self.menuBar().addMenu(self.tx.tr("&File"))
        file_menu.addAction(self.tx.tr("&Open"))
        file_menu.addAction(self.tx.tr("&Save"))
```

#### Qt 翻译器集成方式

如需使用 Qt 的内置翻译系统，需要执行以下步骤：
1. 使用 Qt 的 lrelease 工具将 .po 文件转换为 .qm 格式
2. 通过 TransX 的 Qt 扩展加载 .qm 文件

```python
from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import QTranslator
from transx.extensions.qt import install_qt_translator

app = QApplication([])
translator = QTranslator()

# 安装特定语言的翻译器
# 请确保 ./translations 目录中存在 qt_zh_CN.qm 文件
install_qt_translator(app, translator, "zh_CN", "./translations")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 注意：Qt 的 tr() 函数仅支持 .qm 文件
        # 对于 Python 字符串，需使用 TransX 的 tr() 函数
        self.setWindowTitle("My Application")  # 此处不会被翻译
```

转换 .po 文件为 .qm 文件：
```bash
# 使用 Qt 的 lrelease 工具
lrelease translations/zh_CN/LC_MESSAGES/messages.po -qm translations/qt_zh_CN.qm
```

> 注意：`lrelease` 工具是 Qt Linguist 工具集的组成部分：
> - Windows：通过 [qt.io](https://www.qt.io/download) 下载 Qt 安装程序（在工具栏中查找 Qt Linguist）
> - Linux：通过包管理器安装
>   ```bash
>   # Ubuntu/Debian 系统
>   sudo apt-get install qttools5-dev-tools
>
>   # Fedora 系统
>   sudo dnf install qt5-linguist
>
>   # Arch Linux 系统
>   sudo pacman -S qt5-tools
>   ```
> - macOS：通过 Homebrew 安装
>   ```bash
>   brew install qt5
>   ```

Qt 集成功能：
- 支持加载 .qm 格式的翻译文件
- 支持多个翻译器实例
- 注意：Qt 的 tr() 函数仅支持 .qm 文件，无法直接使用 .mo 文件

### 🔍 消息提取

从源代码中提取可翻译的消息，支持强大的上下文功能：

```python
from transx.api.pot import PotExtractor

# 初始化提取器并指定输出文件
extractor = PotExtractor(pot_file="messages.pot")

# 添加要扫描的源文件或目录
extractor.add_source_file("app.py")
extractor.add_source_file("utils.py")
# 或扫描整个目录
extractor.add_source_directory("src")

# 提取消息并包含项目信息
extractor.save_pot(
    project="MyApp",
    version="1.0.0",
    copyright_holder="Your Name",
    bugs_address="your.email@example.com"
)
```

### 🌐 多应用支持

管理多个应用程序的翻译实例：

```python
from transx import get_transx_instance

# 为不同应用创建翻译实例
app1 = get_transx_instance("app1", default_locale="en_US")
app2 = get_transx_instance("app2", default_locale="zh_CN")

# 每个实例独立维护：
# - 翻译目录
# - 语言设置
# - 消息域
app1.tr("Hello")  # 使用 app1 的翻译
app2.tr("Hello")  # 使用 app2 的翻译

# 独立切换语言环境
app1.switch_locale("ja_JP")
app2.switch_locale("ko_KR")
```

多应用支持特性：
- 独立的翻译目录管理
- 实例级别的语言环境设置
- 线程安全的操作机制

### 🔤 上下文翻译

```python
# UI 上下文
print(tx.tr("Open", context="button"))  # 打开
print(tx.tr("Open", context="menu"))    # 打开文件

# 词性上下文
print(tx.tr("Post", context="verb"))    # 发布
print(tx.tr("Post", context="noun"))    # 文章

# 场景上下文
print(tx.tr("Welcome", context="login")) # 欢迎登录
print(tx.tr("Welcome", context="home"))  # 欢迎回来
```

### ⚠️ 错误处理

TransX 提供全面的错误处理和回退机制：

```python
from transx import TransX
from transx.exceptions import LocaleNotFoundError, TranslationError

# 为开发环境启用严格模式
tx = TransX(strict_mode=True)

try:
    tx.load_catalog("invalid_locale")
except LocaleNotFoundError as e:
    print(f"❌ 语言环境错误：{e.message}")

try:
    result = tx.translate("Hello", target_lang="invalid")
except TranslationError as e:
    print(f"❌ 翻译失败：{e.message}")
```

## 🛠️ 开发

### 🔧 环境配置

1. 克隆仓库：
```bash
git clone https://github.com/loonghao/transx.git
cd transx
```

2. 安装开发依赖：
```bash
pip install -r requirements-dev.txt
```

### 📦 项目结构

TransX 遵循良好组织的包结构：

```
transx/
├── transx/                  # 主包目录
│   ├── __init__.py         # 包初始化
│   ├── __version__.py      # 版本信息
│   ├── api/                # 公共 API 模块
│   │   ├── __init__.py
│   │   ├── mo.py          # MO 文件操作
│   │   ├── po.py          # PO 文件操作
│   │   └── pot.py         # POT 文件操作
│   ├── app.py             # 应用程序管理
│   ├── cli.py             # 命令行界面
│   ├── constants.py        # 常量和配置
│   ├── context/           # 翻译上下文管理
│   │   ├── __init__.py
│   │   └── manager.py    # 上下文管理器实现
│   ├── core.py            # 核心功能
│   ├── exceptions.py       # 自定义异常
│   ├── extensions/        # 框架集成
│   │   ├── __init__.py
│   │   └── qt.py         # Qt 支持
│   └── internal/          # 内部实现细节
│       ├── __init__.py
│       ├── compat.py     # Python 2/3 兼容性
│       ├── filesystem.py # 文件系统操作
│       └── logging.py    # 日志工具
├── examples/              # 示例代码
├── locales/              # 翻译文件
├── tests/                # 测试套件
├── nox_actions/          # Nox 自动化脚本
├── CHANGELOG.md          # 版本历史
├── LICENSE              # MIT 许可证
├── README.md            # 英文文档
├── README_zh.md         # 中文文档
├── noxfile.py           # 测试自动化配置
├── pyproject.toml       # 项目配置
├── requirements.txt     # 生产依赖
└── requirements-dev.txt # 开发依赖
```

### 🔄 开发工作流

我们使用 [Nox](https://nox.thea.codes/) 来自动化开发任务。以下是主要命令：

```bash
# 运行代码检查
nox -s lint

# 自动修复代码检查问题
nox -s lint-fix

# 运行测试
nox -s pytest
```

### 🧪 运行测试

测试使用 pytest 编写，可以通过 nox 运行：

```bash
nox -s pytest
```

运行特定测试：

```bash
# 运行指定测试文件
nox -s pytest -- tests/test_core.py

# 使用特定标记运行测试
nox -s pytest -- -m "not integration"
```

### 🔍 代码质量

我们使用多种工具来保持高代码质量标准：

- **代码检查**: 使用 ruff 和 isort 进行代码检查和格式化
- **类型检查**: 使用 mypy 进行静态类型检查
- **测试**: 使用 pytest 进行全面的测试
- **覆盖率**: 使用 coverage.py 跟踪代码覆盖率
- **CI/CD**: 使用 GitHub Actions 进行自动化测试和部署

### 📝 文档

文档采用 Markdown 格式编写，包括：
- README.md：主要文档
- examples/：示例代码和使用说明
- 源代码中的 API 文档

### 🤝 贡献指南

1. Fork 本仓库
2. 为您的功能创建新分支
3. 进行修改
4. 运行测试和代码检查
5. 提交 Pull Request

请确保您的 PR：
- 通过所有测试
- 包含适当的文档
- 遵循我们的代码风格
- 为新功能提供测试覆盖

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 性能

TransX 在设计时就非常注重性能。我们通过自动化基准测试持续监控和优化其性能。

查看我们的性能基准测试：[TransX 性能测试](https://loonghao.github.io/transx-benchmarks/)

我们的基准测试套件包括：
- 翻译查找性能
- 参数替换性能
- 语言切换性能
- 缓存效率
- 内存使用
- 并发操作
- 以及更多...
