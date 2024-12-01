#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PO file format handler for TransX."""
from __future__ import absolute_import, unicode_literals, print_function, division

# Import built-in modules
import os
import re
import sys
from datetime import datetime

# Import local modules
from transx.constants import (
    DEFAULT_CHARSET,
    DEFAULT_ENCODING,
    METADATA_KEYS,
    DEFAULT_METADATA,
    MSGID_PREFIX,
    MSGSTR_PREFIX,
    MSGCTXT_PREFIX
)
from transx.translators import BaseTranslator, DummyTranslator

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode  # noqa: F821
    binary_type = str
else:
    text_type = str
    binary_type = bytes


class POFile:
    """Class representing a PO file."""

    def __init__(self, path, locale=None):
        """Initialize a new PO file handler.
        
        Args:
            path (str): Path to the PO file
            locale (str, optional): Locale code (e.g., 'en_US', 'zh_CN')
        """
        self.path = path
        self.locale = locale or "en_US"
        self.translations = {}  # {(msgid, context): msgstr}
        self.comments = {}  # {(msgid, context): [comments]}
        self.metadata = DEFAULT_METADATA.copy()
        
        self.metadata[METADATA_KEYS['LANGUAGE']] = self.locale

    def _normalize_key(self, msgid):
        """Normalize a message ID for variant matching."""
        if isinstance(msgid, (list, tuple)):
            msgid = msgid[0]  # Use first part for plural forms
        if isinstance(msgid, binary_type):
            msgid = msgid.decode(DEFAULT_CHARSET)
        return msgid.lower()

    def _escape(self, string):
        """Escape a string for PO file format."""
        if isinstance(string, binary_type):
            string = string.decode(DEFAULT_CHARSET)
        result = []
        for char in string:
            if char == '\\':
                result.append('\\\\')
            elif char == '"':
                result.append('\\"')
            elif char == '\n':
                result.append('\\n')
            elif char == '\t':
                result.append('\\t')
            elif char == '\r':
                result.append('\\r')
            else:
                result.append(char)
        return '"' + ''.join(result) + '"'

    def _normalize_string(self, string, prefix='', width=76):
        """Convert a string into PO file format with proper line wrapping."""
        if not string:
            return '""'
        
        if isinstance(string, binary_type):
            string = string.decode(DEFAULT_CHARSET)

        escaped = self._escape(string)
        if width and width > 0:
            # Wrap the string
            chunks = []
            current_line = prefix
            for chunk in escaped[1:-1].split(' '):
                if not current_line:
                    current_line = prefix
                if len(current_line) + len(chunk) + 3 <= width:
                    if current_line[-1:] != ' ':
                        current_line += ' '
                    current_line += chunk
                else:
                    if current_line.strip():
                        chunks.append(self._escape(current_line.rstrip()))
                    current_line = prefix + chunk
            if current_line.strip():
                chunks.append(self._escape(current_line.rstrip()))
            return '"\n"'.join(chunks)
        return escaped

    def add_translation(self, msgid, msgstr='', context=None, comments=None):
        """Add a new translation entry.
        
        Args:
            msgid (str): Message ID (source text)
            msgstr (str, optional): Translated text
            context (str, optional): Message context
            comments (list, optional): List of translator comments
        """
        self.translations[(msgid, context)] = msgstr
        if comments:
            self.comments[(msgid, context)] = comments

    def get_translation(self, msgid, context=None):
        """Get translation for a message.
        
        Args:
            msgid (str): Message ID to look up
            context (str, optional): Message context
            
        Returns:
            str: Translated text or empty string if not found
        """
        return self.translations.get((msgid, context), '')

    def load(self, path=None):
        """Load translations from a PO file.
        
        Args:
            path (str, optional): Path to PO file. If not provided,
                                    uses the path from initialization.
        """
        path = path or self.path
        if not os.path.exists(path):
            return
        
        with open(path, 'r', encoding=DEFAULT_ENCODING) as f:
            content = f.read()

        # 重置translations字典
        self.translations = {}
        self.comments = {}
        
        # 解析元数据
        header_match = re.search(r'msgid ""\nmsgstr "(.*?)"', content, re.DOTALL)
        if header_match:
            header = header_match.group(1)
            for line in header.split('\\n'):
                if not line or ': ' not in line:
                    continue
                key, value = line.split(': ', 1)
                if key in METADATA_KEYS.values():
                    self.metadata[key] = value

        # 使用正则表达式匹配所有翻译条目
        pattern = re.compile(
            r'(?:msgctxt\s+(".*?")\s+)?'  # optional msgctxt
            r'msgid\s+(".*?")\s+'          # msgid
            r'msgstr\s+(".*?")',           # msgstr
            re.DOTALL | re.MULTILINE
        )

        for match in pattern.finditer(content):
            context = None
            if match.group(1):  # msgctxt exists
                context = self._unescape(match.group(1))
            msgid = self._unescape(match.group(2))
            msgstr = self._unescape(match.group(3))
            
            # 跳过元数据条目
            if msgid == '':
                continue
                
            comments = []
            # Find translator comments
            for line in content.splitlines():
                if line.startswith('#. ') and msgid in line:
                    comments.append(line[3:].strip())
            
            self.add_translation(msgid, msgstr, context, comments)

    def _unescape(self, string):
        """Unescape a string from PO file format.
        
        Args:
            string (str): String to unescape (including quotes)
            
        Returns:
            str: Unescaped string
        """
        if not string:
            return ''
            
        # 移除首尾引号
        string = string.strip()[1:-1]
        
        # 处理多行字符串
        parts = string.split('" "')
        string = ''.join(parts)
        
        # 处理转义字符
        return string.replace('\\\\', '\\').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')

    def save(self, path=None):
        """Save translations to a PO file.
        
        Args:
            path (str, optional): Path to save PO file. If not provided,
                                    uses the path from initialization.
        """
        path = path or self.path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding=DEFAULT_ENCODING) as f:
            # 写入元数据
            f.write('msgid ""\nmsgstr ""\n')
            for key, value in self.metadata.items():
                if key == METADATA_KEYS['PO_REVISION_DATE']:
                    value = datetime.now().strftime('%Y-%m-%d %H:%M%z')
                f.write('"{0}: {1}\\n"\n'.format(key, value))
            f.write('\n')
            
            # 写入翻译条目
            for (msgid, context), msgstr in sorted(self.translations.items()):
                # Write translator comments if they exist
                if (msgid, context) in self.comments:
                    for comment in self.comments[(msgid, context)]:
                        f.write('#. {}\n'.format(comment))
                
                if context is not None:
                    f.write('{0}{1}"\n'.format(MSGCTXT_PREFIX, context))
                f.write('{0}{1}"\n'.format(MSGID_PREFIX, msgid))
                f.write('{0}{1}"\n\n'.format(MSGSTR_PREFIX, msgstr))

    def generate_language_files(self, languages, locales_dir):
        """Generate language files based on the current POT file.
        
        Args:
            languages (list): List of language codes (e.g., ['en', 'zh_CN'])
            locales_dir (str): Path to the locales directory
        """
        for lang in languages:
            print(f"Updating existing translations for {lang}...")
            
            # 设置PO文件路径
            po_dir = os.path.join(locales_dir, lang, 'LC_MESSAGES')
            os.makedirs(po_dir, exist_ok=True)
            po_file = os.path.join(po_dir, 'messages.po')

            # 如果PO文件已存在，先读取它
            po = POFile(po_file, locale=lang)
            if os.path.exists(po_file):
                po.load(po_file)

            # 更新翻译
            for (msgid, context) in self.translations:
                if (msgid, context) not in po.translations:
                    po.add_translation(msgid, '', context)

            # 保存更新后的PO文件
            po.save()
            print(f"Updated {po_file}")

    def translate_entries(self, translator=None):
        # type: (BaseTranslator) -> None
        """Translate all untranslated entries using the provided translator.
        
        Args:
            translator (BaseTranslator, optional): Translator to use. If not provided,
                                                uses DummyTranslator.
        """
        translator = translator or DummyTranslator()
        target_lang = self.metadata.get(METADATA_KEYS['LANGUAGE'], 'en')
        
        for (msgid, context), msgstr in self.translations.items():
            if not msgstr:  # Only translate empty entries
                try:
                    translated = translator.translate(
                        msgid,
                        source_lang="auto",
                        target_lang=target_lang
                    )
                    self.translations[(msgid, context)] = translated
                    print("Translated: {} -> {}".format(msgid, translated))
                except Exception as e:
                    print("Failed to translate '{}': {}".format(msgid, str(e)))
