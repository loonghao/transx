#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Common utilities for workflow scripts."""
# Import built-in modules
import os
import sys


# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Constants
DEMO_FILE = os.path.join(os.path.dirname(__file__), "..", "demo.py")
LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "locales")
POT_FILE = os.path.join(LOCALES_DIR, "messages.pot")

LANGUAGES = ["zh", "ja_JP", "ko_KR", "fr_FR", "es_ES", "en_US"]
# Create locales directory if it doesn't exist
if not os.path.exists(LOCALES_DIR):
    os.makedirs(LOCALES_DIR)
