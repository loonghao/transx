# 🌏 TransX

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

<div align="center">

| Feature | Description                                |
|---------|--------------------------------------------|
| 🚀 Zero Dependencies | No external dependencies required          |
| 🐍 Python Support | Full support for Python 2.7-3.12           |
| 🌍 Context-based | Accurate translations with context support |
| 📦 Standard Format | Compatible with gettext .po/.mo files      |
| 🎯 Simple API | Clean and intuitive interface              |
| 🔄 Auto Management | Automatic translation file handling        |
| 🔍 String Extraction | Built-in source code string extraction     |
| 🌐 Unicode | Complete Unicode support                   |
| 🔠 Parameters | Named, positional and ${var} style parameters |
| 💫 Variable Support | Environment variable expansion support     |
| ⚡ Performance | High-speed and thread-safe operations      |
| 🛡️ Error Handling | Comprehensive error management with fallbacks |
| 🧪 Testing | 100% test coverage with extensive cases    |
| 🌐 Auto Translation | Built-in Google Translate API support      |
| 🎥 DCC Support | Tested with Maya, 3DsMax, Houdini, etc.   |
| 📁 Project Structure | Well-organized and maintainable codebase |
| 🔌 Extensible | Pluggable custom text interpreters system |
| 🎨 Flexible Formatting | Support for various string format styles  |
| 🔄 Runtime Switching | Dynamic locale switching at runtime       |
</div>

## 📁 Project Structure

```
transx/
├── transx/                 # Main package directory
│   ├── api/               # Public API implementations
│   ├── internal/          # Internal implementation details
│   ├── core.py           # Core functionality
│   ├── cli.py            # Command-line interface
│   ├── constants.py      # Constants and configurations
│   └── exceptions.py     # Custom exceptions
├── examples/              # Example code and usage demos
├── tests/                # Test suite
├── pyproject.toml        # Project configuration
└── noxfile.py           # Test automation configuration
```

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
tx.current_locale = "ja_JP"
print(tx.tr("Hello"))  # Output: こんにちは
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

### 🌍 Environment Variable Support

```python
# Environment variables are automatically expanded
tx.tr("User home: ${HOME}")
tx.tr("Current path: ${PATH}")

# Mix with translation parameters
tx.tr("Welcome {name} to ${HOSTNAME}!", name="John")
```

### 🎯 Context-Aware Translation

```python
# Same string, different contexts
tx.tr("Open", context="button")      # Translation for button label
tx.tr("Open", context="menu")        # Translation for menu item
tx.tr("Open", context="file_state")  # Translation for file status

# Context with parameters
tx.tr("Created {count} items", count=5, context="notification")
```

## 🛠️ Advanced API Usage

### 🔌 Custom Interpreter System

TransX provides a powerful and flexible interpreter system that allows you to customize text processing:

```python
from transx import TextInterpreter, InterpreterExecutor

# Create a custom interpreter
class MyCustomInterpreter(TextInterpreter):
    name = "custom"
    description = "My custom text processor"

    def interpret(self, text, context=None):
        # Add your custom text processing logic here
        return text.replace("old", "new")

# Use built-in interpreters
tx = TransX(locales_root="./locales")
executor = tx.get_interpreter_executor()

# Add your custom interpreter
executor.add_interpreter(MyCustomInterpreter())

# Built-in interpreters include:
# - TextTypeInterpreter: Ensures correct text encoding
# - DollarVariableInterpreter: Handles ${var} style variables
# - ParameterSubstitutionInterpreter: Handles {name} style parameters
# - EnvironmentVariableInterpreter: Expands environment variables
# - TranslationInterpreter: Handles text translation

# Chain multiple interpreters
executor = InterpreterExecutor([
    MyCustomInterpreter(),
    tx.get_interpreter("env"),     # Environment variables
    tx.get_interpreter("dollar"),  # ${var} style variables
])

# Execute the interpreter chain
result = executor.execute("Hello ${USER}", {"name": "world"})

# Safe execution with fallback
result = executor.execute_safe(
    "Hello ${USER}",
    fallback_interpreters=[tx.get_interpreter("parameter")]
)
```

