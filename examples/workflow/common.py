#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Common utilities for workflow scripts."""
import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Constants
DEMO_FILE = os.path.join(os.path.dirname(__file__), "..", "demo.py")
LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "locales")
POT_FILE = os.path.join(LOCALES_DIR, "messages.pot")

# Create locales directory if it doesn't exist
if not os.path.exists(LOCALES_DIR):
    os.makedirs(LOCALES_DIR)
