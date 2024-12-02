"""Test translation functionality."""
# Import built-in modules
import logging
import os
import sys

# Import third-party modules
import pytest

# Import local modules
from transx.exceptions import CatalogNotFoundError
from transx.exceptions import LocaleNotFoundError


logger = logging.getLogger(__name__)

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
    assert transx_instance.tr("Hello {name}", name=name) == f"你好 {name}"
    assert transx_instance.tr("File {filename} saved", filename=filename) == f"文件 {filename} 已保存"

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

def test_invalid_parameter_format(transx_instance):
    """Test handling of invalid parameter format."""
    with pytest.raises((KeyError, ValueError)):
        transx_instance.tr("Hello {name}", wrong_param="test")

# Locale Management Tests
def test_locale_switching(transx_instance):
    """Test switching between locales."""
    original_text = transx_instance.tr("Hello")
    assert transx_instance.tr("Hello") == original_text
    try:
        transx_instance.current_locale = "en_US"
        assert transx_instance.tr("Hello") == "Hello"
    finally:
        transx_instance.current_locale = "zh_CN"
        assert transx_instance.tr("Hello") == "你好"

def test_invalid_locale(transx_instance):
    """Test handling of invalid locale."""
    original_locale = transx_instance.current_locale
    try:
        with pytest.raises((LocaleNotFoundError, ValueError)):
            transx_instance.current_locale = "invalid_locale"
    finally:
        transx_instance.current_locale = original_locale

# Unicode and Encoding Tests
def test_unicode_handling(transx_instance):
    """Test handling of unicode characters."""
    result = transx_instance.tr("Hello")
    assert result == "你好"
    try:
        unicode_type = unicode  # Python 2
    except NameError:
        unicode_type = str     # Python 3
    assert isinstance(result, unicode_type)

def test_string_operations(transx_instance):
    """Test string operations across Python versions."""
    result = transx_instance.tr("Hello")
    assert isinstance(result, str if str is bytes else str)  # Python 2/3 compatible
    assert result == "你好"

@pytest.mark.skipif(sys.version_info[0] < 3,
                    reason="Unicode string handling differs in Python 2")
def test_unicode_py3(transx_instance):
    """Test Python 3 specific unicode handling."""
    result = transx_instance.tr("Hello")
    assert isinstance(result, str)
    assert result == "你好"

# File Operations Tests
def test_catalog_loading(transx_instance, locales_dir):
    """Test loading of translation catalogs."""
    assert os.path.exists(locales_dir)
    transx_instance.load_catalog("zh_CN")
    assert transx_instance.tr("Hello") == "你好"

def test_missing_catalog(transx_instance):
    """Test handling of missing catalog."""
    with pytest.raises((CatalogNotFoundError, IOError, OSError)):
        transx_instance.load_catalog("missing_locale")

# Performance Tests
def test_multiple_translations(transx_instance):
    """Test performance with multiple translations."""
    for _ in range(100):
        assert transx_instance.tr("Hello") == "你好"

# Context Management Tests
def test_empty_context(transx_instance):
    """Test handling of empty context."""
    assert transx_instance.tr("Open", context="") == transx_instance.tr("Open")

def test_none_context(transx_instance):
    """Test handling of None context."""
    assert transx_instance.tr("Open", context=None) == transx_instance.tr("Open")

def test_invalid_context_type(transx_instance):
    """Test handling of invalid context type."""
    with pytest.raises((TypeError, ValueError)):
        transx_instance.tr("Open", context=123)

# Cleanup any resources if needed
def teardown_module(module):
    """Clean up any resources after all tests have run."""
    logging.info("Cleaning up after translation tests")