The interpreter system follows a chain-of-responsibility pattern where each interpreter can:
- Transform text in its own specific way
- Pass context information between interpreters
- Be ordered to control processing sequence
- Fail safely without affecting other interpreters
- Have fallback options for robustness

### Message Extraction and PO/MO File Management

```python
from transx.api.pot import PotExtractor
from transx.api.po import POFile
from transx.api.mo import compile_po_file

# Extract messages from source code
extractor = PotExtractor(project="MyProject", version="1.0")
extractor.scan_file("app.py")
extractor.save("messages.pot")

# Create/Update PO file
po = POFile("zh_CN/LC_MESSAGES/messages.po")
po.add_translation("Hello", "你好")
po.add_translation("Welcome", "欢迎", context="greeting")
po.save()

# Compile PO to MO
compile_po_file("zh_CN/LC_MESSAGES/messages.po", "zh_CN/LC_MESSAGES/messages.mo")
```

### Automatic Translation with Google Translate

```python
from transx.api.translate import GoogleTranslator, translate_po_files

# Initialize Google Translator
translator = GoogleTranslator()

# Create and auto-translate PO files for multiple languages
translate_po_files(
    pot_file_path="messages.pot",
    languages=["zh_CN", "ja_JP", "ko_KR"],
    output_dir="locales",
    translator=translator
)

```

### Implementing Custom Translation API

You can implement your own translation API by inheriting from the `Translator` base class:

```python
from transx.api.translate import Translator
from transx.api.translate import translate_po_files


class MyCustomTranslator(Translator):
    def translate(self, text, source_lang="auto", target_lang="en"):
        """Implement your custom translation logic.

        Args:
            text (str): Text to translate
            source_lang (str): Source language code (default: auto)
            target_lang (str): Target language code (default: en)

        Returns:
            str: Translated text
        """
        # Add your translation logic here
        # For example, calling your own translation service:
        return my_translation_service.translate(
            text=text,
            from_lang=source_lang,
            to_lang=target_lang
        )


# Use your custom translator
translator = MyCustomTranslator()
translate_po_files(
    pot_file_path="messages.pot",
    languages=["zh_CN", "ja_JP"],
    translator=translator
)
```

### 🔌 Implementing Custom Translation API

TransX provides a flexible way to implement your own translation service. You can either:
- 🔧 Implement your own translation logic
- 🔗 Integrate with third-party translation libraries
- 🌐 Use direct HTTP requests to translation services

#### Basic Implementation

The simplest way is to inherit from the `Translator` base class:

```python
from transx.api.translate import Translator
from transx.api.translate import translate_po_files


class MyCustomTranslator(Translator):
    def translate(self, text, source_lang="auto", target_lang="en"):
        """Implement your custom translation logic.

        Args:
            text (str): Text to translate
            source_lang (str): Source language code (default: auto)
            target_lang (str): Target language code (default: en)

        Returns:
            str: Translated text
        """
        # Add your translation logic here
        return my_translation_service.translate(
            text=text,
            from_lang=source_lang,
            to_lang=target_lang
        )


# Use your custom translator
translator = MyCustomTranslator()
translate_po_files(
    pot_file_path="messages.pot",
    languages=["zh_CN", "ja_JP"],
    translator=translator
)
```

#### 🚀 Using Third-Party Libraries

For faster implementation, you can integrate with existing translation libraries:

<details>
<summary>📚 deep-translator (Python 3.x only)</summary>

