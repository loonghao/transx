#!/usr/bin/env python
"""Example script for compiling PO files to MO files."""


# Import built-in modules
import os

# Import local modules
from transx.api.mo import compile_po_file
from transx.constants import normalize_language_code


def compile_translations():
    """Compile PO files to MO files for all supported languages."""
    locales_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "locales"))
    # Use standardized full language codes
    languages = ["zh_CN", "ja_JP", "ko_KR", "fr_FR", "es_ES"]

    for lang in languages:
        # Normalize language code
        normalized_lang = normalize_language_code(lang)

        # Build paths for PO and MO files
        locale_dir = os.path.join(locales_dir, normalized_lang, "LC_MESSAGES")
        po_file = os.path.join(locale_dir, "messages.po")
        mo_file = os.path.join(locale_dir, "messages.mo")

        # Ensure directory exists
        os.makedirs(locale_dir, exist_ok=True)

        # Compile PO file to MO file
        if os.path.exists(po_file):
            print(f"Compiling {po_file} to {mo_file}")
            compile_po_file(po_file, mo_file)
        else:
            print(f"Warning: {po_file} does not exist")


if __name__ == "__main__":
    compile_translations()
