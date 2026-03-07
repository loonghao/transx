#!/usr/bin/env python
"""Base POT/PO file format handler for TransX."""

# fmt: off
# isort: skip
# Import future modules
from __future__ import unicode_literals

# Import built-in modules
from collections import OrderedDict
import datetime
import logging
import os

# Import local modules
from transx.api.message import Message
from transx.constants import DEFAULT_CHARSET
from transx.constants import HEADER_COMMENT
from transx.constants import METADATA_KEYS
from transx.internal.filesystem import normalize_path
from transx.internal.filesystem import read_file
from transx.internal.filesystem import write_file


class POTFile(object):

    """Base class for PO/POT file format handling."""

    def __init__(self, path=None, locale=None):
        """Initialize a new PO/POT file handler.

        Args:
            path: Path to the PO/POT file
            locale: Locale code (e.g., 'en_US', 'zh_CN')
        """
        self.path = path
        self.locale = locale
        self.translations = OrderedDict()
        self.metadata = OrderedDict()
        self.header_comment = ""  # Add header_comment attribute
        self._init_metadata()
        self.logger = logging.getLogger(__name__)

    def _init_metadata(self):
        """Initialize default metadata."""
        now = datetime.datetime.now()
        year = now.year
        creation_date = now.strftime("%Y-%m-%d %H:%M%z")

        # Initialize metadata with ordered keys
        self.metadata = OrderedDict()
        for key in METADATA_KEYS:
            self.metadata[key] = ""

        # Set default values
        self.metadata.update({
            "Project-Id-Version": "PROJECT VERSION",
            "Report-Msgid-Bugs-To": "EMAIL@ADDRESS",
            "POT-Creation-Date": creation_date,
            "PO-Revision-Date": "YEAR-MO-DA HO:MI+ZONE",
            "Last-Translator": "FULL NAME <EMAIL@ADDRESS>",
            "Language-Team": "LANGUAGE <LL@li.org>",
            "MIME-Version": "1.0",
            "Content-Type": "text/plain; charset=UTF-8",
            "Content-Transfer-Encoding": "8bit",
            "Generated-By": "TransX",
        })

        # Create header comment
        self.header_comment = HEADER_COMMENT.format(year, year)

        # Create metadata message
        metadata_str = []
        for key in METADATA_KEYS:
            if self.metadata.get(key):
                metadata_str.append("{}: {}".format(key, self.metadata[key]))

        metadata_msg = Message(
            msgid="",
            msgstr="\n".join(metadata_str) + "\n",
            flags={"fuzzy"}
        )
        self.translations[""] = metadata_msg

    def _get_key(self, msgid, context=None):
        """Get the key for storing a message.

        Args:
            msgid: The message ID
            context: The message context

        Returns:
            str: A string key combining msgid and context
        """
        if context is not None:
            return "{0}\x04{1}".format(context, msgid)
        return msgid

    def update_metadata(self, new_metadata):
        """Update metadata without duplicating entries.

        Args:
            new_metadata: New metadata to merge
        """
        for key, value in new_metadata.items():
            if value:  # Only add non-empty values
                self.metadata[key] = value

        # Update header message
        header_key = self._get_key("", None)
        if header_key not in self.translations:
            self.translations[header_key] = Message(msgid="", msgstr="")

        # Generate header content with quotes
        header_lines = []
        for key in METADATA_KEYS.values():  # Use ordered metadata keys
            value = self.metadata.get(key, "")
            if value:  # Only write non-empty values
                header_lines.append("%s: %s\\n" % (key, value))
        self.translations[header_key].msgstr = "\n".join(header_lines)

    def parse_header(self, header):
        """Parse the header into a dictionary.

        Args:
            header: Header string to parse

        Returns:
            OrderedDict: Parsed metadata
        """
        headers = OrderedDict()
        if not header:
            return headers

        # First unescape the entire header
        header = self._unescape_string(header)

        valid_keys = set(METADATA_KEYS.values())
        current_key = None

        # Split into lines and process each line
        for raw_line in header.split("\n"):
            if not raw_line.strip():
                continue

            # Check continuation before trimming leading spaces.
            if raw_line[:1].isspace() and current_key:
                headers[current_key] += " " + raw_line.strip()
                continue

            # Look for "key: value" format
            if ":" in raw_line:
                key, value = raw_line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key in valid_keys:  # Only accept known metadata keys
                    headers[key] = value
                    current_key = key
                else:
                    current_key = None
            else:
                current_key = None

        return headers


    def _write_message(self, message, file):
        """Write a single message to the file."""
        # Write comments
        if message.auto_comments:
            for comment in message.auto_comments:
                file.write("#. {}\n".format(comment))

        if message.user_comments:
            for comment in message.user_comments:
                file.write("# {}\n".format(comment))

        # Write locations one per line, sorted and deduplicated
        if message.locations:
            tuple_locs = set()
            string_locs = set()
            for loc in message.locations:
                if isinstance(loc, tuple):
                    filename, lineno = loc
                    tuple_locs.add((normalize_path(filename), lineno))
                else:
                    string_locs.add(loc)

            for filename, lineno in sorted(tuple_locs):
                file.write("#: {}:{}\n".format(filename, lineno))
            for loc in sorted(string_locs):
                file.write("#: {}\n".format(loc))


        # Write flags
        if message.flags:
            file.write("#, {}\n".format(" ".join(sorted(message.flags))))

        # Write message content
        if message.context:
            file.write('msgctxt "{}"\n'.format(self._escape_string(message.context)))

        # Special handling for metadata message (empty msgid)
        if not message.msgid:
            file.write('msgid ""\n')
            file.write('msgstr ""\n')
            if message.msgstr:
                # Split metadata into lines and write each line
                for line in message.msgstr.strip().split("\n"):
                    if line:
                        file.write('"{0}\\n"\n'.format(line))
            return

        # Write msgid
        if "\n" in message.msgid:
            file.write('msgid ""\n')
            for line in message.msgid.split("\n"):
                file.write('"{0}\\n"\n'.format(self._escape_string(line)))
        else:
            file.write('msgid "{}"\n'.format(self._escape_string(message.msgid)))

        # Write msgstr
        if "\n" in message.msgstr:
            file.write('msgstr ""\n')
            for line in message.msgstr.split("\n"):
                file.write('"{0}\\n"\n'.format(self._escape_string(line)))
        else:
            file.write('msgstr "{}"\n'.format(self._escape_string(message.msgstr)))

    def _escape_string(self, text):
        """Escape a string value for writing to PO/POT file.

        Args:
            text: The string to escape

        Returns:
            str: The escaped string value
        """
        if not text:
            return text
        text = text.replace("\\", "\\\\")  # Must be first
        text = text.replace("\n", "\\n")
        text = text.replace("\r", "\\r")
        text = text.replace("\t", "\\t")
        text = text.replace('"', '\\"')
        return text

    def _unescape_string(self, string):
        """Unescape a quoted string."""
        if not string:
            return ""
        if string.startswith('"') and string.endswith('"'):
            string = string[1:-1]  # Remove surrounding quotes
        # Unescape special characters
        return string.encode("raw_unicode_escape").decode("unicode_escape")

    def _parse_string(self, text):
        """Parse a string value from a PO/POT file.

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

    def save(self, file_path=None):
        """Save the catalog to a file.

        Args:
            file_path: Path to save the file to, defaults to self.path
        """
        if file_path is None:
            file_path = self.path
        if not file_path:
            raise ValueError("No file path specified")

        content = []
        # Write header comment if exists
        if self.header_comment:
            content.append(self.header_comment.strip() + "\n\n")

        # Write metadata
        content.append('msgid ""\n')
        content.append('msgstr ""\n')
        for key, value in self.metadata.items():
            if value:  # Only write non-empty metadata
                content.append('"{}: {}\\n"\n'.format(
                    self._escape_string(key),
                    self._escape_string(value)
                ))
        content.append("\n")

        # Write messages in deterministic order
        messages = [m for m in self.translations.values() if m.msgid != ""]

        def _message_sort_key(message):
            if message.locations:
                locs = sorted((normalize_path(path), lineno) for path, lineno in message.locations)
                first_loc = locs[0]
            else:
                first_loc = ("~", 0)
            return (first_loc[0], first_loc[1], message.context or "", message.msgid)

        for message in sorted(messages, key=_message_sort_key):


            # Write automatic comments
            if message.auto_comments:
                for comment in message.auto_comments:
                    content.append("#. " + comment + "\n")

            # Write user comments
            if message.user_comments:
                for comment in message.user_comments:
                    content.append("# " + comment + "\n")

            # Write locations (deduplicated)
            if message.locations:
                locations = sorted(set(message.locations))  # Remove duplicates
                for loc in locations:
                    if isinstance(loc, tuple):
                        content.append("#: {}:{}\n".format(
                            normalize_path(str(loc[0])),
                            loc[1]
                        ))
                    else:
                        content.append("#: {}\n".format(normalize_path(str(loc))))

            # Write flags (deduplicated)
            if message.flags:
                flags = sorted(set(message.flags))  # Remove duplicates
                content.append("#, " + ", ".join(flags) + "\n")

            # Write message context
            if message.context:
                content.append('msgctxt "{}"\n'.format(self._escape_string(message.context)))

            # Write msgid
            if isinstance(message.msgid, (list, tuple)):
                content.append('msgid ""\n')
                for line in message.msgid:
                    content.append('"{0}"\n'.format(self._escape_string(line)))
            else:
                content.append('msgid "{}"\n'.format(self._escape_string(message.msgid)))

            # Write msgid_plural if exists
            if message.msgid_plural is not None:
                if isinstance(message.msgid_plural, (list, tuple)):
                    content.append('msgid_plural ""\n')
                    for line in message.msgid_plural:
                        content.append('"{0}"\n'.format(self._escape_string(line)))
                else:
                    content.append('msgid_plural "{}"\n'.format(self._escape_string(message.msgid_plural)))

            # Write msgstr
            if message.msgstr_plural:
                for i, plural in enumerate(message.msgstr_plural):
                    if isinstance(plural, (list, tuple)):
                        content.append('msgstr[{}] ""\n'.format(i))
                        for line in plural:
                            content.append('"{0}"\n'.format(self._escape_string(line)))
                    else:
                        content.append('msgstr[{}] "{}"\n'.format(i, self._escape_string(plural)))
            else:
                if isinstance(message.msgstr, (list, tuple)):
                    content.append('msgstr ""\n')
                    for line in message.msgstr:
                        content.append('"{0}"\n'.format(self._escape_string(line)))
                else:
                    content.append('msgstr "{}"\n'.format(self._escape_string(message.msgstr or "")))

            content.append("\n")

        # Write to file using filesystem module
        write_file(file_path, "".join(content), encoding=DEFAULT_CHARSET)

    def load(self, file_path=None):
        """Load messages from a PO/POT file.

        Args:
            file_path: Path to the PO/POT file to load from, defaults to self.path
        """
        if file_path is None:
            file_path = self.path
        if file_path is None:
            raise ValueError("No file path specified")

        if not os.path.exists(file_path):
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

        # Clear existing translations before loading
        self.translations.clear()

        content = read_file(file_path, encoding=DEFAULT_CHARSET)
        for line in content.splitlines():
            line = line.strip()

            # Skip empty lines
            if not line:
                if current_message is not None:
                    # Update msgid and add the message
                    current_message.msgid = "".join(current_msgid)
                    current_message.msgstr = "".join(current_msgstr)
                    if current_msgctxt:
                        current_message.context = "".join(current_msgctxt)
                    if current_locations:
                        current_message.locations = current_locations[:]  # Correctly handle locations
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

            # Parse header comment (only plain comments, not structured ones like #. #: #,)
            if line.startswith("#") and not current_message:
                if not line.startswith("#.") and not line.startswith("#:") and not line.startswith("#,") and not line.startswith("#|"):
                    if not self.header_comment:
                        self.header_comment = ""
                    self.header_comment += line + "\n"
                    continue

            # Parse comments
            if line.startswith("#"):
                if line.startswith("#:"):  # Location
                    locations = line[2:].strip().split()
                    for location in locations:
                        parts = location.split(":")
                        if len(parts) >= 2:
                            # Join all parts except the last one to handle Windows paths
                            filename = ":".join(parts[:-1])
                            try:
                                lineno = int(parts[-1])
                                current_locations.append((normalize_path(filename.strip()), lineno))
                            except ValueError:
                                current_locations.append(normalize_path(location))
                elif line.startswith("#,"):  # Flags
                    flags = line[2:].strip().split(",")
                    current_flags.update(f.strip() for f in flags)
                elif line.startswith("#."):  # Auto comment
                    current_auto_comments.append(line[2:].strip())
                elif line.startswith("#|"):  # Previous string
                    pass  # Ignore previous strings for now
                else:  # User comment
                    current_user_comments.append(line[1:].strip())
                continue

            # Parse msgctxt
            if line.startswith("msgctxt"):
                reading_msgctxt = True
                reading_msgid = False
                reading_msgstr = False
                if '"' in line:
                    current_msgctxt.append(self._parse_string(line[7:]))

            # Parse msgid
            if line.startswith("msgid"):
                reading_msgid = True
                reading_msgstr = False
                reading_msgctxt = False
                if current_message is not None:
                    # Update msgid and add the message
                    current_message.msgid = "".join(current_msgid)
                    if current_locations:
                        current_message.locations = current_locations[:]  # Correctly handle locations
                    if current_flags:
                        current_message.flags = current_flags.copy()
                    if current_auto_comments:
                        current_message.auto_comments = current_auto_comments[:]
                    if current_user_comments:
                        current_message.user_comments = current_user_comments[:]
                    self._add_current_message(current_message)
                # Reset message parts
                current_msgid = []
                current_msgstr = []
                current_message = Message(
                    msgid="",  # Set empty string temporarily, will update later
                    locations=current_locations[:],
                    flags=current_flags.copy(),
                    auto_comments=current_auto_comments[:],
                    user_comments=current_user_comments[:]
                )
                # Reset comment/flag collections for next message
                current_locations = []
                current_flags = set()
                current_auto_comments = []
                current_user_comments = []
                if '"' in line:
                    current_msgid.append(self._parse_string(line[5:]))

            # Parse msgstr
            if line.startswith("msgstr"):
                reading_msgstr = True
                reading_msgid = False
                reading_msgctxt = False
                if '"' in line:
                    current_msgstr.append(self._parse_string(line[6:]))

            # Continuation of previous string
            if line.startswith('"'):
                if reading_msgctxt:
                    current_msgctxt.append(self._parse_string(line))
                elif reading_msgid:
                    current_msgid.append(self._parse_string(line))
                elif reading_msgstr:
                    current_msgstr.append(self._parse_string(line))

        # Add the last message if there is one
        if current_message is not None:
            current_message.msgid = "".join(current_msgid)
            current_message.msgstr = "".join(current_msgstr)
            if current_msgctxt:
                current_message.context = "".join(current_msgctxt)
            if current_locations:
                current_message.locations = current_locations[:]  # Correctly handle locations
            if current_flags:
                current_message.flags = current_flags.copy()
            if current_auto_comments:
                current_message.auto_comments = current_auto_comments[:]
            if current_user_comments:
                current_message.user_comments = current_user_comments[:]
            self._add_current_message(current_message)

        # Parse header if exists
        header_key = self._get_key("", None)
        if header_key in self.translations:
            header = self.translations[header_key].msgstr
            if header:
                self.metadata.update(self.parse_header(header))

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

    def add(self, msgid, msgstr="", flags=None, auto_comments=None, user_comments=None, context=None, locations=None):
        """Add a new message to the catalog.

        Args:
            msgid: Message ID (source string)
            msgstr: Message string (translated string)
            flags: List of flags
            auto_comments: List of automatic comments
            user_comments: List of user comments
            context: Message context
            locations: List of (filename, line) tuples

        Returns:
            Message: The added message
        """
        message = Message(
            msgid=msgid,
            msgstr=msgstr,
            flags=flags or [],
            auto_comments=auto_comments or [],
            user_comments=user_comments or [],
            context=context,
            locations=locations or []
        )
        key = self._get_key(msgid, context)
        self.translations[key] = message
        return message

