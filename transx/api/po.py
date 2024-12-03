#!/usr/bin/env python
"""PO file format handler for TransX."""
from __future__ import unicode_literals

import codecs
import errno
import logging
import os
import re

# Import built-in modules

try:
    from collections import OrderedDict
except ImportError:
    # Python 2.6 compatibility
    from ordereddict import OrderedDict

from transx.api.message import Message
from transx.constants import DEFAULT_ENCODING, DEFAULT_METADATA, METADATA_KEYS


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
        self.metadata = OrderedDict()
        self.metadata.update(DEFAULT_METADATA)
        if self.locale:
            self.metadata["Language"] = self.locale

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
        """Parse the header into a dictionary.
        
        Args:
            header: Header string to parse
            
        Returns:
            OrderedDict: Parsed metadata
        """
        headers = OrderedDict()
        for line in header.split("\n"):
            line = line.rstrip("\\n")  # Remove trailing \n
            if not line:
                continue
            try:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
            except ValueError:
                continue
        return headers

    def load(self, file=None):
        """Load messages from a PO file."""
        if file is None:
            file = self.path

        if isinstance(file, (str, str)):
            file = codecs.open(file, "r", encoding=DEFAULT_ENCODING)

        try:
            current_message = None
            header_comment = []
            in_msgstr = False
            in_header = False

            for line in file:
                line = line.strip()

                # Skip empty lines
                if not line:
                    if current_message:
                        self._add_current_message(current_message, in_header)
                        current_message = None
                        in_header = False
                    continue

                # Parse header comments
                if line.startswith("#") and current_message is None:
                    header_comment.append(line)
                    continue

                # Parse message
                if line.startswith("msgid "):
                    if current_message:
                        self._add_current_message(current_message, in_header)
                    # Remove msgid prefix but keep quotes
                    msgid = line[6:].strip()
                    current_message = Message(msgid=self._parse_string(msgid))
                    in_msgstr = False
                    # Check if this is the header
                    if not current_message.msgid:
                        in_header = True
                    continue

                if line.startswith("msgstr "):
                    if current_message:
                        # Remove msgstr prefix but keep quotes
                        msgstr = line[7:].strip()
                        current_message.msgstr = self._parse_string(msgstr)
                        in_msgstr = True
                    continue

                # Parse string continuation
                if line.startswith('"') and line.endswith('"'):
                    if current_message:
                        if in_msgstr:
                            current_message.msgstr += self._parse_string(line)
                        else:
                            current_message.msgid += self._parse_string(line)
                    continue

                # Parse locations
                if line.startswith("#: "):
                    if current_message is None:
                        current_message = Message("")
                    for location in line[3:].strip().split():
                        if ":" in location:
                            filename, lineno = location.rsplit(":", 1)
                            try:
                                current_message.locations.append((filename, int(lineno)))
                            except ValueError:
                                self.logger.warning("Invalid line number in location: %s", location)
                    continue

                # Parse flags
                if line.startswith("#, "):
                    if current_message is None:
                        current_message = Message("")
                    flags = line[3:].strip().split(", ")
                    current_message.flags.update(flags)
                    continue

                # Parse auto comments
                if line.startswith("#. "):
                    if current_message is None:
                        current_message = Message("")
                    current_message.auto_comments.append(line[3:].strip())
                    continue

                # Parse user comments
                if line.startswith("# "):
                    if current_message is None:
                        current_message = Message("")
                    current_message.user_comments.append(line[2:].strip())
                    continue

                # Parse context
                if line.startswith("msgctxt "):
                    if current_message is None:
                        current_message = Message("")
                    current_message.context = self._parse_string(line[8:])
                    continue

            # Add the last message
            if current_message:
                self._add_current_message(current_message, in_header)

            # Store header comment
            if header_comment:
                self.header_comment = "\n".join(header_comment) + "\n"

        finally:
            if hasattr(file, "close"):
                file.close()

    def _add_current_message(self, message, in_header):
        """Helper method to add the current message to translations.
        
        Args:
            message: Message object to add
            in_header: Whether this is a header message
        """
        if not message:
            return
            
        if in_header and not message.msgid and message.msgstr:
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
            
        # Handle escape sequences
        result = []
        i = 0
        while i < len(text):
            if text[i] == "\\" and i + 1 < len(text):
                if text[i + 1] == "n":
                    result.append("\n")
                    i += 2
                elif text[i + 1] == "t":
                    result.append("\t")
                    i += 2
                elif text[i + 1] == "r":
                    result.append("\r")
                    i += 2
                elif text[i + 1] == "b":
                    result.append("\b")
                    i += 2
                elif text[i + 1] == "f":
                    result.append("\f")
                    i += 2
                elif text[i + 1] == '"':
                    result.append('"')
                    i += 2
                elif text[i + 1] == "\\":
                    result.append("\\")
                    i += 2
                else:
                    result.append(text[i])
                    i += 1
            else:
                result.append(text[i])
                i += 1
                
        return "".join(result)

    def _escape_string(self, text):
        """Escape a string value for writing to a PO file.

        Args:
            text: The string to escape

        Returns:
            str: The escaped string value
        """
        if not text:
            return '""'
            
        # Escape special characters
        text = text.replace("\\", "\\\\")  # Must be first
        text = text.replace('"', '\\"')
        text = text.replace("\n", "\\n")
        text = text.replace("\t", "\\t")
        text = text.replace("\r", "\\r")
        text = text.replace("\b", "\\b")
        text = text.replace("\f", "\\f")
        
        # Only add quotes if not already quoted
        if not (text.startswith('"') and text.endswith('"')):
            text = '"{}"'.format(text)
            
        return text

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
            
        # Handle escape sequences
        result = []
        i = 0
        while i < len(text):
            if text[i] == "\\" and i + 1 < len(text):
                if text[i + 1] == "n":
                    result.append("\n")
                    i += 2
                elif text[i + 1] == "t":
                    result.append("\t")
                    i += 2
                elif text[i + 1] == "r":
                    result.append("\r")
                    i += 2
                elif text[i + 1] == "b":
                    result.append("\b")
                    i += 2
                elif text[i + 1] == "f":
                    result.append("\f")
                    i += 2
                elif text[i + 1] == '"':
                    result.append('"')
                    i += 2
                elif text[i + 1] == "\\":
                    result.append("\\")
                    i += 2
                else:
                    result.append(text[i])
                    i += 1
            else:
                result.append(text[i])
                i += 1
                
        return "".join(result)

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
            header_lines.append("%s: %s\\n" % (key, value))  # Add explicit \n
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
        # Create new message
        message = Message(msgid=msgid)
        message.msgstr = msgstr
        message.context = context

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

        # Add to translations
        key = self._get_key(msgid, context)
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
        with codecs.open(file, 'w', encoding='utf-8') as f:
            if self.header_comment:
                f.write(self.header_comment)

            # Write header message
            header_msg = Message(
                msgid="",
                msgstr=self._generate_header(),
                auto_comments=["Translation file."]
            )
            self._write_message(f, header_msg)
            f.write("\n")

            # Write all other messages
            for message in self.translations.values():
                if message.msgid:  # Skip header message
                    self._write_message(f, message)
                    f.write("\n")

    def _write_message(self, f, message):
        """Write a single message to the file."""
        # Write auto comments
        for comment in message.auto_comments:
            f.write("#. %s\n" % comment)

        # Write user comments
        for comment in message.user_comments:
            f.write("# %s\n" % comment)

        # Write locations
        if message.locations:
            for filename, lineno in sorted(message.locations):
                f.write("#: %s:%d\n" % (filename, lineno))

        # Write flags
        if message.flags:
            f.write("#, %s\n" % ", ".join(sorted(message.flags)))

        # Write context
        if message.context is not None:
            f.write("msgctxt %s\n" % self._escape_string(message.context))

        # Write msgid and msgstr
        if message.msgid or message.msgstr:  # Skip empty messages
            f.write("msgid %s\n" % self._escape_string(message.msgid))
            f.write("msgstr %s\n" % self._escape_string(message.msgstr))

    def _generate_header(self):
        """Generate the header string with metadata."""
        lines = []
        
        # Write metadata in a specific order
        metadata_order = [
            "Project-Id-Version",
            "Report-Msgid-Bugs-To",
            "POT-Creation-Date",
            "PO-Revision-Date",
            "Last-Translator",
            "Language",
            "Language-Team",
            "Plural-Forms",
            "MIME-Version",
            "Content-Type",
            "Content-Transfer-Encoding",
            "Generated-By",
            "COPYRIGHT",
            "COPYRIGHT_HOLDER",
        ]
        
        # Write metadata following the order
        for key in metadata_order:
            if key in self.metadata:
                value = self.metadata[key]
                if value:  # Only write non-empty values
                    lines.append('"{}: {}\\n"'.format(key, value))
        
        # Write any remaining metadata not in the order
        for key, value in self.metadata.items():
            if key not in metadata_order and value:
                lines.append('"{}: {}\\n"'.format(key, value))
        
        return "\n".join(lines)

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
        pattern = r'(\$?\{[^}]+\})'
        
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
            (r'\\[\\"]', 'ESCAPED'),      # Escaped backslash and quotes: \\ \"
            (r'\\[nrt]', 'ESCAPED'),      # Common escape sequences: \n \r \t
            (r'\\[0-7]{1,3}', 'ESCAPED'), # Octal escapes: \123
            (r'\\x[0-9a-fA-F]{2}', 'ESCAPED'),  # Hex escapes: \xFF
            (r'\\u[0-9a-fA-F]{4}', 'ESCAPED'),  # Unicode escapes: \u00FF
            (r'\\U[0-9a-fA-F]{8}', 'ESCAPED'),  # Long Unicode escapes: \U0001F600
            (r'"[^"]*"', 'QUOTED'),       # Quoted strings: "hello"
            (r'&quot;.*?&quot;', 'QUOTED'),  # HTML quotes: &quot;hello&quot;
            (r'\$?\{[^}]+\}', 'PLACEHOLDER'),  # Format placeholders: {name} or ${name}
        ]
        
        for pattern, type_ in patterns:
            def replace(match):
                original = match.group(0)
                marker = "__%s%d__" % (type_, len(special_chars))
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
