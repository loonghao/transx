# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""PO file format handler for TransX."""
# Import future modules
# fmt: off
# isort: skip
# black: disable
from __future__ import unicode_literals

# Import built-in modules
# fmt: on
import codecs
import datetime
import errno
import logging
import os
import re


try:
    # Import built-in modules
    from collections import OrderedDict
except ImportError:
    # Python 2.6 compatibility
    from ordereddict import OrderedDict

# Import local modules
from transx.api.message import Message


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
        self.header_comment = ""  # Add header_comment attribute
        self._init_metadata()
        self.logger = logging.getLogger(__name__)

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
        now = datetime.datetime.now()
        year = now.year

        # Set default header comment
        self.header_comment = (
            "# Translations template for PROJECT.\n"
            "# Copyright (C) {} ORGANIZATION\n"
            "# This file is distributed under the same license as the PROJECT project.\n"
            "# FIRST AUTHOR <EMAIL@ADDRESS>, {}.\n"
            "#\n"
            "#, fuzzy"
        ).format(year, year)

        # Set default metadata
        self.metadata.update({
            "Project-Id-Version": "TransX Demo 1.0",
            "Report-Msgid-Bugs-To": "transx@example.com",
            "POT-Creation-Date": now.strftime("%Y-%m-%d %H:%M"),
            "PO-Revision-Date": "YEAR-MO-DA HO:MI+ZONE",
            "Last-Translator": "FULL NAME <EMAIL@ADDRESS>",
            "Language-Team": "LANGUAGE <LL@li.org>",
            "MIME-Version": "1.0",
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Transfer-Encoding": "8bit",
            "Generated-By": "TransX",
            "Copyright-Holder": "TransX Team"
        })

    def update_metadata(self, new_metadata):
        """Update metadata without duplicating entries.

        Args:
            new_metadata: New metadata to merge
        """
        # Update metadata dictionary
        self.metadata.update(new_metadata)

        # Update header message
        header_key = self._get_key("", None)
        if header_key not in self.translations:
            self.translations[header_key] = Message(msgid="", msgstr="")

        # Generate header content with quotes
        header_lines = []
        for key, value in self.metadata.items():
            if value:  # Only write non-empty values
                header_lines.append('"%s: %s\\n"' % (key, value))
        self.translations[header_key].msgstr = "\n".join(header_lines)

    def parse_header(self, header):
        """Parse the header into a dictionary.

        Args:
            header: Header string to parse

        Returns:
            OrderedDict: Parsed metadata
        """
        headers = OrderedDict()

        # First unescape the entire header
        header = self._unescape_string(header)

        # Split into lines and process each line
        lines = header.split("\\n")
        current_key = None
        current_value = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to parse as a header entry
            try:
                key, value = line.split(":", 1)
                if current_key:
                    # Save previous entry
                    headers[current_key] = "".join(current_value).strip()
                current_key = key.strip()
                current_value = [value.strip()]
            except ValueError:
                # If we can't split on ':', this might be a continuation of the previous value
                if current_key:
                    current_value.append(line)

        # Save last entry
        if current_key:
            headers[current_key] = "".join(current_value).strip()

        return headers

    def load(self, file=None):
        """Load messages from a PO file.

        Args:
            file: Optional file path to load from. If not provided, uses self.path
        """
        if file is None:
            file = self.path
        if file is None:
            raise ValueError("No file path specified")

        if not os.path.exists(file):
            return

        current_message = None
        current_locations = []
        current_flags = set()
        current_auto_comments = []
        current_user_comments = []
        current_msgid = []
        current_msgstr = []
        current_msgctxt = []
        reading_msgid = False
        reading_msgstr = False
        reading_msgctxt = False

        with codecs.open(file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                # Skip empty lines
                if not line:
                    if current_message is not None:
                        self._add_current_message(current_message)
                        current_message = None
                        current_locations = []
                        current_flags = set()
                        current_auto_comments = []
                        current_user_comments = []
                        current_msgid = []
                        current_msgstr = []
                        current_msgctxt = []
                        reading_msgid = False
                        reading_msgstr = False
                        reading_msgctxt = False
                    continue

                # Parse source references
                if line.startswith("#:"):
                    locations = line[2:].strip().split()
                    for location in locations:
                        if ":" in location:
                            filename, lineno = location.rsplit(":", 1)
                            try:
                                current_locations.append((filename.strip(), int(lineno.strip())))
                            except ValueError:
                                self.logger.warning("Invalid line number in location: %s", location)
                    continue

                # Parse flags
                if line.startswith("#,"):
                    flags = line[2:].strip().split(",")
                    current_flags.update(flag.strip() for flag in flags)
                    continue

                # Parse automatic comments
                if line.startswith("#."):
                    current_auto_comments.append(line[2:].strip())
                    continue

                # Parse user comments
                if line.startswith("#") and not line.startswith("#:") and not line.startswith("#,") and not line.startswith("#."):
                    current_user_comments.append(line[1:].strip())
                    continue

                # Parse msgctxt
                if line.startswith("msgctxt "):
                    reading_msgctxt = True
                    reading_msgid = False
                    reading_msgstr = False
                    current_msgctxt = [self._unescape_string(line[8:])]
                    continue

                # Parse msgid
                if line.startswith("msgid "):
                    reading_msgctxt = False
                    reading_msgid = True
                    reading_msgstr = False
                    current_msgid = [self._unescape_string(line[6:])]
                    continue

                # Parse msgstr
                if line.startswith("msgstr "):
                    reading_msgctxt = False
                    reading_msgid = False
                    reading_msgstr = True
                    current_msgstr = [self._unescape_string(line[7:])]
                    current_message = Message(
                        msgid="".join(current_msgid),
                        msgstr="".join(current_msgstr),
                        context="".join(current_msgctxt),
                        locations=current_locations,
                        flags=current_flags,
                        auto_comments=current_auto_comments,
                        user_comments=current_user_comments
                    )
                    continue

                # Continue reading msgid/msgstr/msgctxt
                if reading_msgid:
                    current_msgid.append(self._unescape_string(line))
                elif reading_msgstr:
                    current_msgstr.append(self._unescape_string(line))
                elif reading_msgctxt:
                    current_msgctxt.append(self._unescape_string(line))

            # Add the last message if any
            if current_message is not None:
                self._add_current_message(current_message)

    def _add_current_message(self, message):
        """Helper method to add the current message to translations.

        Args:
            message: Message object to add
        """
        if not message:
            return

        if not message.msgid and message.msgstr:
            # Parse header metadata
            metadata = self.parse_header(message.msgstr)
            self.update_metadata(metadata)

            # Store the header message in translations with empty msgid
            key = self._get_key("", None)
            self.translations[key] = message
        else:
            # Add regular message to translations
            key = self._get_key(message.msgid, message.context)
            self.translations[key] = message

    def _parse_string(self, text):
        """Parse a string value from a PO file.

        Args:
            text: The string to parse

        Returns:
            str: The parsed string value
        """
        text = text.strip()
        if not text:
            return ""

        # Handle multiline strings
        if text.startswith('msgid "') or text.startswith('msgstr "'):
            text = text[7:]  # Remove msgid/msgstr prefix

        # Handle quoted strings
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]  # Remove outer quotes

        # Unescape special characters
        return self._unescape_string(text)

    def _unescape_string(self, string):
        """Unescape a quoted string."""
        if not string:
            return ""
        if string.startswith('"') and string.endswith('"'):
            string = string[1:-1]  # Remove surrounding quotes
        # Unescape special characters
        return string.encode("raw_unicode_escape").decode("unicode_escape")

    def _escape_string(self, text):
        """Escape a string value for writing to a PO file.

        Args:
            text: The string to escape

        Returns:
            str: The escaped string value
        """
        if not text:
            return '""'

        # If the string is already properly quoted, return it as is
        if text.startswith('"') and text.endswith('"'):
            return text

        # Escape special characters
        text = text.replace("\\", "\\\\")  # Must be first
        text = text.replace("\n", "\\n")
        text = text.replace("\r", "\\r")
        text = text.replace("\t", "\\t")
        text = text.replace('"', '\\"')

        # Add quotes
        return '"%s"' % text

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

        # Update metadata from POT file
        self.metadata.update(pot.metadata)

        # Update messages that are in both catalogs
        for key, pot_message in pot.translations.items():
            if not pot_message.msgid:  # Skip header
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
            if key not in pot.translations and message.msgid:  # Don't remove non-header messages
                obsolete[key] = message
                del self.translations[key]

        # Update header message
        header_key = self._get_key("", None)
        if header_key not in self.translations:
            self.translations[header_key] = Message(msgid="", msgstr="")

        # Update header message with current metadata
        header_lines = []
        for key, value in self.metadata.items():
            header_lines.append("%s: %s\\n" % (key, value))  # Use \n instead of \\n
        self.translations[header_key].msgstr = "".join(header_lines)  # Don't add extra \n

        return obsolete

    def add(self, msgid, msgstr="", locations=None, flags=None, auto_comments=None,
            user_comments=None, context=None, metadata=None):
        """Add a message to the catalog.

        Args:
            msgid: The message ID
            msgstr: The translated string
            locations: List of (filename, line) tuples
            flags: Set of flags
            auto_comments: List of automatic comments
            user_comments: List of user comments
            context: String context for disambiguation
            metadata: Dictionary of metadata key/value pairs

        Returns:
            Message: The added message
        """
        # Create a new message
        message = Message(msgid=msgid, msgstr=msgstr, context=context)

        # Add locations
        if locations:
            message.locations.extend(locations)

        # Add flags
        if flags:
            message.flags.update(flags)

        # Add comments
        if auto_comments:
            message.auto_comments.extend(auto_comments)
        if user_comments:
            message.user_comments.extend(user_comments)

        # Update metadata
        if metadata:
            self.update_metadata(metadata)

        # Add to translations using msgid and context as key
        key = self._get_key(msgid, context)
        if key in self.translations:
            # If message already exists, merge locations and comments
            existing = self.translations[key]
            existing.locations.extend(message.locations)
            existing.flags.update(message.flags)
            existing.auto_comments.extend(message.auto_comments)
            existing.user_comments.extend(message.user_comments)
            message = existing
        else:
            self.translations[key] = message

        return message

    def save(self, file=None):
        """Save the catalog to a file.

        Args:
            file: Optional file path to save to. If not provided, uses self.path
        """
        if file is None:
            file = self.path
        if file is None:
            raise ValueError("No file path specified")

        # Create parent directories if they don't exist
        dirname = os.path.dirname(file)
        if dirname and not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        # Open file in text mode with utf-8 encoding
        with codecs.open(file, "w", encoding="utf-8") as f:
            # Write header comments first
            if self.header_comment:
                # Remove any trailing newlines to avoid extra blank lines
                header_comment = self.header_comment.rstrip()
                f.write(header_comment)
                f.write("\n\n")  # Add exactly two newlines after header comments

            # Write empty msgid/msgstr for metadata
            f.write('msgid ""\n')
            f.write('msgstr ""\n')

            # Write metadata in a specific order
            metadata_lines = []
            ordered_metadata = [
                "Project-Id-Version",
                "Report-Msgid-Bugs-To",
                "POT-Creation-Date",
                "PO-Revision-Date",
                "Last-Translator",
                "Language-Team",
                "Language",
                "MIME-Version",
                "Content-Type",
                "Content-Transfer-Encoding",
                "Generated-By",
                "Copyright-Holder",
            ]

            # First write ordered metadata
            for key in ordered_metadata:
                if self.metadata.get(key):
                    metadata_lines.append('"%s: %s\\n"' % (key, self.metadata[key]))

            # Then write any remaining metadata
            for key, value in self.metadata.items():
                if key not in ordered_metadata and value:
                    metadata_lines.append('"%s: %s\\n"' % (key, value))

            f.write("\n".join(metadata_lines))
            f.write("\n\n")

            # Write all other messages
            for message in self.translations.values():
                if message.msgid:  # Skip header message
                    self._write_message(message, f)
                    f.write("\n")  # Add a newline after each message

    def _normalize_path(self, path):
        """Normalize a file path for writing to PO file.

        Args:
            path: The file path to normalize

        Returns:
            str: The normalized path
        """
        # Convert to forward slashes for consistency
        path = path.replace("\\", "/")
        # Remove any '..' path components
        parts = path.split("/")
        normalized_parts = []
        for part in parts:
            if part == "..":
                if normalized_parts:
                    normalized_parts.pop()
            elif part and part != ".":
                normalized_parts.append(part)
        return "/".join(normalized_parts)

    def _write_message(self, message, file):
        """Write a single message to the file."""
        # Write auto comments
        for comment in message.auto_comments:
            file.write("#. %s\n" % comment)

        # Write locations
        if message.locations:
            # Sort locations by filename and line number
            sorted_locations = sorted(message.locations, key=lambda x: (x[0], x[1]))
            # Write each location on a separate line
            for filename, lineno in sorted_locations:
                normalized_path = self._normalize_path(filename)
                file.write("#: %s:%s\n" % (normalized_path, lineno))

        # Write flags
        if message.flags:
            file.write("#, %s\n" % ", ".join(sorted(message.flags)))

        # Write user comments
        for comment in message.user_comments:
            file.write("# %s\n" % comment)

        # Write msgctxt if present
        if message.context is not None:
            file.write("msgctxt %s\n" % self._escape_string(message.context))

        # Write msgid
        file.write("msgid %s\n" % self._escape_string(message.msgid))

        # Write msgstr
        file.write("msgstr %s\n\n" % self._escape_string(message.msgstr))

    def _generate_header(self):
        """Generate the header string with metadata."""
        # First generate an empty msgid
        header = 'msgid ""\n'

        # Then add metadata
        metadata_lines = []
        # 使用OrderedDict去重并保持顺序
        unique_metadata = OrderedDict()
        for key, value in self.metadata.items():
            if value and key not in unique_metadata:  # Only write non-empty values and skip duplicates
                unique_metadata[key] = value
        for key, value in unique_metadata.items():
            metadata_lines.append("%s: %s\\n" % (key, value))

        # Join metadata lines and wrap in quotes
        header += 'msgstr ""\n'
        if metadata_lines:
            header += '"%s"' % "".join(metadata_lines)

        return header

    def get_message(self, msgid, context=None):
        """Get a message by its ID and optional context.

        Args:
            msgid: The message ID
            context: Optional message context

        Returns:
            Message: The message object if found, None otherwise
        """
        key = self._get_key(msgid, context)
        return self.translations.get(key)

    def get_all_entries(self):
        """Get all translation entries.

        Returns:
            list: List of dictionaries containing msgid, msgstr, context and comments
                 for each translation entry.
        """
        entries = []
        for message in self.translations.values():
            entry = {
                "msgid": message.msgid,
                "msgstr": message.msgstr,
                "context": message.context,
                "comments": message.user_comments
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
                "msgid": message.msgid,
                "msgstr": message.msgstr,
                "context": message.context,
                "comments": message.user_comments
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

    def gettext(self, msgid):
        """Get the translation for a message.

        Args:
            msgid: The message ID to translate

        Returns:
            str: The translated string, or msgid if not found
        """
        key = self._get_key(msgid)
        if key in self.translations:
            return self.translations[key].msgstr
        return msgid

    def ngettext(self, msgid1, msgid2, n):
        """Get the plural translation for a message.

        Args:
            msgid1: The singular message ID
            msgid2: The plural message ID
            n: The number determining plural form

        Returns:
            str: The translated string, or msgid1/msgid2 based on n
        """
        key = self._get_key(msgid1)
        if key in self.translations and self.translations[key].msgstr_plural:
            # Get the correct plural form based on n
            # For now, we just use a simple plural rule
            plural_form = 0 if n == 1 else 1
            if plural_form < len(self.translations[key].msgstr_plural):
                return self.translations[key].msgstr_plural[plural_form]
        return msgid1 if n == 1 else msgid2

    def _preserve_placeholders(self, text):
        """Preserve format placeholders during translation.

        Args:
            text: Text containing format placeholders

        Returns:
            tuple: (processed_text, placeholders)
            where placeholders is a dict mapping temp markers to original placeholders
        """
        placeholders = {}

        # Handle both {name} and ${name} style placeholders
        pattern = r"(\$?\{[^}]+\})"

        def replace(match):
            placeholder = match.group(1)
            marker = "__PH%d__" % len(placeholders)
            placeholders[marker] = placeholder
            return marker

        processed = re.sub(pattern, replace, text)
        return processed, placeholders

    def _restore_placeholders(self, text, placeholders):
        """Restore format placeholders after translation.

        Args:
            text: Text with placeholder markers
            placeholders: Dict mapping markers to original placeholders

        Returns:
            str: Text with original placeholders restored
        """
        result = text
        for marker, placeholder in placeholders.items():
            result = result.replace(marker, placeholder)
        return result

    def _preserve_special_chars(self, text):
        """Preserve special characters and escape sequences during translation.

        Args:
            text: Text containing special characters

        Returns:
            tuple: (processed_text, special_chars)
            where special_chars is a dict mapping temp markers to original chars
        """
        special_chars = {}
        processed = text

        # Define patterns for special characters and sequences
        patterns = [
            (r'\\[\\"]', "ESCAPED"),      # Escaped backslash and quotes: \\ \"
            (r"\\[nrt]", "ESCAPED"),      # Common escape sequences: \n \r \t
            (r"\\[0-7]{1,3}", "ESCAPED"), # Octal escapes: \123
            (r"\\x[0-9a-fA-F]{2}", "ESCAPED"),  # Hex escapes: \xFF
            (r"\\u[0-9a-fA-F]{4}", "ESCAPED"),  # Unicode escapes: \u00FF
            (r"\\U[0-9a-fA-F]{8}", "ESCAPED"),  # Long Unicode escapes: \U0001F600
            (r'"[^"]*"', "QUOTED"),       # Quoted strings: "hello"
            (r"&quot;.*?&quot;", "QUOTED"),  # HTML quotes: &quot;hello&quot;
            (r"\$?\{[^}]+\}", "PLACEHOLDER"),  # Format placeholders: {name} or ${name}
        ]

        for pattern, type_ in patterns:
            def replace(match, current_type=type_):
                original = match.group(0)
                marker = "__%s%d__" % (current_type, len(special_chars))
                special_chars[marker] = original
                return marker

            processed = re.sub(pattern, replace, processed)

        return processed, special_chars

    def _restore_special_chars(self, text, special_chars):
        """Restore special characters after translation.

        Args:
            text: Text with special character markers
            special_chars: Dict mapping markers to original chars

        Returns:
            str: Text with original special characters restored
        """
        result = text

        # Sort markers by length (longest first) to avoid partial replacements
        markers = sorted(special_chars.keys(), key=len, reverse=True)

        for marker in markers:
            result = result.replace(marker, special_chars[marker])

        return result

    def translate_messages(self, translator, target_lang=None):
        """Translate untranslated messages using the provided translator.

        Args:
            translator: Translator instance to use
            target_lang: Target language code. If None, uses metadata language

        Returns:
            int: Number of messages translated
        """
        if not target_lang:
            target_lang = self.metadata.get("Language", "en")

        translated_count = 0

        for message in self.translations.values():
            if not message.msgstr and message.msgid:  # Skip empty msgid
                try:
                    # Preserve special characters and placeholders
                    text_to_translate, special_chars = self._preserve_special_chars(message.msgid)

                    # Translate text with preserved characters
                    translated = translator.translate(
                        text_to_translate,
                        source_lang="auto",
                        target_lang=target_lang
                    )

                    if translated:
                        # Restore special characters
                        message.msgstr = self._restore_special_chars(translated, special_chars)
                        translated_count += 1

                except Exception as e:
                    self.logger.error("Failed to translate '%s': %s", message.msgid, str(e))
                    continue

        return translated_count

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
