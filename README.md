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
![Codecov](https://img.shields.io/codecov/c/github/loonghao/transx)
[![Benchmarks](https://img.shields.io/badge/benchmarks-view%20performance-blue)](https://loonghao.github.io/transx-benchmarks/)
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
- 🔌 **Extensible**: Pluggable custom text interpreters
- 🎨 **Flexible Formatting**: Multiple string formatting styles
- 🔄 **Runtime Switching**: Dynamic locale switching at runtime
- 🔧 **Qt Integration**: Built-in support for Qt translations
- 📝 **Message Extraction**: Advanced source code message extraction with context
- 🌐 **Multi-App Support**: Multiple translation instances for different apps

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

### 🌳 Multiple Locale Roots

`TransX` now supports loading translations from multiple locale roots.

```python
from transx import TransX

# First root has higher priority on duplicate keys (first-wins)
tx = TransX(
    locales_root=[
        "./package_a/locales",
        "./package_b/locales",
    ],
    default_locale="zh_CN",
)

print(tx.locales_root)   # backward-compatible: first root
print(tx.locales_roots)  # full root list
print(tx.available_locales)

print(tx.tr("Hello"))
print(tx.tr("Export"))
```

See `examples/multiple_locale_roots.py` for a full runnable demo.

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

#### Custom marker with `tr()` parity

If your project uses a custom marker (for example `trm`) and you want exactly the same runtime behavior as `tr()`, alias it directly to `tx.tr`:

```python
trm = tx.tr
trm("Open", context="menu")
trm("Hello {name}", name="Alice")
trm("Path: $HOME")
```

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

TransX provides a command-line interface for common translation tasks. When no arguments are provided for commands, TransX will use the `./locales` directory in your current working directory as the default path.

```bash
# Extract messages from source files
# Default: Will look for source files in current directory and output to ./locales
transx extract

# Same as:
transx extract . --output ./locales/messages.pot

# Update .po files with new translations
# Default: Will update .po files in ./locales
transx update

# Same as:
transx update ./locales

# Compile .po files to .mo files
# Default: Will compile .po files from ./locales
transx compile

# Same as:
transx compile ./locales
```

The default working directory structure:
```
./
└── locales/           # Default translation directory
    ├── messages.pot   # Extracted messages template
    ├── en/           # English translations
    │   └── LC_MESSAGES/
    │       ├── messages.po
    │       └── messages.mo
    └── zh_CN/        # Chinese translations
        └── LC_MESSAGES/
            ├── messages.po
            └── messages.mo
```

### Extract Messages
```bash
# Extract from a single file
transx extract app.py -o messages.pot

# Extract from a directory with project info
transx extract ./src -o messages.pot -p "MyProject" -v "1.0"

# Extract and specify languages
transx extract ./src -l "en_US,zh_CN,ja_JP"

# Extract with additional custom methods
transx extract ./src -o messages.pot --methods trm lazy_gettext
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


## 🚀 Advanced Features

### 🖥️ Qt Usage

TransX can be used with Qt applications in two ways:

#### Basic Integration

Use TransX directly in your Qt application:

```python
from PySide2.QtWidgets import QMainWindow
from transx import get_transx_instance

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tx = get_transx_instance("myapp")

        # Translate window title
        self.setWindowTitle(self.tx.tr("My Application"))

        # Translate menu items
        file_menu = self.menuBar().addMenu(self.tx.tr("&File"))
        file_menu.addAction(self.tx.tr("&Open"))
        file_menu.addAction(self.tx.tr("&Save"))
```

#### Qt Translator Integration

For Qt's built-in translation system, you'll need to:
1. First convert your .po files to .qm format using Qt's lrelease tool
2. Install the .qm files using TransX's Qt extension

```python
from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import QTranslator
from transx.extensions.qt import install_qt_translator

app = QApplication([])
translator = QTranslator()

# Install translator for specific locale
# Make sure qt_zh_CN.qm exists in ./translations directory
install_qt_translator(app, translator, "zh_CN", "./translations")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Note: Qt's tr() will only work with .qm files
        # For Python strings, use TransX's tr() function
        self.setWindowTitle("My Application")  # This won't be translated
```

Converting .po to .qm files:
```bash
# Using Qt's lrelease tool
lrelease translations/zh_CN/LC_MESSAGES/messages.po -qm translations/qt_zh_CN.qm
```

> Note: The `lrelease` tool is part of Qt's Linguist tools:
> - Windows: Install with Qt installer from [qt.io](https://www.qt.io/download) (Look for Qt Linguist under Tools)
> - Linux: Install via package manager
>   ```bash
>   # Ubuntu/Debian
>   sudo apt-get install qttools5-dev-tools
>
>   # Fedora
>   sudo dnf install qt5-linguist
>
>   # Arch Linux
>   sudo pacman -S qt5-tools
>   ```
> - macOS: Install via Homebrew
>   ```bash
>   brew install qt5
>   ```

The Qt integration supports:
- Loading .qm format translation files
- Multiple translator instances
- Note: Qt's built-in tr() function requires .qm files and won't work with .mo files

### 🔍 Message Extraction

Extract translatable messages from your source code with powerful context support:

```python
from transx.api.pot import PotExtractor

# Initialize extractor with output file
extractor = PotExtractor(
    pot_file="messages.pot",
    additional_keywords=["trm", "lazy_gettext"]
)

# Note:
# - list/tuple/set keywords are treated as tr()-like markers
#   (supports msgid + context=... extraction)
# - dict keywords let you define explicit gettext-style specs
#   e.g. {"my_pgettext": ((1, "c"), 2)}



# Add source files or directories to scan
extractor.add_source_file("app.py")
extractor.add_source_file("utils.py")
# Or scan entire directories
extractor.add_source_directory("src")

# Extract messages with project info
extractor.save_pot(
    project="MyApp",
    version="1.0.0",
    copyright_holder="Your Name",
    bugs_address="your.email@example.com"
)
```

### 🌐 Multi-App Support

Manage multiple translation instances for different applications or components:

```python
from transx import get_transx_instance

# Create instances for different apps or components
app1 = get_transx_instance("app1", default_locale="en_US")
app2 = get_transx_instance("app2", default_locale="zh_CN")

# Each instance has its own:
# - Translation catalog
# - Locale settings
# - Message domains
app1.tr("Hello")  # Uses app1's translations
app2.tr("Hello")  # Uses app2's translations

# Switch locales independently
app1.switch_locale("ja_JP")
app2.switch_locale("ko_KR")
```

Multi-app support features:
- Independent translation catalogs
- Separate locale settings per instance
- Thread-safe operation

### 🔤 Context-Based Translations

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

### ⚠️ Error Handling

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

## 📄 Performance

TransX is designed with performance in mind. We continuously monitor and optimize its performance through automated benchmarks.

View our performance benchmarks at: [TransX Benchmarks](https://loonghao.github.io/transx-benchmarks/)

Our benchmark suite includes:
- Translation lookup performance
- Parameter substitution performance
- Locale switching performance
- Cache efficiency
- Memory usage
- Concurrent operations
- And more...

## 🛠️ Development

### 🔧 Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/loonghao/transx.git
cd transx
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```


### 📦 Project Structure

TransX follows a well-organized package structure:

```
transx/
├── transx/                  # Main package directory
│   ├── __init__.py         # Package initialization
│   ├── __version__.py      # Version information
│   ├── api/                # Public API modules
│   │   ├── __init__.py
│   │   ├── mo.py          # MO file operations
│   │   ├── po.py          # PO file operations
│   │   └── pot.py         # POT file operations
│   ├── app.py             # Application management
│   ├── cli.py             # Command-line interface
│   ├── constants.py        # Constants and configurations
│   ├── context/           # Translation context management
│   │   ├── __init__.py
│   │   └── manager.py    # Context manager implementation
│   ├── core.py            # Core functionality
│   ├── exceptions.py       # Custom exceptions
│   ├── extensions/        # Framework integrations
│   │   ├── __init__.py
│   │   └── qt.py         # Qt support
│   └── internal/          # Internal implementation details
│       ├── __init__.py
│       ├── compat.py     # Python 2/3 compatibility
│       ├── filesystem.py # File system operations
│       └── logging.py    # Logging utilities
├── examples/              # Example code
├── locales/              # Translation files
├── tests/                # Test suite
├── nox_actions/          # Nox automation scripts
├── CHANGELOG.md          # Version history
├── LICENSE              # MIT License
├── README.md            # English documentation
├── README_zh.md         # Chinese documentation
├── noxfile.py           # Test automation config
├── pyproject.toml       # Project configuration
├── requirements.txt     # Production dependencies
└── requirements-dev.txt # Development dependencies
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


### 📊 Code Quality

We maintain high code quality standards using various tools:


- **Linting**: We use ruff and isort for code linting and formatting
- **Type Checking**: Static type checking with mypy
- **Testing**: Comprehensive test suite with pytest
- **Coverage**: Code coverage tracking with coverage.py
- **CI/CD**: Automated testing and deployment with GitHub Actions


### 🧠 AI Skill (TransX)

This repository provides a reusable AI skill for better TransX usage patterns.

Install it locally:

```bash
skills add ./skills/transx
```

After installation, the skill guides AI assistants on:
- standard locale directory layout
- `tr()` / `translate()` usage boundaries
- context (`msgctxt`) best practices
- multi-root loading (`locales_root=[...]`) and conflict behavior
- extraction/update/compile workflow

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
