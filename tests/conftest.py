#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test configuration and fixtures."""
# Import built-in modules
import os
import shutil
import sys
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
    try:
        os.makedirs(locales_dir)
    except OSError:
        if not os.path.isdir(locales_dir):
            raise
    return locales_dir

@pytest.fixture(autouse=True)
def setup_translations(locales_dir, translations):
    """Set up translation files before each test."""
    # Create PO file for zh_CN
    locale = "zh_CN"
    locale_dir = os.path.join(locales_dir, locale, "LC_MESSAGES")
    try:
        os.makedirs(locale_dir)
    except OSError:
        if not os.path.isdir(locale_dir):
            raise

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
    try:
        shutil.rmtree(locale_dir)
    except OSError:
        pass

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
            (u"Hello", None): u"你好",
            (u"Goodbye", None): u"再见",
            (u"", None): u"",  # Empty string test

            # Parameter translations
            (u"Hello, $name!", None): u"你好，$name！",
            (u"File ${filename} saved", None): u"文件 ${filename} 已保存",
            (u"Price: $${price}", None): u"价格：$${price}",
            (u"Hello {name}", None): u"你好 {name}",
            (u"File {filename} saved", None): u"文件 {filename} 已保存",

            # UI Context translations
            (u"Open", u"button"): u"打开",
            (u"Open", u"menu"): u"打开文件",
            (u"Save", u"button"): u"保存",
            (u"Save", u"menu"): u"保存文件",
            (u"Save {filename}", u"button"): u"保存 {filename}",
            (u"Save {filename}", u"menu"): u"保存文件 {filename}",

            # Part of Speech Context translations
            (u"Post", u"verb"): u"发布",
            (u"Post", u"noun"): u"文章",

            # Scene Context translations
            (u"Welcome", u"home"): u"欢迎回来",
            (u"Welcome", u"login"): u"欢迎登录",

            # Special character translations
            (u"Hello\nWorld", None): u"你好\n世界",
            (u"Tab\there", None): u"制表符\t在这里",
        }
    }

@pytest.fixture
def python_version():
    """Return the current Python version info."""
    return sys.version_info
