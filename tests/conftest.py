"""Test configuration and fixtures."""
# Import built-in modules
from contextlib import suppress
import os
import shutil
import sys

# Import third-party modules
import pytest

# Import local modules
from transx import TransX
from transx.api.mo import compile_po_file
from transx.api.po import POFile
from transx.api.pot import PotExtractor


@pytest.fixture
def test_data_dir():
    """Return the path to test data directory."""
    return os.path.join(os.path.dirname(__file__), "data")

@pytest.fixture
def locales_dir(test_data_dir):
    """Return the path to test locales directory."""
    locales_dir = os.path.join(test_data_dir, "locales")
    os.makedirs(locales_dir, exist_ok=True)
    return locales_dir

@pytest.fixture(autouse=True)
def setup_translations(locales_dir, translations):
    """Set up translation files before each test."""
    # Create PO file for zh_CN
    locale = "zh_CN"
    locale_dir = os.path.join(locales_dir, locale, "LC_MESSAGES")
    os.makedirs(locale_dir, exist_ok=True)

    po_file = os.path.join(locale_dir, "messages.po")
    po = POFile(po_file, locale=locale)

    # Add translations
    for (msgid, context), msgstr in translations[locale].items():
        po.add(msgid, msgstr=msgstr, context=context)
    po.save()

    # Compile PO to MO
    mo_file = os.path.join(locale_dir, "messages.mo")
    compile_po_file(po_file, mo_file)

    yield locale_dir

    # Cleanup after tests
    with suppress(OSError):
        shutil.rmtree(locale_dir)

@pytest.fixture
def transx_instance(locales_dir):
    """Return a TransX instance configured for testing."""
    tx = TransX(locales_root=locales_dir)
    tx.current_locale = "zh_CN"
    return tx

@pytest.fixture
def pot_extractor(locales_dir):
    """Return a POT extractor instance configured for testing."""
    pot_file = os.path.join(locales_dir, "messages.pot")
    return PotExtractor(pot_file)

@pytest.fixture
def translations():
    """Return test translation data."""
    return {
        "zh_CN": {
            # Basic translations
            ("Hello", None): "你好",
            ("Goodbye", None): "再见",
            ("", None): "",  # Empty string test

            # UI Context translations
            ("Open", "button"): "打开",
            ("Open", "menu"): "打开文件",
            ("Save", "button"): "保存",
            ("Save", "menu"): "保存文件",
            ("Save {filename}", "button"): "保存 {filename}",
            ("Save {filename}", "menu"): "保存文件 {filename}",

            # Part of Speech Context translations
            ("Post", "verb"): "发布",
            ("Post", "noun"): "文章",

            # Scene Context translations
            ("Welcome", "home"): "欢迎回来",
            ("Welcome", "login"): "欢迎登录",

            # Parameter translations
            ("Hello {name}", None): "你好 {name}",
            ("File {filename} saved", None): "文件 {filename} 已保存",

            # Special character translations
            ("Hello\nWorld", None): "你好\n世界",
            ("Tab\there", None): "制表符\t在这里",
        }
    }

@pytest.fixture
def python_version():
    """Return the current Python version info."""
    return sys.version_info
