#!/usr/bin/env python
"""POT file format handler for TransX."""
from __future__ import unicode_literals

# Import built-in modules
import datetime
import os
import tokenize

try:
    from collections import OrderedDict
except ImportError:
    # Python 2.6 compatibility
    from ordereddict import OrderedDict

from transx.api.locale import normalize_language_code
from transx.api.message import Message
from transx.api.po import POFile
from transx.compat import PY2, safe_eval_string, tokenize_source

# Import local modules
from transx.constants import (
    DEFAULT_KEYWORDS,
    LANGUAGE_CODES,
)


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
        # Only load existing POT file if we're extracting messages
        if self.source_files and self.pot_file and os.path.exists(self.pot_file):
            self.catalog.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context and save changes if no exception occurred."""
        if exc_type is None and self.source_files:  # Only save if we're extracting messages
            self.save_pot()

    def _init_pot_metadata(self):
        """Initialize POT file metadata."""
        now = datetime.datetime.now()
        year = now.year
        creation_date = now.strftime("%Y-%m-%d %H:%M%z")

        # Add header comments
        self.catalog.header_comment = (
            "# Translations template for PROJECT.\n"
            "# Copyright (C) {} ORGANIZATION\n"
            "# This file is distributed under the same license as the PROJECT project.\n"
            "# FIRST AUTHOR <EMAIL@ADDRESS>, {}.\n"
            "#\n"
            "#, fuzzy\n"
        ).format(year, year)

        self.catalog.metadata.update({
            "Project-Id-Version": "PROJECT VERSION",
            "Report-Msgid-Bugs-To": "EMAIL@ADDRESS",
            "POT-Creation-Date": creation_date,
            "PO-Revision-Date": "YEAR-MO-DA HO:MI+ZONE",
            "Last-Translator": "FULL NAME <EMAIL@ADDRESS>",
            "Language-Team": "LANGUAGE <LL@li.org>",
            "MIME-Version": "1.0",
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Transfer-Encoding": "8bit",
            "Generated-By": "TransX",
        })

    def add_source_file(self, file_path):
        """Add a source file to extract strings from."""
        if os.path.isfile(file_path):
            self.source_files.append(file_path)

    def extract_messages(self):
        """Extract translatable strings from source files."""
        for file_path in self.source_files:
            print("Scanning %s for translatable messages..." % file_path)
            self.current_file = file_path
            self.current_line = 0

            try:
                if PY2:
                    with open(file_path, "rb") as f:
                        content = f.read().decode("utf-8")
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                self._process_tokens(content)
            except IOError as e:
                print("Error reading file %s: %s" % (file_path, str(e)))
                continue

    def _process_tokens(self, content):
        """Process tokens from source file."""
        tokens = tokenize_source(content)
        tokens = list(tokens)  # Convert iterator to list for look-ahead
        
        i = 0
        while i < len(tokens):
            token_type, token_string, start, end, line = tokens[i]
            
            # Look for translation function calls
            if token_type == tokenize.NAME and token_string in DEFAULT_KEYWORDS:
                func_name = token_string
                # Skip the function name token
                i += 1
                if i >= len(tokens):
                    break
                    
                # Look for opening parenthesis
                token_type, token_string, start, end, line = tokens[i]
                if token_type == tokenize.OP and token_string == "(":
                    # Skip the opening parenthesis
                    i += 1
                    if i >= len(tokens):
                        break
                        
                    # Get arguments
                    args = []
                    kwargs = {}
                    while i < len(tokens):
                        token_type, token_string, start, end, line = tokens[i]
                        
                        # End of function call
                        if token_type == tokenize.OP and token_string == ")":
                            break
                            
                        # Handle keyword arguments
                        if token_type == tokenize.NAME:
                            if i + 1 < len(tokens) and tokens[i+1][1] == "=":
                                kwarg_name = token_string
                                i += 2  # Skip '=' token
                                if i < len(tokens) and tokens[i][0] == tokenize.STRING:
                                    kwargs[kwarg_name] = safe_eval_string(tokens[i][1])
                                i += 1
                                continue
                                
                        # Handle positional string arguments
                        if token_type == tokenize.STRING:
                            string_content = safe_eval_string(token_string)
                            if string_content is not None:
                                args.append(string_content)
                                
                        # Skip commas
                        if token_type == tokenize.OP and token_string == ",":
                            i += 1
                            continue
                            
                        i += 1
                        
                    # Process arguments based on function type
                    if func_name in ("tr", "pgettext"):
                        # Handle tr(msgid, context=context) and pgettext(context, msgid)
                        msgid = kwargs.get("msgid") or (args[0] if args else None)
                        if msgid and not self._should_skip_string(msgid):
                            self._add_message(msgid, start[0])
                            
                    elif func_name in ("ngettext", "ungettext", "dngettext", "npgettext"):
                        # Handle plural forms
                        singular = args[0] if args else None
                        plural = args[1] if len(args) > 1 else None
                        if singular and plural and not self._should_skip_string(singular):
                            # Add both singular and plural forms
                            msg = Message(msgid=singular, msgid_plural=plural)
                            self._add_message(msg, start[0])
                            
                    else:
                        # Handle simple gettext functions
                        if args and not self._should_skip_string(args[0]):
                            self._add_message(args[0], start[0])
            i += 1

    def _should_skip_string(self, string):
        """Check if a string should be skipped from translation.
        
        Args:
            string: String to check
            
        Returns:
            bool: True if string should be skipped
        """
        # Skip empty strings or whitespace only
        if not string or string.isspace():
            return True
            
        # Skip language codes using the full LANGUAGE_CODES dictionary
        for code, (name, aliases) in LANGUAGE_CODES.items():
            if string in [code] + aliases:
                return True
            
        # Skip directory names
        if string in ("locales", "LC_MESSAGES"):
            return True
            
        # Skip Python special names
        if string in ("__main__", "__init__", "__file__"):
            return True
            
        # Skip strings that are just separators/formatting
        if set(string).issubset({"=", "-", "_", "\n", " ", "."}):
            return True
            
        # Skip strings that are just numbers
        if string.replace(".", "").isdigit():
            return True
            
        # Skip URLs
        if string.startswith(("http://", "https://", "ftp://")):
            return True
            
        return False

    def _add_message(self, message, line):
        """Add a message to the catalog with location information.
        
        Args:
            message: Message to add
            line: Line number where message was found
        """
        # Get relative path from project root
        rel_path = os.path.relpath(
            self.current_file,
            os.path.dirname(os.path.dirname(self.pot_file))
        )
        
        # Add location using relative path
        location = (rel_path, line)
        
        # Only add location to locations list, not as auto_comments
        if message in self.catalog.translations:
            # Update existing message
            existing_msg = self.catalog.translations[message]
            if location not in existing_msg.locations:
                existing_msg.locations.append(location)
        else:
            # Add new message
            self.catalog.add(
                msgid=message,
                locations=[location]
            )

    def save_pot(self, project=None, version=None, copyright_holder=None, bugs_address=None):
        """Save POT file with project information.

        Args:
            project: Project name
            version: Project version
            copyright_holder: Copyright holder
            bugs_address: Email address for bug reports
        """
        # Update metadata
        if project:
            self.catalog.metadata["Project-Id-Version"] = "%s %s" % (project, version or "")
        if copyright_holder:
            self.catalog.metadata["Copyright-Holder"] = copyright_holder
        if bugs_address:
            self.catalog.metadata["Report-Msgid-Bugs-To"] = bugs_address

        # Save POT file
        self.catalog.save()


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

    def create_language_catalogs(self, languages):
        """Create or update PO catalogs for specified languages.
        
        Args:
            languages: List of language codes to generate catalogs for
        """
        if not os.path.exists(self.pot_file):
            raise ValueError("POT file not found")

        # Create a new POFile instance to read the POT file
        # This ensures we don't modify the original POT file
        pot = POFile(self.pot_file)
        pot.load()

        for lang in languages:
            # Create language directory
            lang = normalize_language_code(lang)
            lang_dir = os.path.join(self.locales_dir, lang, "LC_MESSAGES")
            if not os.path.exists(lang_dir):
                os.makedirs(lang_dir)

            # Create or update PO file
            po_file = os.path.join(lang_dir, "messages.po")
            po = POFile(po_file)
            
            # If PO file exists, load it to preserve translations
            existing_translations = {}
            if os.path.exists(po_file):
                po.load()
                # Save existing translations
                for key, message in po.translations.items():
                    if message.msgstr:  # Only save non-empty translations
                        existing_translations[key] = message.msgstr

            # Start fresh with POT metadata
            po.metadata = pot.metadata.copy()
            # Only update the language field
            po.metadata["Language"] = lang
            
            # Update messages from POT
            po.translations.clear()
            for key, message in pot.translations.items():
                # Create new message with POT data
                new_message = Message(
                    msgid=message.msgid,
                    msgstr=existing_translations.get(key, ""),  # Restore existing translation if available
                    locations=message.locations[:],  # Make a copy of locations
                    auto_comments=message.auto_comments[:],
                    user_comments=message.user_comments[:],
                    context=message.context,
                    flags=message.flags.copy()
                )
                po.translations[key] = new_message
            
            # Save the updated PO file
            po.save()

    def update_po_file(self, po_file, language):
        """Update a PO file with messages from the POT file.

        Args:
            po_file: Path to the PO file to update
            language: Language code for the PO file
        """
        # Create or load PO file
        po = POFile(po_file)
        if os.path.exists(po_file):
            po.load()

        # Update metadata
        self._update_po_metadata(po, language)

        # Clear existing translations but keep the previous ones for reference
        previous = {msg.msgid: msg.msgstr for msg in po.translations.values()}
        po.translations.clear()

        # Copy messages from POT file
        for msgid, message in self.pot_catalog.translations.items():
            if not msgid:  # Skip header
                continue

            # Create a new message in the PO file
            po_message = po.add(
                msgid,
                msgstr=previous.get(msgid, ""),  # Restore previous translation if available
                flags=message.flags,
                auto_comments=message.auto_comments,
                user_comments=message.user_comments,
                context=message.context,
            )

            # Copy locations from POT file
            if message.locations:
                # Sort locations by filename and line number
                sorted_locations = sorted(message.locations, key=lambda x: (x[0], x[1]))
                po_message.locations = sorted_locations
            
        # Save the updated PO file
        po.save()

    def _update_po_metadata(self, po_catalog, language):
        """Update PO file metadata based on POT metadata and language."""
        now = datetime.datetime.now()
        year = now.year
        revision_date = now.strftime("%Y-%m-%d %H:%M%z")

        # Get language display name
        language_name = {
            "en_US": "English (United States)",
            "zh_CN": "Chinese (Simplified)",
            "zh_TW": "Chinese (Traditional)",
        }.get(language, language)

        # Add header comments without fuzzy flag
        po_catalog.header_comment = (
            "# {} translations for PROJECT.\n"
            "# Copyright (C) {} ORGANIZATION\n"
            "# This file is distributed under the same license as the PROJECT project.\n"
            "# FIRST AUTHOR <EMAIL@ADDRESS>, {}.\n"
            "#\n"
        ).format(language_name, year, year)

        # Start with a fresh metadata dictionary
        metadata = OrderedDict()

        # Copy metadata from POT file
        for key, value in self.pot_catalog.metadata.items():
            if key not in ["Language", "Language-Team", "Plural-Forms", "PO-Revision-Date"]:
                metadata[key] = value

        # Update language-specific metadata
        metadata.update({
            "PO-Revision-Date": revision_date,
            "Language": language,
            "Language-Team": "{} <LL@li.org>".format(language),
            "Plural-Forms": "nplurals=1; plural=0;" if language.startswith("zh") else "nplurals=2; plural=(n != 1);",
        })

        # Update the catalog's metadata
        po_catalog.metadata = metadata
