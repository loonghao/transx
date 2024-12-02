#!/usr/bin/env python
"""POT file format handler for TransX."""

# Import built-in modules
import os
import re
import sys
import tokenize
import io
import ast
import datetime
from collections import OrderedDict

# Import local modules
from transx.constants import (
    DEFAULT_CHARSET,
    DEFAULT_ENCODING,
    DEFAULT_METADATA,
    METADATA_KEYS,
    DEFAULT_KEYWORDS,
    MSGCTXT_PREFIX,
    MSGID_PREFIX,
    MSGSTR_PREFIX,
    REFERENCE_COMMENT_PREFIX,
    TRANSLATOR_COMMENT_PREFIX,
    TR_FUNCTION_PATTERN,
    normalize_language_code
)
from transx.api.po import POFile
from transx.api.message import Message
from transx.api.locale import normalize_locale

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode
    binary_type = str
else:
    text_type = str
    binary_type = bytes


class PotExtractor(object):
    """Extract translatable strings from Python source files."""

    def __init__(self, source_files=None, pot_file=None):
        """Initialize a new PotExtractor instance.

        Args:
            source_files: List of source files to extract from
            pot_file: Path to output POT file
        """
        self.source_files = source_files or []
        self.pot_file = pot_file
        self.catalog = POFile(path=pot_file)
        self.current_file = None
        self.current_line = 0
        self._init_pot_metadata()

    def __enter__(self):
        """Enter the runtime context for using PotExtractor with 'with' statement."""
        if self.pot_file and os.path.exists(self.pot_file):
            self.catalog.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context and save changes if no exception occurred."""
        if exc_type is None:  # No exception occurred
            self.save()

    def _init_pot_metadata(self):
        """Initialize POT file metadata."""
        now = datetime.datetime.now()
        creation_date = now.strftime("%Y-%m-%d %H:%M%z")

        self.catalog.metadata.update({
            METADATA_KEYS["PROJECT_ID_VERSION"]: "PROJECT VERSION",
            METADATA_KEYS["REPORT_MSGID_BUGS_TO"]: "EMAIL@ADDRESS",
            METADATA_KEYS["POT_CREATION_DATE"]: creation_date,
            METADATA_KEYS["PO_REVISION_DATE"]: "YEAR-MO-DA HO:MI+ZONE",
            METADATA_KEYS["LAST_TRANSLATOR"]: "FULL NAME <EMAIL@ADDRESS>",
            METADATA_KEYS["LANGUAGE_TEAM"]: "LANGUAGE <LL@li.org>",
            METADATA_KEYS["MIME_VERSION"]: "1.0",
            METADATA_KEYS["CONTENT_TYPE"]: "text/plain; charset=UTF-8",
            METADATA_KEYS["CONTENT_TRANSFER_ENCODING"]: "8bit",
        })

    def add_source_file(self, file_path):
        """Add a source file to extract strings from."""
        if os.path.isfile(file_path):
            self.source_files.append(file_path)

    def extract_messages(self):
        """Extract translatable strings from source files."""
        for file_path in self.source_files:
            print("Scanning {0} for translatable messages...".format(file_path))
            self.current_file = file_path
            try:
                if sys.version_info[0] >= 3:
                    with tokenize.open(file_path) as f:
                        tokens = list(tokenize.generate_tokens(f.readline))
                        self._process_tokens(tokens)
                else:
                    # Python 2.7 compatibility
                    with open(file_path, 'rb') as f:
                        tokens = list(tokenize.generate_tokens(f.readline))
                        self._process_tokens(tokens)
            except Exception as e:
                print("Error processing file {0}: {1}".format(file_path, str(e)))

    def _process_tokens(self, tokens):
        """Process tokens from source file."""
        for i, token in enumerate(tokens):
            # Python 2.7 compatibility: token is a tuple
            token_type = token[0]
            token_string = token[1]
            token_start = token[2]

            self.current_line = token_start[0]

            # Look for translation function calls
            if token_type == tokenize.NAME and token_string in DEFAULT_KEYWORDS:
                next_token = tokens[i + 1]
                next_type = next_token[0]
                next_string = next_token[1]

                if next_type == tokenize.OP and next_string == '(':
                    # Found a translation function call
                    string_token = tokens[i + 2]
                    string_type = string_token[0]
                    string_value = string_token[1]

                    if string_type == tokenize.STRING:
                        # Safely evaluate string literal without extra quotes
                        msgid = ast.literal_eval(string_value)
                        # Format location as filename:line_number
                        location = (
                            os.path.relpath(self.current_file),
                            self.current_line
                        )
                        self.catalog.add(
                            msgid=msgid,
                            locations=[location]
                        )

    def save(self, project=None, version=None, copyright_holder=None, bugs_address=None):
        """Save extracted messages to POT file."""
        if not self.pot_file:
            raise ValueError("No POT file specified")

        # Update metadata
        if project:
            self.catalog.metadata[METADATA_KEYS["PROJECT_ID_VERSION"]] = "{0} {1}".format(project, version or '')
        if copyright_holder:
            # Set both COPYRIGHT and COPYRIGHT_HOLDER
            self.catalog.metadata[METADATA_KEYS["COPYRIGHT"]] = "Copyright (C) {0} {1}".format(
                datetime.datetime.now().year, copyright_holder
            )
            self.catalog.metadata[METADATA_KEYS["COPYRIGHT_HOLDER"]] = copyright_holder
        if bugs_address:
            self.catalog.metadata[METADATA_KEYS["REPORT_MSGID_BUGS_TO"]] = bugs_address

        # Write header comment
        year = datetime.datetime.now().year
        project_name = project or "PROJECT"
        header = [
            "# Translation template for {0}.".format(project_name),
            "# Copyright (C) {0} {1}".format(year, copyright_holder or 'ORGANIZATION'),
            "# This file is distributed under the same license as the {0} project.".format(project_name),
            "# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.",
            "#",
            "#, fuzzy"
        ]
        self.catalog._header_comment = "\n".join(header)

        # Save the POT file
        self.catalog.save(self.pot_file)

    def create_language_catalogs(self, languages, locales_dir):
        """Create or update PO catalogs for specified languages.
        
        Args:
            languages: List of language codes to generate catalogs for
            locales_dir: Base directory for locale files
        """
        if not os.path.exists(self.pot_file):
            raise ValueError("POT file not found")

        # Load the POT file
        pot = POFile(self.pot_file)
        pot.load()

        for lang in languages:
            # Create language directory
            lang = normalize_locale(lang)
            lang_dir = os.path.join(locales_dir, lang, "LC_MESSAGES")
            if not os.path.exists(lang_dir):
                os.makedirs(lang_dir)

            # Create or update PO file
            po_file = os.path.join(lang_dir, "messages.po")
            po = POFile(po_file)
            
            # If PO file exists, load it to preserve translations
            if os.path.exists(po_file):
                po.load()
            
            # Update metadata for this language
            metadata = pot.metadata.copy()
            metadata["Language"] = lang
            po.update_metadata(metadata)
            
            # Update messages from POT
            for key, message in pot.translations.items():
                if key in po.translations:
                    # Preserve existing translation
                    existing = po.translations[key]
                    existing.locations = message.locations
                    existing.auto_comments = message.auto_comments
                    existing.flags = message.flags
                else:
                    # Add new untranslated message
                    po.add(
                        msgid=message.msgid,
                        msgstr="",
                        locations=message.locations,
                        auto_comments=message.auto_comments,
                        user_comments=message.user_comments,
                        context=message.context,
                        flags=message.flags
                    )
            
            # Save the updated PO file
            po.save()
