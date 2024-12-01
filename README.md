# TransX

A lightweight, zero-dependency Python internationalization library that supports Python 2.7 through 3.12.

## Features

- Zero external dependencies
- Python 2.7 to 3.12 compatibility
- Context-based translations for accurate localization
- Standard gettext .po/.mo file format support
- Simple and intuitive API
- Automatic translation file management
- String extraction from Python source code
- Unicode support
- Parameter substitution in translations

## Installation

```bash
pip install transx
```

## Quick Start

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
print(tx.tr('Save {filename}', context='button', filename='test.txt'))  # Output: 保存 test.txt

## Command Line Interface

TransX provides a convenient command-line interface for managing translations:

### Extract Messages

Extract translatable messages from source files to a POT file:

```bash
# Extract from a single file
transx extract app.py

# Extract from a directory
transx extract ./src

# Extract with custom options
transx extract ./src \
    --output locales/custom.pot \
    --project "My Project" \
    --version "1.0" \
    --copyright "My Company" \
    --bugs-address "bugs@example.com"
```

### Update Translation Files

Create or update PO files for specific languages:

```bash
# Update translations for multiple languages
transx update locales/messages.pot en zh_CN ja_JP

# Specify custom output directory
transx update messages.pot en zh_CN --output-dir ./translations
```

### Compile Translations

Compile PO files to MO files for use in production:

```bash
# Compile a single PO file
transx compile locales/en/LC_MESSAGES/messages.po

# Compile multiple PO files
transx compile locales/*/LC_MESSAGES/messages.po
```

## Directory Structure

TransX follows the standard gettext directory structure:

```
your_project/
├── locales/
│   ├── zh_CN/
│   │   └── LC_MESSAGES/
│   │       ├── messages.po    # Source translation file
│   │       └── messages.mo    # Compiled translation file
│   └── ja_JP/
│       └── LC_MESSAGES/
│           ├── messages.po
│           └── messages.mo
└── your_code.py
```

## Examples

### Basic Usage

```python
from transx import TransX

# Initialize translator
tx = TransX(locales_root='locales')
tx.current_locale = 'zh_CN'

# Basic translation
print(tx.tr('Hello'))  # Output: 你好
print(tx.tr('Goodbye'))  # Output: 再见

# With parameters
print(tx.tr('Hello {name}!', name='张三'))  # Output: 你好 张三！
```

### Context-Based Translations

```python
# UI Context Example
print(tx.tr('Open', context='button'))  # Output: 打开
print(tx.tr('Open', context='menu'))    # Output: 打开文件

# Part of Speech Context
print(tx.tr('Post', context='verb'))  # Output: 发布
print(tx.tr('Post', context='noun'))  # Output: 文章

# Scene Context
print(tx.tr('Welcome', context='login'))  # Output: 欢迎登录
print(tx.tr('Welcome', context='home'))   # Output: 欢迎回来
```

### Advanced Usage

### Loading Translation Catalogs

TransX supports loading translation catalogs directly:

```python
from transx import TransX

tx = TransX()

# Load a specific catalog file
tx.load_catalog('path/to/messages.mo')

# Load catalogs from a directory structure
tx = TransX(locales_root='locales')
tx.current_locale = 'zh_CN'  # Will automatically load catalogs for zh_CN
```

### Working with Multiple Catalogs

You can work with multiple translation catalogs:

```python
tx = TransX()
tx.load_catalog('path/to/main.mo')    # Load main translations
tx.load_catalog('path/to/extra.mo')   # Load additional translations

# Translations from both catalogs will be available
print(tx.tr('Hello'))  # Uses translations from either catalog
```

### Translation Workflow

1. Extract messages from source code:
```python
from transx.formats.pot import PotExtractor

# Create POT extractor
extractor = PotExtractor('locales/messages.pot')

# Scan Python files
extractor.scan_file('your_code.py')
extractor.save_pot()
```

2. Create/Update PO files:
```python
from transx.formats.po import POFile

# Create PO file for Chinese
po = POFile('locales/zh_CN/LC_MESSAGES/messages.po', locale='zh_CN')

# Add translations
po.add_translation("Hello", msgstr="你好")
po.add_translation("Open", msgstr="打开", context="button")
po.save()
```

3. Compile PO to MO:
```python
from transx.formats.mo import compile_po_file

# Compile PO to MO
compile_po_file(
    'locales/zh_CN/LC_MESSAGES/messages.po',
    'locales/zh_CN/LC_MESSAGES/messages.mo'
)
```

For more examples, check out the [examples](examples/) directory.

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=transx
```

## License

MIT License - see LICENSE file for details
