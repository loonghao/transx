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

## 🛠️ Command Line Interface

TransX comes with powerful CLI tools for translation management:

### 📤 Extract Messages

```bash
# Extract from a single file
transx extract app.py

# Extract from a directory with custom options
transx extract ./src \
    --output locales/custom.pot \
    --project "My Project" \
    --version "1.0"
```

### 🔄 Update Translations

```bash
# Update multiple languages
transx update locales/messages.pot en zh_CN ja_JP

# Custom output directory
transx update messages.pot en zh_CN --output-dir ./translations
```

### ⚙️ Compile Translations

```bash
# Compile translations
transx compile locales/*/LC_MESSAGES/messages.po
```

## 📁 Project Structure

```
your_project/
├── 📂 locales/
│   ├── 📂 zh_CN/
│   │   └── 📂 LC_MESSAGES/
│   │       ├── 📝 messages.po    # Source translations
│   │       └── 📦 messages.mo    # Compiled translations
│   └── 📂 ja_JP/
│       └── 📂 LC_MESSAGES/
│           ├── 📝 messages.po
│           └── 📦 messages.mo
└── 📜 your_code.py
```

## 🎯 Advanced Features

### 🌍 Context-Based Translations

```python
# UI Context
print(tx.tr('Open', context='button'))  # 打开
print(tx.tr('Open', context='menu'))    # 打开文件

# Part of Speech
print(tx.tr('Post', context='verb'))    # 发布
print(tx.tr('Post', context='noun'))    # 文章

# Scene Context
print(tx.tr('Welcome', context='login')) # 欢迎登录
print(tx.tr('Welcome', context='home'))  # 欢迎回来
```

### 🛡️ Error Handling

```python
from transx.exceptions import LocaleNotFoundError, CatalogNotFoundError

try:
    tx.current_locale = 'invalid_locale'
except LocaleNotFoundError:
    print("❌ Locale not found")

try:
    tx.load_catalog('missing_catalog.mo')
except CatalogNotFoundError:
    print("❌ Catalog not found")
```

### 📚 Multiple Catalogs

```python
tx = TransX()
tx.load_catalog('path/to/main.mo')     # Main catalog
tx.load_catalog('path/to/extra.mo')    # Extra translations
```

## ⚡ Performance Tips

- 🚀 Uses compiled MO files for optimal speed
- 💾 Automatic translation caching
- 🔒 Thread-safe for concurrent access
- 📉 Minimal memory footprint

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Submit pull requests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
Made with ❤️ by the LongHao
</div>
