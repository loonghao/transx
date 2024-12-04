#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Translate messages in PO files."""

# Import third-party modules
from common import POT_FILE

# Import local modules
from transx.api.translate import GoogleTranslator
from transx.api.translate import translate_po_files


def translate_messages():
    """Translate messages in PO files."""
    # Create translator instance
    translator = GoogleTranslator()

    languages = ["zh_CN", "ja_JP", "ko_KR", "fr_FR", "es_ES"]
    print("\nTranslating PO files for languages:", languages)
    translate_po_files(POT_FILE, languages, translator=translator)

if __name__ == "__main__":
    translate_messages()