```python
from deep_translator import GoogleTranslator as DeepGoogleTranslator
from transx.api.translate import Translator

class DeepTranslator(Translator):
    """A powerful translator using deep-translator library.

    Supported Services:
    ✨ Google Translate
    ✨ DeepL
    ✨ Microsoft Translator
    ✨ PONS
    ✨ Linguee
    ✨ MyMemory
    And more...
    """
    def translate(self, text, source_lang="auto", target_lang="en"):
        try:
            # Convert language codes (e.g., zh_CN -> zh-cn)
            source = source_lang.lower().replace('_', '-')
            target = target_lang.lower().replace('_', '-')

            translator = DeepGoogleTranslator(
                source=source if source != "auto" else "auto",
                target=target
            )
            return translator.translate(text)
        except Exception as e:
            raise TranslationError(f"Translation failed: {str(e)}")
```
</details>

<details>
<summary>📦 translate (Python 2.7 compatible)</summary>

```python
from translate import Translator as PyTranslator
from transx.api.translate import Translator

class SimpleTranslator(Translator):
    """A lightweight translator using the 'translate' library.

    Supported Services:
    ✨ Google Translate
    ✨ MyMemory
    ✨ Microsoft Translator
    """
    def translate(self, text, source_lang="auto", target_lang="en"):
        try:
            translator = PyTranslator(from_lang=source_lang, to_lang=target_lang)
            return translator.translate(text)
        except Exception as e:
            raise TranslationError(f"Translation failed: {str(e)}")
```
</details>

#### ⚠️ Python 2.7 Compatibility Note

While TransX supports Python 2.7 through 3.12, many modern translation libraries have dropped Python 2.7 support. Here are your options:

1. 📦 Use older versions of translation libraries that still support Python 2.7
2. 🌐 Implement a simple HTTP client to directly call translation APIs
3. ✨ Use TransX's built-in `GoogleTranslator` which maintains Python 2.7 compatibility

<details>
<summary>🔧 HTTP Client Example (Python 2.7 compatible)</summary>

```python
import requests
from transx.api.translate import Translator
from transx.compat import urlencode

class SimpleGoogleTranslator(Translator):
    """A basic Google Translate implementation using requests."""

    def translate(self, text, source_lang="auto", target_lang="en"):
        try:
            # Convert language codes
            source = source_lang.lower().replace('_', '-')
            target = target_lang.lower().replace('_', '-')

            # Build URL
            params = {
                'sl': source,
                'tl': target,
                'q': text
            }
            url = 'https://translate.googleapis.com/translate_a/single?' + urlencode({
                'client': 'gtx',
                'dt': 't',
                **params
            })

            # Make request
            response = requests.get(url)
            data = response.json()

            # Extract translation
            return ''.join(part[0] for part in data[0])

        except Exception as e:
            raise TranslationError(f"Translation failed: {str(e)}")
```
</details>

### 🌍 Language Code Support

TransX provides flexible language code handling with automatic normalization:

<details>
<summary>📝 Example Usage</summary>

```python
from transx import TransX

tx = TransX()

# Different language code formats are supported:
tx.current_locale = "zh-CN"    # Hyphen format
tx.current_locale = "zh_CN"    # Underscore format
tx.current_locale = "zh"       # Language only (will use default country code)
tx.current_locale = "Chinese"  # Language name
```
</details>

#### Supported Language Codes

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

#### 🔄 Default Behavior

TransX handles language codes in the following way:
1. 🔍 Attempts to detect the system language automatically
2. 🔄 Normalizes language codes to standard format (e.g., `zh-CN` → `zh_CN`)
3. ⚡ Falls back to `en_US` if the system language is not supported or cannot be detected

## 🛠️ Command Line Interface

TransX provides a powerful CLI for translation management:

### Extract Messages
```bash
# Extract from a single file
transx extract app.py -o messages.pot

# Extract from a directory
transx extract ./src -o messages.pot -p "MyProject" -v "1.0"
```

### Update PO Files
```bash
# Update or create PO files for specific languages
transx update messages.pot -l zh_CN ja_JP ko_KR

# Auto-translate during update
transx update messages.pot -l zh_CN ja_JP ko_KR --translate
```

