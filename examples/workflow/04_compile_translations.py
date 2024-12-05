#!/usr/bin/env python
"""Example script for compiling PO files to MO files."""


# Import built-in modules
import os

# Import third-party modules
from common import LANGUAGES
from common import LOCALES_DIR

# Import local modules
from transx.api.locale import normalize_language_code
from transx.api.mo import compile_po_file


def compile_translations():
    """Compile PO files to MO files for all supported languages."""
    # Use standardized full language codes
    for lang in LANGUAGES:
        # Normalize language code
        normalized_lang = normalize_language_code(lang)

        # Build paths for PO and MO files
        locale_dir = os.path.join(LOCALES_DIR, normalized_lang, "LC_MESSAGES")
        po_file = os.path.join(locale_dir, "messages.po")
        mo_file = os.path.join(locale_dir, "messages.mo")

        # Ensure directory exists
        if not os.path.exists(locale_dir):
            os.makedirs(locale_dir)

        # Compile PO file to MO file
        if os.path.exists(po_file):
            print("Compiling %s to %s" % (po_file, mo_file))
            compile_po_file(po_file, mo_file)
        else:
            print("Warning: %s does not exist" % po_file)


if __name__ == "__main__":
    compile_translations()
