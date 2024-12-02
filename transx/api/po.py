#!/usr/bin/env python
"""PO file format handler for TransX."""
from __future__ import unicode_literals

# Import built-in modules
import datetime
import os
import re
try:
    from collections import OrderedDict
except ImportError:
    # Python 2.6 compatibility
    from ordereddict import OrderedDict
import sys
import time

# Import local modules
from transx.constants import (
    DEFAULT_CHARSET,
    DEFAULT_ENCODING,
    DEFAULT_METADATA,
    METADATA_KEYS,
    MSGCTXT_PREFIX,
    MSGID_PREFIX,
    MSGSTR_PREFIX,
    REFERENCE_COMMENT_PREFIX,
    TRANSLATOR_COMMENT_PREFIX,
)
from transx.api.translators import DummyTranslator
from transx.api.message import Message


# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode
    binary_type = str
else:
    text_type = str
    binary_type = bytes


class POFile(object):
    """Class representing a PO file."""

    def __init__(self, path=None, locale=None):
        """Initialize a new PO file handler.

        Args:
            path: Path to the PO file
            locale: Locale code (e.g., 'en_US', 'zh_CN')
        """
        self.path = path
        self.locale = locale
        self.translations = OrderedDict()
        self.metadata = OrderedDict()
        self._init_metadata()

    def _get_key(self, msgid, context=None):
        """Get the key for storing a message.
        
        Args:
            msgid: The message ID
            context: The message context
            
        Returns:
            tuple: A tuple of (msgid, context)
        """
        return (msgid, context)

    def _init_metadata(self):
        """Initialize default metadata."""
        self.metadata = OrderedDict()
        self.metadata.update(DEFAULT_METADATA)
        if self.locale:
            self.metadata['Language'] = self.locale

    def update_metadata(self, new_metadata):
        """Update metadata without duplicating entries.
        
        Args:
            new_metadata: New metadata to merge
        """
        # Clear any existing metadata first to prevent duplication
        self.metadata.clear()
        self._init_metadata()
        
        # Update with new metadata
        if new_metadata:
            self.metadata.update(new_metadata)

    def parse_header(self, header):
        """Parse the header into a dictionary."""
        headers = OrderedDict()
        for line in header.split('\\n'):
            if not line:
                continue
            try:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
            except ValueError:
                continue
        return headers

    def load(self, file=None):
        """Load messages from a PO file."""
        if file is None and self.path:
            file = open(self.path, 'r', encoding=DEFAULT_ENCODING)

        try:
            # Reset translations but keep metadata
            self.translations = OrderedDict()
            current = None

            for line in file:
                line = line.strip()
                if not line:
                    if current and current.msgid is not None:
                        key = self._get_key(current.msgid, current.context)
                        self.translations[key] = current
                    current = Message(msgid="")  # Initialize with empty msgid
                    continue

                if line.startswith('#: '):
                    # Reference comment
                    if not current:
                        current = Message(msgid="")  # Initialize with empty msgid
                    for loc in line[3:].strip().split():
                        try:
                            if ':' in loc:
                                filename, lineno = loc.rsplit(':', 1)
                                current.add_location(filename, int(lineno))
                            else:
                                current.add_location(loc, 0)
                        except (ValueError, AttributeError):
                            # If location is malformed, just store it as is
                            current.add_location(loc, 0)
                elif line.startswith('#,'):
                    # Flag comment
                    if not current:
                        current = Message(msgid="")  # Initialize with empty msgid
                    for flag in line[2:].strip().split(','):
                        current.flags.add(flag.strip())  # Use set.add() instead of non-existent add_flag()
                elif line.startswith('#.'):
                    # Auto comment
                    if not current:
                        current = Message(msgid="")  # Initialize with empty msgid
                    current.auto_comments.append(line[2:].strip())  # Directly append to list
                elif line.startswith('# '):
                    # User comment
                    if not current:
                        current = Message(msgid="")  # Initialize with empty msgid
                    current.user_comments.append(line[2:])  # Directly append to list
                elif line.startswith('msgctxt'):
                    if not current:
                        current = Message(msgid="")  # Initialize with empty msgid
                    current.context = self._unescape_string(line[7:].strip())
                elif line.startswith('msgid'):
                    if not current:
                        current = Message(msgid="")  # Initialize with empty msgid
                    current.msgid = self._unescape_string(line[5:].strip())
                elif line.startswith('msgstr'):
                    if current:
                        current.msgstr = self._unescape_string(line[6:].strip())
                        if current.msgid == "":
                            # Parse header and update metadata
                            new_metadata = self.parse_header(current.msgstr)
                            self.update_metadata(new_metadata)
                            current.metadata = self.metadata.copy()
                elif line.startswith('"'):
                    # Continuation line
                    if current:
                        if hasattr(current, '_tmp_attr'):
                            setattr(current, current._tmp_attr,
                                    getattr(current, current._tmp_attr) + self._unescape_string(line))
                        else:
                            current.msgstr += self._unescape_string(line)

            # Add any remaining message
            if current and current.msgid is not None:
                key = self._get_key(current.msgid, current.context)
                self.translations[key] = current

        finally:
            if file is not self.path:
                file.close()

    def _unescape_string(self, text):
        """Convert a string from PO format.
        
        Args:
            text: String to unescape
            
        Returns:
            Unescaped string
        """
        if not text:
            return ""
            
        # Handle quoted strings
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
            
        # Convert to unicode if needed
        if isinstance(text, bytes):
            text = text.decode('utf-8')
            
        # Handle escape sequences
        result = []
        i = 0
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                if text[i + 1] == 'n':
                    result.append('\n')
                    i += 2
                elif text[i + 1] == 't':
                    result.append('\t')
                    i += 2
                elif text[i + 1] == 'r':
                    result.append('\r')
                    i += 2
                elif text[i + 1] == '\\':
                    result.append('\\')
                    i += 2
                elif text[i + 1] == '"':
                    result.append('"')
                    i += 2
                else:
                    result.append(text[i])
                    i += 1
            else:
                result.append(text[i])
                i += 1
                
        return ''.join(result)

    def _escape_string(self, text):
        """Convert a string to PO format.
        
        Args:
            text: String to escape
            
        Returns:
            Escaped string
        """
        if not text:
            return ""
            
        # Convert to unicode if needed
        if isinstance(text, bytes):
            text = text.decode('utf-8')
            
        # Handle escape sequences
        result = []
        for char in text:
            if char == '\n':
                result.append('\\n')
            elif char == '\t':
                result.append('\\t')
            elif char == '\r':
                result.append('\\r')
            elif char == '\\':
                result.append('\\\\')
            elif char == '"':
                result.append('\\"')
            else:
                result.append(char)
                
        return ''.join(result)

    def get(self, msgid, context=None):
        """Get a message from the catalog."""
        key = self._get_key(msgid, context)
        return self.translations.get(key)

    def update(self, pot_file, no_fuzzy_matching=False):
        """Update translations from a POT file."""
        if isinstance(pot_file, str):
            pot = POFile(pot_file)
            pot.load()
        else:
            pot = pot_file

        # Keep track of obsolete messages
        obsolete = {}

        # Update metadata from POT file while preserving existing translations
        header_key = self._get_key("", None)
        if header_key in pot.translations:
            pot_header = pot.translations[header_key]
            pot_metadata = self.parse_header(pot_header.msgstr)
            
            if header_key not in self.translations:
                # If no header exists, create one from the POT file
                self.translations[header_key] = Message(
                    msgid="",
                    msgstr="",
                    metadata=pot_metadata.copy()
                )
                self.metadata.clear()
                self.metadata.update(pot_metadata)
            else:
                # Update only non-translation metadata fields
                for key, value in pot_metadata.items():
                    if key not in self.metadata or not self.metadata[key].strip():
                        self.metadata[key] = value
                # Update header message metadata
                self.translations[header_key].metadata = self.metadata.copy()

            # Update header message with current metadata
            header_lines = []
            for key, value in self.metadata.items():
                header_lines.append(f"{key}: {value}")
            self.translations[header_key].msgstr = "\n".join(header_lines) + "\n"

        # Update messages that are in both catalogs
        for key, pot_message in pot.translations.items():
            if key == header_key:  # Skip header
                continue
            if key in self.translations:
                message = self.translations[key]
                message.locations = pot_message.locations
                message.auto_comments = pot_message.auto_comments
                if not no_fuzzy_matching:
                    message.flags = pot_message.flags
            else:
                # Add new message
                self.translations[key] = pot_message.clone()
                self.translations[key].msgstr = ""

        # Find obsolete messages
        for key, message in list(self.translations.items()):
            if key not in pot.translations and key != header_key:  # Don't remove header
                obsolete[key] = message
                del self.translations[key]

        return obsolete

    def add(self, msgid, msgstr="", locations=None, auto_comments=None, user_comments=None, context=None, flags=None):
        """Add a new message to the catalog.

        Args:
            msgid: The message ID (source text)
            msgstr: The message translation
            locations: List of (filename, line) tuples
            auto_comments: List of automatic comments
            user_comments: List of translator comments
            context: Message context
            flags: Set of flags (e.g., 'fuzzy')
        """
        key = self._get_key(msgid, context)
        if key in self.translations:
            message = self.translations[key]
            # Update existing message
            if locations:
                message.locations.extend(locations)
            if auto_comments:
                message.auto_comments.extend(auto_comments)
            if user_comments:
                message.user_comments.extend(user_comments)
            if flags:
                message.flags.update(flags)
        else:
            # Create new message
            message = Message(
                msgid=msgid,
                msgstr=msgstr,
                context=context,
                locations=locations or [],
                flags=flags or set(),
                auto_comments=auto_comments or [],
                user_comments=user_comments or []
            )
            self.translations[key] = message

    def save(self, file=None):
        """Save the catalog to a file.

        Args:
            file: Optional file path to save to. If not provided, uses self.path
        """
        if file is None:
            file = self.path
        if not file:
            raise ValueError("No file path provided")

        with open(file, 'w', encoding=DEFAULT_ENCODING) as f:
            # Write header with metadata
            f.write('msgid ""\n')
            f.write('msgstr ""\n')
            
            # Write metadata in a sorted order to maintain consistency
            for key in sorted(self.metadata.keys()):
                value = self.metadata[key]
                if value:  # Only write non-empty values
                    f.write('"{}: {}\\n"\n'.format(key, value))
            f.write('\n')

            # Write messages
            for message in self.translations.values():
                # Skip empty messages and metadata
                if not message.msgid:
                    continue

                # Write locations
                if message.locations:
                    for filename, lineno in message.locations:
                        f.write('#: {}:{}\n'.format(filename, lineno))

                # Write flags
                if message.flags:
                    f.write('#, {}\n'.format(', '.join(sorted(message.flags))))

                # Write auto comments
                for comment in message.auto_comments:
                    f.write('#. {}\n'.format(comment))

                # Write user comments
                for comment in message.user_comments:
                    f.write('# {}\n'.format(comment))

                # Write context if present
                if message.context is not None:
                    f.write('msgctxt "{}"\n'.format(self._escape_string(message.context)))

                # Write msgid and msgstr
                f.write('msgid "{}"\n'.format(self._escape_string(message.msgid)))
                f.write('msgstr "{}"\n'.format(self._escape_string(message.msgstr)))
                f.write('\n')

    def translate_entries(self, translator=None):
        # type: (BaseTranslator) -> None
        """Translate all untranslated entries using the provided translator.

        Args:
            translator (BaseTranslator, optional): Translator to use. If not provided,
                                                uses DummyTranslator.
        """
        translator = translator or DummyTranslator()
        target_lang = self.metadata.get(METADATA_KEYS["LANGUAGE"], "en")

        for message in self.translations.values():
            if not message.msgstr:  # Only translate empty entries
                try:
                    translated = translator.translate(
                        message.msgid,
                        source_lang="auto",
                        target_lang=target_lang
                    )
                    message.msgstr = translated
                    print(f"Translated: {message.msgid} -> {translated}")
                except Exception as e:
                    print(f"Failed to translate '{message.msgid}': {e!s}")

    def get_all_entries(self):
        """Get all translation entries.

        Returns:
            list: List of dictionaries containing msgid, msgstr, context and comments
                 for each translation entry.
        """
        entries = []
        for message in self.translations.values():
            entry = {
                'msgid': message.msgid,
                'msgstr': message.msgstr,
                'context': message.context,
                'comments': message.user_comments
            }
            entries.append(entry)
        return entries

    def get_entry(self, msgid, context=None):
        """Get a single translation entry with all its information.

        Args:
            msgid (str): Message ID to look up
            context (str, optional): Message context

        Returns:
            dict: Dictionary containing msgid, msgstr, context and comments
                 for the specified entry, or None if not found
        """
        key = self._get_key(msgid, context)
        if key in self.translations:
            message = self.translations[key]
            return {
                'msgid': message.msgid,
                'msgstr': message.msgstr,
                'context': message.context,
                'comments': message.user_comments
            }
        return None

    def iter_entries(self):
        """Iterate over all translation entries.

        Yields:
            tuple: (msgid, msgstr, context, comments) for each translation entry
        """
        for message in self.translations.values():
            yield message.msgid, message.msgstr, message.context, message.user_comments

    def merge_duplicates(self):
        """Merge duplicate messages by combining their locations and comments."""
        # Create a temporary dict to store merged messages
        merged = {}
        
        for key, message in self.translations.items():
            if key in merged:
                # Merge locations and comments
                existing = merged[key]
                existing.locations.extend(message.locations)
                existing.auto_comments.extend(message.auto_comments)
                existing.user_comments.extend(message.user_comments)
                existing.flags.update(message.flags)
                
                # Remove duplicates while preserving order
                existing.locations = list(dict.fromkeys(existing.locations))
                existing.auto_comments = list(dict.fromkeys(existing.auto_comments))
                existing.user_comments = list(dict.fromkeys(existing.user_comments))
            else:
                merged[key] = message
        
        # Update translations with merged messages
        self.translations = merged

    def __enter__(self):
        """Context manager entry point.
        
        Returns:
            POFile: The POFile instance with loaded translations
        """
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        if exc_type is None:  # Only save if no exception occurred
            self.save()
