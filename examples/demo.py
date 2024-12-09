#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TransX Demo Program

This demo showcases the key features of TransX, including:
1. Instance creation and caching
2. Locale switching and persistence
3. Multiple app support
4. Translation functionality with context
5. Unicode handling
"""
# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# Import built-in modules
import logging
import os
import sys


try:
    # Import built-in modules
    from builtins import str  # Python 2/3 compatibility
except ImportError:
    str = unicode  # Python 2 fallback

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Import local modules
from transx import get_transx_instance


def test_instance_management():
    """Test TransX instance management features."""
    print("\n=== Instance Management ===\n")

    # Create instances for different apps
    app1 = get_transx_instance("app1", default_locale="en_US")
    app2 = get_transx_instance("app2", default_locale="ja_JP")

    print("Initial setup:")
    print("App1 default locale: {0}".format(app1._context.default_locale))
    print("App2 default locale: {0}".format(app2._context.default_locale))

    # Switch locales independently
    app1.switch_locale("zh_CN")
    app2.switch_locale("fr_FR")

    print("\nAfter switching:")
    print("App1 current locale: {0}".format(app1._context.current_locale))
    print("App2 current locale: {0}".format(app2._context.current_locale))

    # Get same instances again
    app1_again = get_transx_instance("app1", default_locale="ko_KR")
    app2_again = get_transx_instance("app2", default_locale="es_ES")

    print("\nRetrieved instances:")
    print("App1 current/default: {0}/{1}".format(
        app1_again._context.current_locale,
        app1_again._context.default_locale
    ))
    print("App2 current/default: {0}/{1}".format(
        app2_again._context.current_locale,
        app2_again._context.default_locale
    ))


def test_basic_translations(tx):
    """Test basic translations with both add_message and add_translation."""
    print("\n=== Basic Translations ===\n")

    # Using add_translation (high-level API)
    print("Using add_translation:")
    tx.add_translation("Hello", "こんにちは", context="greeting")
    tx.add_translation("Hello", "おはよう", context="morning")
    tx.add_translation("Welcome {name}", "ようこそ {name}さん")

    print("Greeting: {0}".format(tx.tr("Hello", context="greeting")))
    print("Morning: {0}".format(tx.tr("Hello", context="morning")))
    print("Welcome: {0}".format(tx.tr("Welcome {name}", name="Alice")))
    print("Default Hello: {0}".format(tx.tr("Hello")))  # Without context

    # Using add_message (low-level API)
    print("\nUsing add_message directly:")
    catalog = tx._catalogs[tx._context.current_locale]
    catalog.add_message("Goodbye", "さようなら")
    catalog.add_message("Thanks", "ありがとう", context="greeting")  # Using context parameter

    print("Direct message: {0}".format(catalog.get_message("Goodbye")))
    print("Direct with context: {0}".format(catalog.get_message("Thanks", context="greeting")))


def test_locale_persistence():
    """Test locale persistence across instances."""
    print("\n=== Locale Persistence ===\n")

    # Create initial instance
    tx1 = get_transx_instance("persist_demo", default_locale="ja_JP")
    print("Initial default locale: {0}".format(tx1._context.default_locale))

    # Switch locale
    tx1.switch_locale("zh_CN")
    print("Switched current locale to: {0}".format(tx1._context.current_locale))

    # Create new instance with different default
    tx2 = get_transx_instance("persist_demo", default_locale="en_US")
    print("New instance - current: {0}, default: {1}".format(
        tx2._context.current_locale,
        tx2._context.default_locale
    ))


def test_unicode_handling(tx):
    """Test unicode handling."""
    print("\n=== Unicode Handling ===")
    print(tx.tr("Hello", context="login"))
    print(tx.tr(r"Hello\nWorld"))  # Explicitly show newline
    print(tx.tr(r"Tab\there"))     # Explicitly show tab
    print(tx.tr("Tab\\there!"))     # Explicitly show tab
    print(tx.tr(r'Path to the file: "C:\Program Files\MyApp"'))  # Use raw string for path

def test_multiline_strings(tx):
    """Test multiline string support."""
    print("\n=== Multiline String Support ===\n")
    print(tx.tr("如果出现错误，显示找不到 DCF_updateViewportList,"
                "或者找不到 CgAbBlastPanelOptChangeCallback，"
                "说明你的文件存在病毒，请运行一下打开优化工具，"
                "执行 remove unknown node and plugin 和 remove callback 两个按钮，"
                "然后保存一下文件"))


def test_multiple_languages(tx):
    """Test translations for different languages."""
    print("\n=== Multiple Languages Support ===\n")

    # Common phrases to test
    phrases = {
        "Hello": {
            "fr_FR": "Bonjour",
            "zh_CN": "你好",
            "ja_JP": "こんにちは",
            "ko_KR": "안녕하세요",
            "es_ES": "Hola"
        },
        "Welcome {name}": {
            "fr_FR": "Bienvenue {name}",
            "zh_CN": "欢迎 {name}",
            "ja_JP": "ようこそ {name}さん",
            "ko_KR": "환영합니다 {name}님",
            "es_ES": "Bienvenido {name}"
        },
        "Settings": {
            "fr_FR": "Paramètres",
            "zh_CN": "设置",
            "ja_JP": "設定",
            "ko_KR": "설정",
            "es_ES": "Configuración"
        }
    }

    # Test translations for different languages
    languages = ["fr_FR", "zh_CN", "ja_JP", "ko_KR", "es_ES"]

    for lang in languages:
        print("\n" + "=" * 50)
        print("Testing language:", lang)
        print("=" * 50)

        # Switch to the language
        tx.switch_locale(lang)

        # Add translations for this language
        for msgid, translations in phrases.items():
            tx.add_translation(msgid, translations[lang])

        # Define translatable strings
        strings = {
            "hello": tx.tr("Hello"),
            "welcome": tx.tr("Welcome {name}", name="Alice"),
            "settings": tx.tr("Settings")
        }

        # Test the translations
        print("Simple greeting:", strings["hello"])
        print("Welcome message:", strings["welcome"])
        print("Settings menu:", strings["settings"])


def main():
    """Run all demo tests."""
    # Create a TransX instance for testing
    tx = get_transx_instance("demo", default_locale="ja_JP")

    # Run all tests
    test_instance_management()
    test_basic_translations(tx)
    test_locale_persistence()
    test_unicode_handling(tx)
    test_multiline_strings(tx)
    test_multiple_languages(tx)


if __name__ == "__main__":
    main()
