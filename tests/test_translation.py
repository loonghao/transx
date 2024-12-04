#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test translation functionality."""
# Import built-in modules
import logging
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


def test_basic_parameter_substitution(transx_instance):
    """Test basic parameter substitution in translations."""
    filename = text_type("test.txt")
    # Test with ${name} syntax
    assert transx_instance.tr("File ${filename} saved", filename=filename) == text_type(u"文件 {0} 已保存".format(filename))


def test_dollar_sign_handling(transx_instance):
    """Test handling of dollar signs in translations."""
    price = text_type("100")
    # Test with dollar sign
    assert transx_instance.tr("Price: $${price}", price=price) == text_type(u"价格: $$100")
    # Test with multiple dollar signs
    assert transx_instance.tr("Price: $${price}$$", price=price) == text_type(u"Price: $$100$$")


def test_missing_parameter(transx_instance):
    """Test behavior when parameter is missing."""
    # Test missing parameter (should keep the placeholder)
    assert transx_instance.tr("Hello, $name!") == text_type(u"你好, $name!")


def test_multiple_parameters(transx_instance):
    """Test translations with multiple parameters."""
    name = text_type("Alice")
    filename = text_type("test.txt")
    # Test multiple parameters
    assert transx_instance.tr("$name saved $filename", name=name, filename=filename) == text_type("Alice saved test.txt")


@pytest.fixture
def env_vars(monkeypatch):
    """Setup test environment variables."""
    monkeypatch.setenv("TEST_USER", "john")
    monkeypatch.setenv("TEST_FILE", "data.txt")


def test_environment_variable_expansion(transx_instance, env_vars):
    """Test environment variable expansion in translations."""
    filename = text_type("test.txt")

    # Test environment variable expansion with translation
    assert transx_instance.tr("File $TEST_FILE saved") == text_type(u"文件 data.txt 已保存")

    # Test environment variable with parameter substitution
    assert transx_instance.tr("User $TEST_USER saved ${filename}", filename=filename) == text_type(u"用户 john 保存了 {0}".format(filename))

    # Test environment variable that doesn't exist (should keep the placeholder)
    assert transx_instance.tr("Welcome $NONEXISTENT_USER") == text_type("Welcome $NONEXISTENT_USER")

    # Test escaping dollar sign with environment variable
    assert transx_instance.tr("Price: $$TEST_FILE") == text_type("Price: $$TEST_FILE")


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
    # Import local modules
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
    po.add(msgid="Hello, $name!", msgstr="你好, $name!")
    po.add(msgid="File ${filename} saved", msgstr="文件 ${filename} 已保存")
    po.add(msgid="Price: $${price}", msgstr="价格: $$100")
    po.add(msgid="$name saved $filename", msgstr="$name saved $filename")
    po.add(msgid="Hello\nWorld", msgstr="Hello\nWorld")
    po.add(msgid="Tab\there", msgstr="Tab\there")
    po.add(msgid="File $TEST_FILE saved", msgstr="文件 $TEST_FILE 已保存")
    po.add(msgid="User $TEST_USER saved ${filename}", msgstr="用户 $TEST_USER 保存了 ${filename}")
    po.add(msgid="Price: $${price}$$", msgstr="Price: $$100$$")
    po.save()

    # Initialize TransX
    tx = TransX(locales_root=str(tmp_path / "locales"))
    tx.current_locale = "zh_CN"
    return tx
