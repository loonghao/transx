"""Test translation functionality."""
# Import built-in modules
import errno
import logging
import os
import sys

# Import third-party modules
import pytest


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
    assert transx_instance.tr("Hello") == "你好"
    assert transx_instance.tr("Goodbye") == "再见"


def test_translation_with_context(transx_instance):
    """Test translations with different contexts."""
    assert transx_instance.tr("Open", context="button") == "打开"
    assert transx_instance.tr("Open", context="menu") == "打开文件"
    assert transx_instance.tr("Welcome", context="home") == "欢迎回来"
    assert transx_instance.tr("Welcome", context="login") == "欢迎登录"


def test_translation_with_parameters(transx_instance):
    """Test translations with parameter substitution."""
    name = "Alice"
    filename = "test.txt"
    assert transx_instance.tr("Hello {name}", name=name) == "你好 {}".format(name)
    assert transx_instance.tr("File {filename} saved", filename=filename) == "文件 {} 已保存".format(filename)


# Edge Cases and Error Handling
def test_missing_translation(transx_instance):
    """Test behavior when translation is missing."""
    missing_text = "This text has no translation"
    assert transx_instance.tr(missing_text) == missing_text


def test_empty_string_translation(transx_instance):
    """Test translation of empty string."""
    assert transx_instance.tr("") == ""


def test_none_input(transx_instance):
    """Test handling of None input."""
    with pytest.raises((ValueError, TypeError)):
        transx_instance.tr(None)

# Locale Management Tests
def test_locale_switching(transx_instance):
    """Test switching between locales."""
    original_text = transx_instance.tr("Hello")
    assert original_text == "你好"

    # Create test locales directory structure
    locales_dir = os.path.join(os.path.dirname(__file__), "data", "locales")
    en_us_dir = os.path.join(locales_dir, "en_US", "LC_MESSAGES")
    makedirs(en_us_dir)

    # Create test MO file
    # Import local modules
    from transx.api.mo import compile_po_file
    from transx.api.po import POFile
    po_file = os.path.join(en_us_dir, "messages.po")
    mo_file = os.path.join(en_us_dir, "messages.mo")

    po = POFile(po_file)
    po.add_translation("Hello", "Hello")
    po.save()
    compile_po_file(po_file, mo_file)

    try:
        transx_instance.current_locale = "en_US"
        assert transx_instance.tr("Hello") == "Hello"
    finally:
        transx_instance.current_locale = "zh_CN"
        assert transx_instance.tr("Hello") == "你好"



# Unicode and Encoding Tests
def test_unicode_handling(transx_instance):
    """Test handling of unicode characters."""
    result = transx_instance.tr("Hello")
    assert result == "你好"
    assert isinstance(result, text_type)


def test_string_operations(transx_instance):
    """Test string operations across Python versions."""
    result = transx_instance.tr("Hello")
    assert isinstance(result, text_type)
    assert result == "你好"


@pytest.mark.skipif(PY2, reason="Unicode string handling differs in Python 2")
def test_unicode_py3(transx_instance):
    """Test Python 3 specific unicode handling."""
    result = transx_instance.tr("Hello")
    assert isinstance(result, str)
    assert result == "你好"




# Context Management Tests
def test_empty_context(transx_instance):
    """Test handling of empty context."""
    assert transx_instance.tr("Hello", context="") == transx_instance.tr("Hello")


def test_none_context(transx_instance):
    """Test handling of None context."""
    assert transx_instance.tr("Hello", context=None) == transx_instance.tr("Hello")


def test_invalid_context_type(transx_instance):
    """Test handling of invalid context type."""
    with pytest.raises((TypeError, ValueError)):
        transx_instance.tr("Hello", context=123)


# Cleanup any resources if needed
def teardown_module(module):
    """Clean up any resources after all tests have run."""
    test_locales = os.path.join(os.path.dirname(__file__), "data", "locales")
    if os.path.exists(test_locales):
        # Import built-in modules
        import shutil
        shutil.rmtree(test_locales)
