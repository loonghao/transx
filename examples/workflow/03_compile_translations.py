#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example script for compiling PO files to MO files."""

from __future__ import absolute_import, unicode_literals, print_function, division

import os
from transx.formats.mo import compile_po_file
from transx.constants import normalize_language_code


def compile_translations():
    """Compile PO files to MO files for all supported languages."""
    locales_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'locales'))
    # Use standardized full language codes
    languages = ['zh_CN', 'ja_JP', 'ko_KR', 'fr_FR', 'es_ES']
    
    for lang in languages:
        # Normalize language code
        normalized_lang = normalize_language_code(lang)
        
        # Build paths for PO and MO files
        locale_dir = os.path.join(locales_dir, normalized_lang, 'LC_MESSAGES')
        po_file = os.path.join(locale_dir, 'messages.po')
        mo_file = os.path.join(locale_dir, 'messages.mo')
        
        # Ensure directory exists
        os.makedirs(locale_dir, exist_ok=True)
        
        # Compile PO file to MO file
        if os.path.exists(po_file):
            print("Compiling {} to {}".format(po_file, mo_file))
            compile_po_file(po_file, mo_file)
        else:
            print("Warning: {} does not exist".format(po_file))


if __name__ == "__main__":
    compile_translations()
