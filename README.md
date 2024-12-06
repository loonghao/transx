# 🌏 TransX

English | [简体中文](README_zh.md)

🚀 A lightweight, zero-dependency Python internationalization library that supports Python 2.7 through 3.12.

The API is designed to be [DCC](https://en.wikipedia.org/wiki/Digital_content_creation)-friendly, for example, works with [Maya](https://www.autodesk.com/products/maya/overview), [3DsMax](https://www.autodesk.com/products/3ds-max/overview), [Houdini](https://www.sidefx.com/products/houdini/), etc.


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

TransX provides a comprehensive set of features for internationalization:

- 🚀 **Zero Dependencies**: No external dependencies required
- 🐍 **Python Support**: Full support for Python 2.7-3.12
- 🌍 **Context-based**: Accurate translations with context support
- 📦 **Standard Format**: Compatible with gettext .po/.mo files
- 🎯 **Simple API**: Clean and intuitive interface
- 🔄 **Auto Management**: Automatic translation file handling
- 🔍 **String Extraction**: Built-in source code string extraction
- 🌐 **Unicode**: Complete Unicode support
- 🔠 **Parameters**: Named, positional and ${var} style parameters
- 💫 **Variable Support**: Environment variable expansion support
- ⚡ **Performance**: High-speed and thread-safe operations
- 🛡️ **Error Handling**: Comprehensive error management with fallbacks
- 🧪 **Testing**: 100% test coverage with extensive cases
- 🌐 **Auto Translation**: Built-in Google Translate API support
- 🎥 **DCC Support**: Tested with Maya, 3DsMax, Houdini, etc.
- 🔌 **Extensible**: Pluggable custom text interpreters system
- 🎨 **Flexible Formatting**: Support for various string format styles
- 🔄 **Runtime Switching**: Dynamic locale switching at runtime
- 📦 **GNU gettext**: Full compatibility with GNU gettext standard and tools

## GNU gettext Compatibility

TransX is fully compatible with the GNU gettext standard, providing seamless integration with existing translation workflows:

- **Standard Formats**: Full support for `.po` and `.mo` file formats according to GNU gettext specifications
- **File Structure**: Follows the standard locale directory structure (`LC_MESSAGES/domain.{po,mo}`)
- **Header Support**: Complete support for gettext headers and metadata
- **Plural Forms**: Compatible with gettext plural form expressions and handling
- **Context Support**: Full support for msgctxt (message context) using gettext standard separators
- **Encoding**: Proper handling of character encodings as specified in PO/MO headers
- **Tools Integration**: Works with standard gettext tools (msgfmt, msginit, msgmerge, etc.)
- **Binary Format**: Implements the official MO file format specification with both little and big endian support

This means you can:
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

TransX provides two main methods for translation with different levels of functionality:


#### tr() - High-Level Translation API

The `tr()` method is the recommended high-level API that provides all translation features:


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

The `translate()` method is a lower-level API that provides basic translation and parameter substitution:


```python
# Basic translation
tx.translate("Hello")  # 你好

# Translation with context
tx.translate("Open", context="button")  # 打开

# Simple parameter substitution
tx.translate("Hello {name}!", name="张三")  # 你好 张三！
```


The main differences between `tr()` and `translate()`:


| Feature | tr() | translate() |
|---------|------|------------|
| Basic Translation | ✅ | ✅ |
| Context Support | ✅ | ✅ |
| Parameter Substitution | ✅ | ✅ |
| Environment Variables | ✅ | ❌ |
| ${var} Style Variables | ✅ | ❌ |
| $$ Escaping | ✅ | ❌ |
| Interpreter Chain | ✅ | ❌ |


Choose `tr()` for full functionality or `translate()` for simpler use cases where you only need basic translation and parameter substitution.


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

TransX provides a convenient way to get a list of available locales in your project:


```python
from transx import TransX

tx = TransX(locales_root="./locales")

# Get list of available locales
print(f"Available locales: {tx.available_locales}")  # e.g. ['en_US', 'zh_CN', 'ja_JP']

# Check if a locale is available before switching
if "zh_CN" in tx.available_locales:
    tx.current_locale = "zh_CN"
```


The `available_locales` property returns a sorted list of locale codes that:
- Have a valid locale directory structure (`LC_MESSAGES` folder)
- Contain either `.po` or `.mo` translation files
- Are ready to use for translation


This is useful for:
- Building language selection interfaces
- Validating locale switches
- Checking translation file completeness
- Displaying supported languages to users


## 🛠️ Command Line Interface

TransX provides a powerful CLI for translation management:


### Extract Messages
```bash
# Extract from a single file
transx extract app.py -o messages.pot

# Extract from a directory with project info
transx extract ./src -o messages.pot -p "MyProject" -v "1.0"

# Extract and specify languages
transx extract ./src -l "en_US,zh_CN,ja_JP"
```


### Update PO Files
```bash
# Update or create PO files for specific languages
transx update messages.pot -l "zh_CN,ja_JP,ko_KR"

# Auto-discover and update all language files
transx update messages.pot

# Update with custom output directory
transx update messages.pot -o ./locales
```


### Compile MO Files
```bash
# Compile a single PO file
transx compile path/to/messages.po

# Compile all PO files in a directory
transx compile -d ./locales

# Compile multiple specific files
transx compile file1.po file2.po
```


### List Available Locales
```bash
# List all available locales in default directory
transx list

# List locales in a specific directory
transx list -d /path/to/locales
```


### Common Options
- `-d, --directory`: Specify working directory
- `-o, --output`: Specify output file/directory
- `-l, --languages`: Comma-separated list of language codes
- `-p, --project`: Project name (for POT generation)
- `-v, --version`: Project version (for POT generation)


For detailed help on any command:
```bash
transx <command> --help
```


## 🎯 Advanced Features

### Context-Based Translations


```python
# UI Context
print(tx.tr("Open", context="button"))  # 打开
print(tx.tr("Open", context="menu"))    # 打开文件

# Part of Speech
print(tx.tr("Post", context="verb"))    # 发布
print(tx.tr("Post", context="noun"))    # 文章

# Scene Context
print(tx.tr("Welcome", context="login")) # 欢迎登录
print(tx.tr("Welcome", context="home"))  # 欢迎回来
```


### Error Handling

TransX provides comprehensive error handling with fallback mechanisms:


```python
from transx import TransX
from transx.exceptions import LocaleNotFoundError, TranslationError

# Enable strict mode for development
tx = TransX(strict_mode=True)

try:
    tx.load_catalog("invalid_locale")
except LocaleNotFoundError as e:
    print(f"❌ Locale error: {e.message}")

try:
    result = tx.translate("Hello", target_lang="invalid")
except TranslationError as e:
    print(f"❌ Translation failed: {e.message}")
```


## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


### 📁 Project Structure


```bash
transx/
├── transx/                 # Main package directory
│   ├── api/               # Public API modules
│   │   ├── locale.py      # Locale handling
│   │   ├── mo.py         # MO file operations
│   │   ├── po.py         # PO file operations
│   │   └── translate.py   # Translation services
│   ├── core.py           # Core functionality
│   ├── cli.py            # Command-line interface
│   ├── constants.py       # Constants and configurations
│   └── exceptions.py      # Custom exceptions
├── tests/                 # Test directory
├── examples/              # Example code and usage
├── nox_actions/          # Nox automation scripts
├── docs/                 # Documentation
├── pyproject.toml        # Project configuration
└── noxfile.py           # Test automation configuration
```


## ⚡ Performance Features

- 🚀 Uses compiled MO files for optimal speed
- 💾 Automatic translation caching
- 🔒 Thread-safe for concurrent access
- 📉 Minimal memory footprint
- 🔄 Automatic PO to MO compilation


### 🔧 Development Setup

1. Clone the repository:
```bash
git clone https://github.com/loonghao/transx.git
cd transx
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```


### 🔄 Development Workflow

We use [Nox](https://nox.thea.codes/) to automate development tasks. Here are the main commands:


```bash
# Run linting
nox -s lint

# Fix linting issues automatically
nox -s lint-fix

# Run tests
nox -s pytest
```


### 🧪 Running Tests

Tests are written using pytest and can be run using nox:


```bash
nox -s pytest
```


For running specific tests:


```bash
# Run a specific test file
nox -s pytest -- tests/test_core.py

# Run tests with specific markers
nox -s pytest -- -m "not integration"
```


### 🔍 Code Quality

We maintain high code quality standards using various tools:


- **Linting**: We use ruff and isort for code linting and formatting
- **Type Checking**: Static type checking with mypy
- **Testing**: Comprehensive test suite with pytest
- **Coverage**: Code coverage tracking with coverage.py
- **CI/CD**: Automated testing and deployment with GitHub Actions


### 📝 Documentation

Documentation is written in Markdown and is available in:
- README.md: Main documentation
- examples/: Example code and usage
- API documentation in source code


### 🤝 Contributing Guidelines

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests and linting
5. Submit a pull request


Please ensure your PR:
- Passes all tests
- Includes appropriate documentation
- Follows our code style
- Includes test coverage for new features


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
