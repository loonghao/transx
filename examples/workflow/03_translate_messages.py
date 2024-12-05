#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Translate messages in PO files."""

# Import third-party modules
from common import LANGUAGES
from common import POT_FILE

# Import local modules
from transx.api.translate import GoogleTranslator
from transx.api.translate import translate_po_files


def translate_messages():
    """Translate messages in PO files."""
    # Create translator instance
    translator = GoogleTranslator()

    print("\nTranslating PO files for languages:", LANGUAGES)
    translate_po_files(POT_FILE, LANGUAGES, translator=translator)

if __name__ == "__main__":
    translate_messages()