### Compile MO Files
```bash
# Compile a single PO file
transx compile locales/zh_CN/LC_MESSAGES/messages.po

# Compile all PO files in a directory
transx compile locales
```

## 🌐 Supported Languages

The Google Translator supports a wide range of languages. Here are some commonly used language codes:

- Chinese (Simplified): `zh_CN`
- Japanese: `ja_JP`
- Korean: `ko_KR`
- French: `fr_FR`
- Spanish: `es_ES`

For a complete list of supported languages, refer to the [language code documentation](https://cloud.google.com/translate/docs/languages).

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

TransX provides comprehensive error handling for various scenarios:

```python
from transx import TransX
from transx.exceptions import LocaleNotFoundError, CatalogNotFoundError, TranslationError

# 1. Locale and Catalog Errors
tx = TransX(strict_mode=True)  # Enable strict mode to raise exceptions

try:
    tx.load_catalog("invalid_locale")
except LocaleNotFoundError as e:
    print(f"❌ Locale error: {e.message}")
    print(f"  Missing locale: {e.locale}")

try:
    tx.load_catalog(None)
except ValueError as e:
    print("❌ Invalid locale: Locale cannot be None")

# 2. Translation Errors
from transx.api.translate import GoogleTranslator

translator = GoogleTranslator()
try:
    result = translator.translate("Hello", source_lang="invalid", target_lang="zh_CN")
except TranslationError as e:
    print(f"❌ Translation failed: {e.message}")
    print(f"  Source text: {e.source_text}")
    print(f"  From: {e.source_lang} To: {e.target_lang}")

# 3. File Parsing Errors
from transx.exceptions import ParserError, ValidationError
from transx.api.po import POFile

try:
    po = POFile("invalid.po")
    po.parse()
except ParserError as e:
    print(f"❌ Parse error in {e.file_path}")
    if e.line_number:
        print(f"  At line: {e.line_number}")
    if e.reason:
        print(f"  Reason: {e.reason}")

# 4. Non-Strict Mode Behavior
tx = TransX(strict_mode=False)  # Default behavior
# These operations will log warnings instead of raising exceptions
tx.load_catalog("missing_locale")  # Returns False, logs warning
tx.tr("missing_key")  # Returns the key itself, logs warning
```

Key error handling features:
- 🔒 Strict mode for development/testing
- 📝 Detailed error messages and context
- 🪵 Fallback behavior in non-strict mode
- 📋 Comprehensive logging

### 🔧 Error Handling

```python
from transx.exceptions import TranslationError, LocaleError

try:
    tx.tr("Hello")
except TranslationError as e:
    print(f"Translation failed: {e}")
except LocaleError as e:
    print(f"Locale error: {e}")
```

### Multiple Catalogs

```python
tx = TransX()
tx.load_catalog("path/to/main.mo")     # Main catalog
tx.load_catalog("path/to/extra.mo")    # Extra translations
```

## ⚡ Performance Features

- 🚀 Uses compiled MO files for optimal speed
- 💾 Automatic translation caching
- 🔒 Thread-safe for concurrent access
- 📉 Minimal memory footprint
- 🔄 Automatic PO to MO compilation

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 👨‍💻 Developer Guide

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

### 📁 Project Structure

```
transx/
├── transx/                 # Main package directory
│   ├── api/               # Public API modules
│   │   ├── locale.py      # Locale handling
│   │   ├── mo.py         # MO file operations
│   │   ├── po.py         # PO file operations
│   │   └── translate.py   # Translation services
│   ├── core.py           # Core functionality
│   └── constants.py       # Constants and configurations
├── tests/                 # Test directory
├── examples/              # Example code and usage
├── nox_actions/          # Nox automation scripts
│   ├── codetest.py       # Test execution configuration
│   ├── lint.py          # Code linting and formatting
│   └── utils.py         # Shared utilities and constants
└── docs/                 # Documentation
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

### 🤝 Contributing

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
