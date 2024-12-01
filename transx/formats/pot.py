#!/usr/bin/env python
"""POT file format handler for TransX."""

# Import built-in modules
import os
import re
import sys

# Import local modules
from transx.constants import (
    METADATA_KEYS,
    DEFAULT_CHARSET,
    DEFAULT_KEYWORDS,
    TR_FUNCTION_PATTERN,
    normalize_language_code,
)
from .po import POFile

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode  # noqa: F821
    binary_type = str
else:
    text_type = str
    binary_type = bytes


class PotExtractor:
    """Extract translatable strings from Python source files."""

    def __init__(self, output_file="messages.pot", keywords=None):
        self.output_file = output_file
        self.keywords = keywords or DEFAULT_KEYWORDS
        self.messages = POFile(output_file)
        self.current_file = None

    def scan_directory(self, directory):
        """Scan directory for Python files and extract messages."""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    self.scan_file(os.path.join(root, file))

    def scan_file(self, filename):
        """Scan a file for translatable strings."""
        self.current_file = filename
        with open(filename, encoding=DEFAULT_CHARSET) as f:
            content = f.read()

        # Extract all translation function calls
        for match in re.finditer(TR_FUNCTION_PATTERN, content):
            msgid = match.group(1).strip()  # Remove leading/trailing whitespace
            context = match.group(2).strip() if match.group(2) else None  # Remove leading/trailing whitespace
            
            # Add message to catalog
            if context:
                self.messages.add_translation(msgid, context=context)
            else:
                self.messages.add_translation(msgid)

    def save_pot(self, project="", version="", copyright_holder="", bugs_address=""):
        """Save extracted messages to POT file."""
        # Add metadata
        self.messages.metadata[METADATA_KEYS["PROJECT_ID_VERSION"]] = f"{project} {version}"
        self.messages.metadata[METADATA_KEYS["REPORT_MSGID_BUGS_TO"]] = bugs_address
        self.messages.metadata[METADATA_KEYS["COPYRIGHT"]] = copyright_holder
        self.messages.metadata[METADATA_KEYS["MIME_VERSION"]] = "1.0"
        self.messages.metadata[METADATA_KEYS["CONTENT_TYPE"]] = "text/plain; charset=utf-8"
        self.messages.metadata[METADATA_KEYS["CONTENT_TRANSFER_ENCODING"]] = "8bit"
        self.messages.metadata[METADATA_KEYS["GENERATED_BY"]] = "TransX"
        
        self.messages.save()

    def generate_language_files(self, languages, locales_dir):
        """Generate language files based on the current POT file.
        
        Args:
            languages (list): List of language codes (e.g., ['en', 'zh_CN'])
            locales_dir (str): Path to the locales directory
        """
        for lang in languages:
            # 标准化语言代码
            normalized_lang = normalize_language_code(lang)
            print(f"Updating existing translations for {normalized_lang}...")
            
            # 设置PO文件路径
            po_dir = os.path.join(locales_dir, normalized_lang, "LC_MESSAGES")
            os.makedirs(po_dir, exist_ok=True)
            po_file = os.path.join(po_dir, "messages.po")

            # 如果PO文件已存在，先读取它
            po = POFile(po_file, locale=normalized_lang)
            if os.path.exists(po_file):
                po.load(po_file)

            # 更新翻译
            for (msgid, context) in self.messages.translations:
                if (msgid, context) not in po.translations:
                    po.add_translation(msgid, "", context)

            # 保存更新后的PO文件
            po.save()
            print(f"Updated {po_file}")
