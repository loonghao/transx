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
                self.current_line = start[0]  # Update current line number
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
                    if func_name == "pgettext":
                        # pgettext(context, msgid)
                        if len(args) >= 2:
                            context, msgid = args[0], args[1]
                            if not self._should_skip_string(msgid):
                                msg = Message(msgid=msgid, context=context)
                                self._add_message(msg, start[0])
                    elif func_name == "tr":
                        # tr(msgid, context=context)
                        if args:
                            msgid = args[0]
                            context = kwargs.get("context")  # Get context from kwargs
                            if not self._should_skip_string(msgid):
                                msg = Message(msgid=msgid, context=context)
                                self._add_message(msg, start[0])
                    elif func_name in ("ngettext", "ungettext", "dngettext", "npgettext"):
                        # Handle plural forms
                        if len(args) >= 2:
                            singular, plural = args[0], args[1]
                            context = args[2] if len(args) > 2 and func_name == "npgettext" else None
                            if not self._should_skip_string(singular):
                                msg = Message(msgid=singular, msgid_plural=plural, context=context)
                                self._add_message(msg, start[0])
                    else:
                        # Handle simple gettext functions
                        if args and not self._should_skip_string(args[0]):
                            msg = Message(msgid=args[0])
                            self._add_message(msg, start[0])
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
        # Add location information
        location = (self.current_file, line)
        
        # Check if this message already exists
        key = self.catalog._get_key(message.msgid, message.context)
        if key in self.catalog.translations:
            # Get existing message
            existing = self.catalog.translations[key]
            # Add new location if not already present
            if location not in existing.locations:
                existing.locations.append(location)
                existing.locations.sort()  # Sort locations for consistent output
            # Update comments and flags
            existing.flags.update(message.flags)
            for comment in message.auto_comments:
                if comment not in existing.auto_comments:
                    existing.auto_comments.append(comment)
            for comment in message.user_comments:
                if comment not in existing.user_comments:
                    existing.user_comments.append(comment)
        else:
            # Add new message with location
            message.locations = [location]
            self.catalog.translations[key] = message

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
        
        # Load the POT file
        self.pot_catalog = POFile(pot_file)
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
            po_file = os.path.join(locale_dir, "messages.po")
            po = POFile(po_file)

            # Load existing translations if any
            existing_translations = {}
            if os.path.exists(po_file):
                po.load()
                for key, message in po.translations.items():
                    if message.msgid:  # Skip header
                        existing_translations[key] = message

            # Start with a fresh catalog
            po.translations.clear()

            # Copy POT header comments and metadata
            po.header_comment = self.pot_catalog.header_comment
            po.metadata = self.pot_catalog.metadata.copy()
            po.metadata["Language"] = lang

            # First add the header message (empty msgid)
            header_key = po._get_key("", None)
            if header_key in self.pot_catalog.translations:
                header_message = self.pot_catalog.translations[header_key]
                po.translations[header_key] = Message(
                    msgid=header_message.msgid,
                    msgstr="",
                    flags=header_message.flags,
                    auto_comments=header_message.auto_comments,
                    user_comments=header_message.user_comments
                )

            # Then add all other messages
            for key, message in self.pot_catalog.translations.items():
                if message.msgid:  # Skip header message
                    existing_message = existing_translations.get(key)
                    # Create a new message with all attributes from POT
                    new_message = Message(
                        msgid=message.msgid,
                        msgstr=existing_message.msgstr if existing_message else "",
                        flags=message.flags.copy(),
                        auto_comments=message.auto_comments[:],
                        user_comments=message.user_comments[:],
                        context=message.context
                    )
                    
                    # Copy locations exactly as they are in POT
                    if message.locations:
                        new_message.locations = message.locations[:]
                    
                    # Add to PO file using the same key as POT
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
        previous = {}
        for msg in po.translations.values():
            key = (msg.msgid, msg.context)  # Use both msgid and context as key
            previous[key] = msg.msgstr
        po.translations.clear()

        # Copy messages from POT file
        for key, message in self.pot_catalog.translations.items():
            if not key[0]:  # Skip header (empty msgid)
                continue

            # Create a new message in the PO file
            po_message = po.add(
                msgid=message.msgid,
                msgstr=previous.get((message.msgid, message.context), ""),  # Restore previous translation if available
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

        # Start with metadata from POT file
        metadata = OrderedDict()
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

        # Update the catalog's metadata using update_metadata
        po_catalog.update_metadata(metadata)
