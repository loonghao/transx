#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Multilingual support demo program."""
# Import built-in modules
import logging
import os
import sys

# For Python 2/3 compatibility
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding("utf-8")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Import local modules
from transx import TransX


def test_basic_translations(tx):
    """Test basic translations."""
    print(tx.tr("Hello", context="login"))
    print(tx.tr("Welcome {name}", name="Alice"))
    print(tx.tr("Hello~"))
    print(tx.tr("Current username: $username"))
    print(tx.tr("Current language is {lang}", lang=tx.current_locale))

def test_workflow_messages(tx):
    """Test workflow related messages."""
    print("\n=== Workflow Messages ===\n")
    print(tx.tr("Hello~"))
    print(tx.tr("Starting workflow"))
    print(tx.tr("Processing file {filename}", filename="data.txt"))
    print(tx.tr("Workflow completed"))
    print(tx.tr("Validating input data"))
    print(tx.tr("Analyzing results"))
    print(tx.tr("Task completed successfully"))

def test_error_messages(tx):
    """Test error messages."""
    print("\n=== Error Messages ===\n")
    print(tx.tr("Error: File not found"))
    print(tx.tr("Warning: Low disk space"))
    print(tx.tr("Invalid input: {input}", input="abc123"))
    print(tx.tr("Operation failed: {reason}", reason="timeout"))

def test_unicode_handling(tx):
    """Test unicode handling."""
    print("\n=== Unicode Handling ===")
    print(tx.tr("Hello"))
    print(tx.tr(r"Hello\nWorld"))  # Explicitly show newline
    print(tx.tr(r"Tab\there"))     # Explicitly show tab
    print(tx.tr("Tab\\there!"))     # Explicitly show tab
    print(tx.tr(r'Path to the file: "C:\Program Files\MyApp"'))  # Use raw string for path

def main():
    # Initialize TransX instance with language pack directory
    locale_dir = os.path.join(os.path.dirname(__file__), "locales")
    tx = TransX(locales_root=locale_dir, default_locale="fr_FR")

    # Test translations for different languages
    languages = ["fr_FR", "zh_CN", "ja_JP", "ko_KR", "es_ES"]

    for lang in languages:
        print("\n==================================================")
        print("Testing language: {}".format(lang))
        print("==================================================")

        # Switch language
        tx.current_locale = lang

        # Run all tests
        test_basic_translations(tx)
        test_workflow_messages(tx)
        test_error_messages(tx)
        test_unicode_handling(tx)

if __name__ == "__main__":
    main()
