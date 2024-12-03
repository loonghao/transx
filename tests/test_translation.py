#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test translation functionality."""
# Import built-in modules
import logging
import os
import sys

# Import third-party modules
import pytest

# Import local modules
from transx.constants import DEFAULT_CHARSET

logger = logging.getLogger(__name__)

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode
else:
    text_type = str


# Basic Translation Tests
def test_basic_translation(transx_instance):
    """Test basic translation without context."""
    assert isinstance(transx_instance.tr("Hello"), text_type)
    assert transx_instance.tr("Hello") == text_type("Hello")  # No translation in test
    assert transx_instance.tr("Goodbye") == text_type("Goodbye")  # No translation in test


def test_translation_with_context(transx_instance):
    """Test translations with different contexts."""
    assert transx_instance.tr("Open", context="button") == text_type("Open")  # Button action
    assert transx_instance.tr("Open", context="menu") == text_type("Open")  # Menu action
    assert transx_instance.tr("Welcome", context="home") == text_type("Welcome")  # Home page
    assert transx_instance.tr("Welcome", context="login") == text_type("Welcome")  # Login page


def test_translation_with_parameters(transx_instance):
    """Test translations with parameter substitution using Template."""
    name = text_type("Alice")
    filename = text_type("test.txt")
    price = text_type("100")
    
    # Test basic parameter substitution
    assert transx_instance.tr("Hello, $name!", name=name) == text_type(u"你好，Alice！")
    
    # Test with ${name} syntax
    assert transx_instance.tr("File ${filename} saved", filename=filename) == text_type(u"文件 test.txt 已保存")
    
    # Test with dollar sign
    assert transx_instance.tr("Price: $${price}", price=price) == text_type(u"价格：$100")
    
    # Test missing parameter (should keep the placeholder)
    assert transx_instance.tr("Hello, $name!") == text_type("Hello, $name!")
    
    # Test multiple parameters
    assert transx_instance.tr("$name saved $filename", name=name, filename=filename) == text_type("Alice saved test.txt")


def test_missing_translation(transx_instance):
    """Test behavior when translation is missing."""
    missing_text = "This text does not exist in translations"
    assert transx_instance.tr(missing_text) == text_type(missing_text)


def test_empty_string_translation(transx_instance):
    """Test translation of empty string."""
    assert transx_instance.tr("") == text_type("")


def test_unicode_handling(transx_instance):
    """Test handling of unicode characters."""
    assert isinstance(transx_instance.tr("Hello\nWorld"), text_type)
    assert transx_instance.tr("Hello\nWorld") == text_type("Hello\nWorld")
    assert transx_instance.tr("Tab\there") == text_type("Tab\there")


def test_string_operations(transx_instance):
    """Test string operations across Python versions."""
    text = transx_instance.tr("Hello")
    assert isinstance(text, text_type)
    assert text.encode(DEFAULT_CHARSET).decode(DEFAULT_CHARSET) == text


@pytest.mark.skipif(PY2, reason="Python 3 specific unicode test")
def test_unicode_py3(transx_instance):
    """Test Python 3 specific unicode handling."""
    text = transx_instance.tr("Hello")
    assert isinstance(text, str)
    assert isinstance(text.encode(), bytes)
    assert isinstance(text.encode().decode(), str)


def test_empty_context(transx_instance):
    """Test handling of empty context."""
    assert transx_instance.tr("Hello", context="") == text_type("Hello")


def test_none_context(transx_instance):
    """Test handling of None context."""
    assert transx_instance.tr("Hello", context=None) == text_type("Hello")


@pytest.fixture
def transx_instance(tmp_path):
    """Create a TransX instance for testing."""
    from transx import TransX
    from transx.api.po import POFile
    
    # Create test PO file
    po_dir = tmp_path / "locales" / "zh_CN" / "LC_MESSAGES"
    po_dir.mkdir(parents=True, exist_ok=True)
    po_file = po_dir / "messages.po"
    
    po = POFile(path=str(po_file), locale="zh_CN")
    # Add test translations
    po.add(msgid="Hello", msgstr="Hello")
    po.add(msgid="Goodbye", msgstr="Goodbye")
    po.add(msgid="Open", msgstr="Open", context="button")
    po.add(msgid="Open", msgstr="Open", context="menu")
    po.add(msgid="Welcome", msgstr="Welcome", context="home")
    po.add(msgid="Welcome", msgstr="Welcome", context="login")
    po.add(msgid="Hello, $name!", msgstr="你好，$name！")
    po.add(msgid="File ${filename} saved", msgstr="文件 ${filename} 已保存")
    po.add(msgid="Price: $${price}", msgstr="价格：$${price}")
    po.add(msgid="$name saved $filename", msgstr="$name saved $filename")
    po.add(msgid="Hello\nWorld", msgstr="Hello\nWorld")
    po.add(msgid="Tab\there", msgstr="Tab\there")
    po.save()
    
    # Initialize TransX
    tx = TransX(locales_root=str(tmp_path / "locales"))
    tx.current_locale = "zh_CN"
    return tx
