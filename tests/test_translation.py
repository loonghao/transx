"""Test translation functionality."""
# Import built-in modules
import errno
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


def makedirs(path):
    """Create directory and ignore error if it exists."""
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


# Basic Translation Tests
def test_basic_translation(transx_instance):
    """Test basic translation without context."""
    assert isinstance(transx_instance.tr("Hello"), text_type)
    assert transx_instance.tr("Hello") == text_type("你好")
    assert transx_instance.tr("Goodbye") == text_type("再见")


def test_translation_with_context(transx_instance):
    """Test translations with different contexts."""
    assert transx_instance.tr("Open", context="button") == text_type("打开")
    assert transx_instance.tr("Open", context="menu") == text_type("打开文件")
    assert transx_instance.tr("Welcome", context="home") == text_type("欢迎回来")
    assert transx_instance.tr("Welcome", context="login") == text_type("欢迎登录")


def test_translation_with_parameters(transx_instance):
    """Test translations with parameter substitution."""
    name = text_type("Alice")
    filename = text_type("test.txt")
    assert transx_instance.tr("Hello {name}", name=name) == text_type("你好 {}").format(name)
    assert transx_instance.tr("File {filename} saved", filename=filename) == text_type("文件 {} 已保存").format(filename)


def test_missing_translation(transx_instance):
    """Test behavior when translation is missing."""
    missing_text = "This text does not exist in translations"
    assert transx_instance.tr(missing_text) == text_type(missing_text)


def test_empty_string_translation(transx_instance):
    """Test translation of empty string."""
    assert transx_instance.tr("") == text_type("")


def test_none_input(transx_instance):
    """Test handling of None input."""
    with pytest.raises(ValueError):
        transx_instance.tr(None)


# Locale Management Tests
def test_locale_switching(transx_instance):
    """Test switching between locales."""
    # Default locale
    assert transx_instance.tr("Hello") == text_type("你好")
    
    # Non-existent locale should use fallback behavior
    transx_instance.current_locale = "fr_FR"
    assert transx_instance.tr("Hello") == text_type("Hello")
    
    # Switch back to zh_CN
    transx_instance.current_locale ="zh_CN"
    assert transx_instance.tr("Hello") == text_type("你好")


# Unicode and Encoding Tests
def test_unicode_handling(transx_instance):
    """Test handling of unicode characters."""
    assert isinstance(transx_instance.tr("Hello\nWorld"), text_type)
    assert transx_instance.tr("Hello\nWorld") == text_type("你好\n世界")
    assert transx_instance.tr("Tab\there") == text_type("制表符\t在这里")


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


# Context Management Tests
def test_empty_context(transx_instance):
    """Test handling of empty context."""
    assert transx_instance.tr("Hello", context="") == text_type("你好")


def test_none_context(transx_instance):
    """Test handling of None context."""
    assert transx_instance.tr("Hello", context=None) == text_type("你好")


def test_invalid_context_type(transx_instance):
    """Test handling of invalid context type."""
    with pytest.raises((TypeError, ValueError)):
        transx_instance.tr("Hello", context=123)


def teardown_module(module):
    """Clean up any resources after all tests have run."""
    pass
