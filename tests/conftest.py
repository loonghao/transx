#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test configuration and fixtures."""
# Import built-in modules
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
    try:
        os.makedirs(locales_dir)
    except OSError:
        if not os.path.isdir(locales_dir):
            raise
    return locales_dir


@pytest.fixture
def transx_instance(locales_dir):
    """Return a TransX instance configured for testing."""
    return TransX(locales_root=locales_dir)


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
            (u"Hello", None): u"Hello",
            (u"Goodbye", None): u"Goodbye",
            (u"", None): u"",  # Empty string test

            # Parameter translations
            (u"Hello, $name!", None): u"Hello, $name!",
            (u"File ${filename} saved", None): u"File ${filename} saved",
            (u"Price: $${price}", None): u"Price: ${price}",
            (u"Hello {name}", None): u"Hello {name}",
            (u"File {filename} saved", None): u"File {filename} saved",

            # UI Context translations
            (u"Open", u"button"): u"Open",
            (u"Open", u"menu"): u"Open file",
            (u"Save", u"button"): u"Save",
            (u"Save", u"menu"): u"Save file",
            (u"Save {filename}", u"button"): u"Save {filename}",
            (u"Save {filename}", u"menu"): u"Save file {filename}",

            # Part of Speech Context translations
            (u"Post", u"verb"): u"Post",
            (u"Post", u"noun"): u"Post",

            # Scene Context translations
            (u"Welcome", u"home"): u"Welcome back",
            (u"Welcome", u"login"): u"Welcome login",

            # Special character translations
            (u"Hello\nWorld", None): u"Hello\nWorld",
            (u"Tab\there", None): u"Tab\there",
        },
        "ja_JP": {
            # Basic translations
            (u"Hello", None): u"こんにちは",
            (u"Goodbye", None): u"さようなら",
            (u"", None): u"",  # Empty string test

            # Parameter translations
            (u"Hello, $name!", None): u"こんにちは、$name!",
            (u"File ${filename} saved", None): u"ファイル ${filename} が保存されました",
            (u"Price: $${price}", None): u"価格: ${price}円",
            (u"Hello {name}", None): u"こんにちは、{name}さん",
            (u"File {filename} saved", None): u"ファイル {filename} が保存されました",

            # UI Context translations
            (u"Open", u"button"): u"開く",
            (u"Open", u"menu"): u"ファイルを開く",
            (u"Save", u"button"): u"保存",
            (u"Save", u"menu"): u"ファイルを保存",
            (u"Save {filename}", u"button"): u"{filename} を保存",
            (u"Save {filename}", u"menu"): u"ファイル {filename} を保存",

            # Part of Speech Context translations
            (u"Post", u"verb"): u"投稿する",
            (u"Post", u"noun"): u"投稿",

            # Scene Context translations
            (u"Welcome", u"home"): u"おかえりなさい",
            (u"Welcome", u"login"): u"ログインしました",

            # Special character translations
            (u"Hello\nWorld", None): u"こんにちは\n世界",
            (u"Tab\there", None): u"タブ\tここ",
        }
    }


@pytest.fixture(autouse=True)
def setup_translations(locales_dir, translations):
    """Set up translation files before each test."""
    locale_dirs = []

    # Create PO files for all locales
    for locale, translations_data in translations.items():
        locale_dir = os.path.join(locales_dir, locale, "LC_MESSAGES")
        try:
            os.makedirs(locale_dir)
        except OSError:
            if not os.path.isdir(locale_dir):
                raise
        locale_dirs.append(locale_dir)

        po_file = os.path.join(locale_dir, "messages.po")
        po = POFile(po_file, locale=locale)

        # Add translations
        for (msgid, context), msgstr in translations_data.items():
            po.add(msgid, msgstr=msgstr, context=context)
        po.save()  # POFile.save() directly writes to file

        # Compile PO to MO
        mo_file = os.path.join(locale_dir, "messages.mo")
        compile_po_file(po_file, mo_file)

    yield locale_dirs

    # Cleanup after tests
    for locale_dir in locale_dirs:
        try:  # noqa: SIM105
            shutil.rmtree(locale_dir)
        except OSError:
            # Ignore errors when cleaning up test directory
            pass


@pytest.fixture(autouse=True)
def setup_env_vars(locales_dir):
    """Set up environment variables for tests."""
    # Store original environment
    old_env = {}
    test_apps = ["TEST_APP", "APP1", "APP2"]

    # Set up test environment
    for app in test_apps:
        env_var = "TRANSX_{}_LOCALES_ROOT".format(app)
        old_env[env_var] = os.environ.get(env_var)
        os.environ[env_var] = locales_dir

    yield

    # Restore original environment
    for env_var, value in old_env.items():
        if value is None:
            del os.environ[env_var]
        else:
            os.environ[env_var] = value


@pytest.fixture
def python_version():
    """Return the current Python version info."""
    return sys.version_info
