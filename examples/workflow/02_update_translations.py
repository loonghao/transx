#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update PO files from POT file."""

# Import built-in modules

# Import third-party modules
from common import LANGUAGES
from common import LOCALES_DIR
from common import POT_FILE

# Import local modules
from transx.api.pot import PotUpdater


def update_translations():
    """Update translation catalogs."""
    # Create PO updater
    updater = PotUpdater(pot_file=POT_FILE, locales_dir=LOCALES_DIR)

    updater.create_language_catalogs(LANGUAGES)

    print("Language catalogs updated.")


if __name__ == "__main__":
    update_translations()
