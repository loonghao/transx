#!/usr/bin/env python
"""POT updater for TransX."""

# fmt: off
# isort: skip
# Import future modules
from __future__ import unicode_literals

# Import built-in modules
from collections import OrderedDict
import datetime
import os

# Import local modules
from transx.api.locale import normalize_language_code
from transx.api.po import POFile
from transx.api.pot.base_file import POTFile
from transx.constants import HEADER_COMMENT
from transx.constants import LANGUAGE_CODES
from transx.constants import LANGUAGE_NAMES


class PotUpdater(object):
    """Update PO catalogs from a POT file."""

    def __init__(self, pot_file, locales_dir):
        """Initialize a new PotUpdater instance.

        Args:
            pot_file: Path to POT file
            locales_dir: Base directory for locale files
        """
        self.pot_file = pot_file
        self.locales_dir = locales_dir

        # Load the POT file
        self.pot_catalog = POTFile(pot_file)
        if os.path.exists(pot_file):
            self.pot_catalog.load()
        else:
            raise ValueError("POT file not found: {}".format(pot_file))

    def create_language_catalogs(self, languages):
        """Create or update PO catalogs for specified languages.

        Args:
            languages: List of language codes to generate catalogs for
        """
        for lang in languages:
            # Create language directory
            lang = normalize_language_code(lang)
            if lang not in LANGUAGE_CODES:
                print("Warning: Unknown language code %r" % lang)
                continue

            locale_dir = os.path.join(self.locales_dir, lang, "LC_MESSAGES")
            if not os.path.exists(locale_dir):
                os.makedirs(locale_dir)

            # Create or update PO file
            self.update_po_file(lang)

    def update_po_file(self, lang):
        """Update a PO file with messages from the POT file.

        Args:
            lang: Language code for the PO file

        """
        # Load POT file
        pot = POFile(self.pot_file)
        pot.load()

        # Create language directory
        lang_dir = os.path.join(self.locales_dir, lang, "LC_MESSAGES")
        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir)
        po_file_path = os.path.join(lang_dir, "messages.po")

        # Create PO file from POT
        po = POFile(po_file_path, locale=lang)
        po.load() if os.path.exists(po_file_path) else None

        # Update PO from POT
        po.update(pot)

        # Set language-specific metadata
        po.metadata.update({
            "Language": lang,
            "Language-Team": "%s <LL@li.org>" % lang,
            "Plural-Forms": "nplurals=1; plural=0;" if lang.startswith("zh") else "nplurals=2; plural=(n != 1);"
        })

        # Save PO file
        po.save()
        print("Created/updated PO file: {}".format(po_file_path))

    def _update_po_metadata(self, po_catalog, language):
        """Update PO file metadata based on POT metadata and language.

        Args:
            po_catalog: The PO catalog to update
            language: Language code for the PO file
        """
        # Start with metadata from POT file
        metadata = OrderedDict()
        for key, value in self.pot_catalog.metadata.items():
            if key not in ["Language", "Language-Team", "Plural-Forms", "PO-Revision-Date"]:
                metadata[key] = value

        # Update language-specific metadata
        now = datetime.datetime.now()
        revision_date = now.strftime("%Y-%m-%d %H:%M%z")

        # Get language display name
        language_name = LANGUAGE_NAMES.get(language, language)

        # Set language-specific metadata
        metadata.update({
            "Project-Id-Version": metadata.get("Project-Id-Version", "PROJECT VERSION"),
            "Report-Msgid-Bugs-To": metadata.get("Report-Msgid-Bugs-To", "EMAIL@ADDRESS"),
            "POT-Creation-Date": metadata.get("POT-Creation-Date", revision_date),
            "PO-Revision-Date": revision_date,
            "Last-Translator": "FULL NAME <EMAIL@ADDRESS>",
            "Language": language,
            "Language-Team": "{} <LL@li.org>".format(language_name),
            "MIME-Version": "1.0",
            "Content-Type": "text/plain; charset=UTF-8",
            "Content-Transfer-Encoding": "8bit",
            "Generated-By": "TransX",
        })

        # Update plural forms based on language
        if language.startswith("zh") or language in ["ja", "ja_JP", "ko", "ko_KR", "vi", "vi_VN"]:
            metadata["Plural-Forms"] = "nplurals=1; plural=0;"
        elif language in ["fr", "fr_FR", "es", "es_ES"]:
            metadata["Plural-Forms"] = "nplurals=2; plural=(n > 1);"
        else:
            metadata["Plural-Forms"] = "nplurals=2; plural=(n != 1);"

        po_catalog.metadata = metadata

    def _update_po_header_comment(self, po_catalog, language):
        """Update PO file header comment.

        Args:
            po_catalog: The PO catalog to update
            language: Language code for the PO file
        """
        # Get language display name
        language_name = LANGUAGE_NAMES.get(language, language)

        # Add header comments with fuzzy flag
        year = datetime.datetime.now().year
        po_catalog.header_comment = HEADER_COMMENT.format(language_name, year, year)
