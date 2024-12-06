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

</div>

---

## ✨ Features

TransX 提供了全面的国际化功能：

- 🚀 **Zero Dependencies**: 无需任何外部依赖
- 🐍 **Python Support**: 完全支持 Python 2.7-3.12
- 🌍 **Context-based**: 基于上下文的精确翻译
- 📦 **Standard Format**: 兼容 gettext .po/.mo 文件
- 🎯 **Simple API**: 清晰直观的接口
- 🔄 **Auto Management**: 自动处理翻译文件
- 🔍 **String Extraction**: 内置源代码字符串提取
- 🌐 **Unicode**: 完整的 Unicode 支持
- 🔠 **Parameters**: 支持命名、位置和 ${var} 风格的参数
- 💫 **Variable Support**: 支持环境变量展开
- ⚡ **Performance**: 高速且线程安全的操作
- 🛡️ **Error Handling**: 全面的错误管理和回退机制
- 🧪 **Testing**: 100% 测试覆盖率
- 🌐 **Auto Translation**: 内置 Google 翻译 API 支持
- 🎥 **DCC Support**: 已在 Maya、3DsMax、Houdini 等软件中测试
- 🔌 **Extensible**: 可插拔的自定义文本解释器系统
- 🎨 **Flexible Formatting**: 支持多种字符串格式化风格
- 🔄 **Runtime Switching**: 支持运行时动态切换语言
- 📦 **GNU gettext**: 完全兼容 GNU gettext 标准和工具

## GNU gettext Compatibility

TransX 完全兼容 GNU gettext 标准，可与现有翻译工作流无缝集成：

- **Standard Formats**: 完全支持 `.po` 和 `.mo` 文件格式
- **File Structure**: 遵循标准的语言目录结构 (`LC_MESSAGES/domain.{po,mo}`)
- **Header Support**: 完整支持 gettext 头部和元数据
- **Plural Forms**: 兼容 gettext 复数形式表达式和处理
- **Context Support**: 使用 gettext 标准分隔符完全支持 msgctxt（消息上下文）
- **Encoding**: 按照 PO/MO 头部规范正确处理字符编码
- **Tools Integration**: 可与标准 gettext 工具（msgfmt、msginit、msgmerge 等）配合使用
- **Binary Format**: 实现官方 MO 文件格式规范，支持大小端序

这意味着您可以：
- Use existing PO editors like Poedit, Lokalize, or GTranslator
- Integrate with established translation workflows
- Migrate existing gettext-based translations seamlessly
- Use standard gettext tools alongside TransX
- Maintain compatibility with other gettext-based systems

## 🚀 Quick Start

### 📥 Installation

```bash
pip install transx
```

### 📝 Basic Usage

```python
from transx import TransX

# Initialize with locale directory
tx = TransX(locales_root="./locales")

# Basic translation
print(tx.tr("Hello"))  # Output: 你好

# Translation with parameters
print(tx.tr("Hello {name}!", name="张三"))  # Output: 你好 张三！

# Context-based translation
print(tx.tr("Open", context="button"))  # 打开
print(tx.tr("Open", context="menu"))    # 打开文件

# Switch language at runtime
tx.switch_locale("ja_JP")
print(tx.tr("Hello"))  # Output: こんにちは
```

### 🔄 Translation API

TransX 提供两种主要的翻译方法，具有不同级别的功能：


#### tr() - High-Level Translation API

`tr()` 方法是推荐的高级 API，提供所有翻译功能：


```python
# Basic translation
tx.tr("Hello")  # 你好

# Translation with parameters
tx.tr("Hello {name}!", name="张三")  # 你好 张三！

# Context-based translation
tx.tr("Open", context="button")  # 打开
tx.tr("Open", context="menu")    # 打开文件

# Environment variable expansion
tx.tr("Home: $HOME")  # Home: /Users/username

# Dollar sign escaping
tx.tr("Price: $$99.99")  # Price: $99.99

# Complex parameter substitution
tx.tr("Welcome to ${city}, {country}!", city="北京", country="中国")
```


#### translate() - Low-Level Translation API

`translate()` 方法是一个低级 API，提供基本的翻译和参数替换：


```python
# Basic translation
tx.translate("Hello")  # 你好

# Translation with context
tx.translate("Open", context="button")  # 打开

# Simple parameter substitution
tx.translate("Hello {name}!", name="张三")  # 你好 张三！
```


`tr()` 和 `translate()` 的主要区别：


