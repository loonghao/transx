from __future__ import absolute_import, unicode_literals, print_function, division

import os
import sys
import abc

# Import local modules
from transx.formats.po import POFile
from transx.constants import (
    LANGUAGE_CODES,
    LANGUAGE_CODE_ALIASES,
    INVALID_LANGUAGE_CODE_ERROR,
    DEFAULT_LOCALE
)

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})
    text_type = unicode  # noqa: F821
else:
    ABC = abc.ABC
    text_type = str

class Translator(ABC):
    """Base class for translation API."""
    
    @abc.abstractmethod
    def translate(self, text, source_lang="auto", target_lang="en"):
        """Translate text from source language to target language."""
        pass

class DummyTranslator(Translator):
    """A dummy translator that returns the input text unchanged."""
    
    def translate(self, text, source_lang="auto", target_lang="en"):
        return text

def ensure_dir(path):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(path):
        os.makedirs(path)

def normalize_locale(locale):
    """标准化语言代码格式
    
    将各种格式的语言代码转换为标准格式（如 'zh-CN' -> 'zh_CN'）。
    支持的格式包括：
    - ISO 639-1 语言代码（如 'en'）
    - ISO 3166-1 国家/地区代码（如 'zh_CN'）
    - 常见的非标准代码（如 'cn' -> 'zh_CN'）
    
    Args:
        locale (str): 语言代码 (e.g., 'zh-CN', 'zh_cn', 'zh')
        
    Returns:
        str: 标准化的语言代码 (e.g., 'zh_CN')
        
    Raises:
        ValueError: 如果提供了无效的语言代码
    """
    if not locale:
        return DEFAULT_LOCALE
        
    # 移除所有空白并转换为小写
    normalized = locale.strip().lower()
    
    # 检查是否是标准代码
    if normalized in LANGUAGE_CODES:
        return normalized
    
    # 检查是否是别名
    if normalized in LANGUAGE_CODE_ALIASES:
        return LANGUAGE_CODE_ALIASES[normalized]
    
    # 如果代码包含分隔符，尝试标准化格式
    if '-' in normalized or '_' in normalized:
        parts = normalized.replace('-', '_').split('_')
        if len(parts) == 2:
            lang, region = parts
            # 构建可能的标准代码
            possible_code = '{}_{}'.format(lang, region.upper())
            if possible_code in LANGUAGE_CODES:
                return possible_code
    
    # 如果找不到匹配的代码，生成错误消息
    valid_codes = '\n'.join(
        '- {} ({}): {}'.format(
            code, 
            name, 
            ', '.join(["'" + a + "'" for a in aliases])
        )
        for code, (name, aliases) in sorted(LANGUAGE_CODES.items())
    )
    
    raise ValueError(
        INVALID_LANGUAGE_CODE_ERROR.format(
            code=locale,
            valid_codes=valid_codes
        )
    )

def translate_po_file(po_file_path, translator=None):
    """
    Translate a PO file using the specified translator.
    
    Args:
        po_file_path (str): Path to the PO file
        translator (Translator, optional): Translator instance to use
    """
    if translator is None:
        translator = DummyTranslator()
    
    # 确保目录存在
    po_dir = os.path.dirname(po_file_path)
    ensure_dir(po_dir)
    
    print("Loading PO file: {}".format(po_file_path))
    po = POFile(po_file_path)
    po.load()
    
    # 获取目标语言并标准化
    lang_dir = os.path.basename(os.path.dirname(os.path.dirname(po_file_path)))
    lang = normalize_locale(lang_dir)
    print("Target language: {}".format(lang))
    
    # 打印当前的翻译条目数
    print("Total translation entries: {}".format(len(po.translations)))
    
    # 遍历所有未翻译的条目
    untranslated_count = 0
    for (msgid, context), msgstr in po.translations.items():
        if not msgstr:  # 只翻译空的条目
            untranslated_count += 1
            try:
                print("\nTranslating: {}".format(msgid))
                translated = translator.translate(msgid, target_lang=lang)
                print("Translated to: {}".format(translated))
                po.add_translation(msgid, translated, context)
            except Exception as e:
                print("Failed to translate '{}': {}".format(msgid, str(e)))
    
    print("\nTotal untranslated entries: {}".format(untranslated_count))
    
    if untranslated_count > 0:
        print("Saving translations to: {}".format(po_file_path))
        po.save()
    else:
        print("No untranslated entries found.")

def translate_pot_file(pot_file_path, languages, output_dir=None, translator=None):
    """
    Generate and translate PO files from a POT file for specified languages.
    
    Args:
        pot_file_path (str): Path to the POT file
        languages (list): List of language codes to generate (e.g. ['en', 'zh_CN'])
        output_dir (str, optional): Output directory for PO files
        translator (Translator, optional): Translator instance to use
    """
    if translator is None:
        translator = DummyTranslator()
    
    if output_dir is None:
        output_dir = os.path.dirname(pot_file_path)
    
    # 确保POT文件存在
    if not os.path.exists(pot_file_path):
        raise FileNotFoundError("POT file not found: {}".format(pot_file_path))
    
    # 确保输出目录存在
    ensure_dir(output_dir)
    
    # 加载POT文件
    print("Loading POT file: {}".format(pot_file_path))
    pot = POFile(pot_file_path)
    pot.load()
    
    # 标准化语言代码并创建PO文件
    for lang in languages:
        lang = normalize_locale(lang)
        print("\nProcessing language: {}".format(lang))
        
        # 创建语言目录结构
        lang_dir = os.path.join(output_dir, lang, 'LC_MESSAGES')
        ensure_dir(lang_dir)
        
        # 生成PO文件路径
        po_file = os.path.join(lang_dir, os.path.basename(pot_file_path).replace('.pot', '.po'))
        
        # 创建并翻译PO文件
        print("Generating PO file: {}".format(po_file))
        pot.generate_language_files([lang], output_dir)
        translate_po_file(po_file, translator)
