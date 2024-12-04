#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update PO files from POT file."""

# Import built-in modules

# Import third-party modules
from common import LOCALES_DIR, POT_FILE

# Import local modules
from transx.api.pot import PotUpdater


def update_translations():
    """Update translation catalogs."""
    # Create PO updater
    updater = PotUpdater(pot_file=POT_FILE, locales_dir=LOCALES_DIR)

    # Update PO files for all languages
    languages = ["zh", "ja_JP", "ko_KR", "fr_FR", "es_ES"]
    updater.create_language_catalogs(languages)

    print("Language catalogs updated.")


if __name__ == "__main__":
    update_translations()