| Feature | tr() | translate() |
|---------|------|------------|
| Basic Translation | ✅ | ✅ |
| Context Support | ✅ | ✅ |
| Parameter Substitution | ✅ | ✅ |
| Environment Variables | ✅ | ❌ |
| ${var} Style Variables | ✅ | ❌ |
| $$ Escaping | ✅ | ❌ |
| Interpreter Chain | ✅ | ❌ |


选择 `tr()` 获取完整功能，或选择 `translate()` 用于仅需基本翻译和参数替换的简单场景。


### 🔄 Advanced Parameter Substitution


```python
# Named parameters
tx.tr("Welcome to {city}, {country}!", city="北京", country="中国")

# Positional parameters
tx.tr("File {0} of {1}", 1, 10)

# Dollar sign variables (useful in shell-like contexts)
tx.tr("Current user: ${USER}")  # Supports ${var} syntax
tx.tr("Path: $HOME/documents")  # Supports $var syntax

# Escaping dollar signs
tx.tr("Price: $$99.99")  # Outputs: Price: $99.99
```

## 🌐 Available Locales

TransX 提供了一个便捷的方式来获取项目中可用的语言环境列表：


```python
from transx import TransX

tx = TransX(locales_root="./locales")

# Get list of available locales
print(f"Available locales: {tx.available_locales}")  # e.g. ['en_US', 'zh_CN', 'ja_JP']

# Check if a locale is available before switching
if "zh_CN" in tx.available_locales:
    tx.current_locale = "zh_CN"

# Check current locale
print(f"Current locale: {tx.current_locale}")  # Current locale: zh_CN

# Get locale info
print(f"Locale info: {tx.locale_info}")  # Displays detailed locale information
```

## 🎯 Language Code Support

TransX 提供灵活的语言代码处理，支持自动规范化。该库支持多种格式的语言代码，使其在不同场景下易于使用：

```python
from transx import TransX

tx = TransX()

# All these formats are valid and normalized automatically:
tx.current_locale = "zh-CN"    # Hyphen format
tx.current_locale = "zh_CN"    # Underscore format
tx.current_locale = "zh"       # Language only
tx.current_locale = "Chinese"  # Language name
```

支持的语言代码示例：

| Language | Standard Code | Alternative Formats |
|----------|--------------|-------------------|
| Chinese (Simplified) | `zh_CN` | `zh-CN`, `zh_Hans`, `Chinese`, `Chinese Simplified` |
| Japanese | `ja_JP` | `ja`, `Japanese` |
| Korean | `ko_KR` | `ko`, `Korean` |
| English | `en_US` | `en`, `English` |
| French | `fr_FR` | `fr`, `French` |
| Spanish | `es_ES` | `es`, `Spanish` |
| German | `de_DE` | `de`, `German` |
| Italian | `it_IT` | `it`, `Italian` |
| Russian | `ru_RU` | `ru`, `Russian` |

## 📁 Project Structure

```
transx/
├── transx/
│   ├── __init__.py
│   ├── core.py          # Core functionality
│   ├── api/             # Public API
│   │   ├── __init__.py
│   │   ├── mo.py       # MO file handling
│   │   └── locale.py   # Locale management
│   └── utils/          # Utility functions
├── tests/              # Test suite
├── examples/           # Example code
├── docs/              # Documentation
└── README.md          # This file
```

## 🔧 Development

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/transx.git
cd transx

# Create and activate virtual environment (optional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

使用 nox 运行测试：

```bash
# Run all tests
nox -s pytest

# Run specific test file
nox -s pytest -- tests/test_core.py

# Run with coverage
nox -s pytest -- --cov=transx

# Fix linting issues automatically
nox -s lint-fix

# Run tests
nox -s pytest
```

### 🧪 Running Tests

使用 pytest 编写测试，可以通过 nox 运行：

```bash
nox -s pytest
```

运行特定测试：

```bash
# Run a specific test file
nox -s pytest -- tests/test_core.py

# Run tests with specific markers
nox -s pytest -- -m "not integration"
```

### 🔍 Code Quality

我们使用多种工具维护高代码质量标准：

- **Linting**: 使用 ruff 和 isort 进行代码检查和格式化
- **Type Checking**: 使用 mypy 进行静态类型检查
- **Testing**: 使用 pytest 的综合测试套件
- **Coverage**: 使用 coverage.py 跟踪代码覆盖率
- **CI/CD**: 使用 GitHub Actions 进行自动化测试和部署

### 📝 Documentation

文档使用 Markdown 编写，可在以下位置找到：
- README.md: 主要文档
- examples/: 示例代码和用法
- API documentation in source code

### 🤝 Contributing Guidelines

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests and linting
5. Submit a pull request

请确保您的 PR：
- Passes all tests
- Includes appropriate documentation
- Follows our code style
- Includes test coverage for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
