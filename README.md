# 🌏 TransX

🚀 A lightweight, zero-dependency Python internationalization library that supports Python 2.7 through 3.12.

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
| 🔠 Parameters | Dynamic parameter substitution             |
| ⚡ Performance | High-speed and thread-safe operations      |
| 🛡️ Error Handling | Comprehensive error management             |
| 🧪 Testing | Extensive test coverage                    |
| 🌐 Auto Translation | Built-in Google Translate support          |

</div>

## 🚀 Quick Start

### 📥 Installation

```bash
pip install transx
```

### 📝 Basic Usage

```python
from transx import TransX

# Initialize translator
tx = TransX(locales_root='locales')
tx.current_locale = 'zh_CN'

# Basic translation
print(tx.tr('Hello'))  # Output: 你好

# Translation with context
print(tx.tr('Open', context='button'))  # Output: 打开
print(tx.tr('Open', context='menu'))    # Output: 打开文件

# Translation with parameters
print(tx.tr('Hello {name}!', name='张三'))  # Output: 你好 张三！
```

## 🛠️ Advanced API Usage

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
from transx.api.translate import GoogleTranslator, create_po_files

# Initialize Google Translator
translator = GoogleTranslator()

# Create and auto-translate PO files for multiple languages
create_po_files(
    pot_file_path="messages.pot",
    languages=["zh_CN", "ja_JP", "ko_KR"],
    output_dir="locales",
    translator=translator
)

# Or translate a single PO file
from transx.api.translate import translate_po_file
translate_po_file("locales/zh_CN/LC_MESSAGES/messages.po", translator)
```

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

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
