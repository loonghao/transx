#!/usr/bin/env python
"""POT file format handler for TransX."""
# fmt: off
# isort: skip
# Import future modules
from __future__ import unicode_literals

# Import built-in modules
from collections import OrderedDict
import datetime
import logging
import os
import tokenize

# Import local modules
from transx.api.locale import normalize_language_code
from transx.api.message import Message
from transx.api.translate import POFile
from transx.constants import DEFAULT_CHARSET
from transx.constants import DEFAULT_KEYWORDS
from transx.constants import LANGUAGE_CODES
from transx.constants import METADATA_KEYS
from transx.internal.compat import PY2
from transx.internal.compat import safe_eval_string
from transx.internal.compat import tokenize_source
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
        self.header_comment = (
            "# Translations template for PROJECT.\n"
            "# Copyright (C) {} ORGANIZATION\n"
            "# This file is distributed under the same license as the PROJECT project.\n"
            "# FIRST AUTHOR <EMAIL@ADDRESS>, {}."
        ).format(year, year)

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

        # Split into lines and process each line
        for line in header.split("\\n"):
            line = line.strip()
            if not line:
                continue

            # Check for continuation of previous value
            if line.startswith(" ") and "current_key" in locals():
                headers[current_key] += " " + line.strip()
                continue

            # Look for "key: value" format
            if ": " in line:
                key, value = line.split(": ", 1)
                key = key.strip()
                value = value.strip()
                if key in METADATA_KEYS:  # Only accept known metadata keys
                    headers[key] = value
                    current_key = key
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
            # Sort and deduplicate locations
            unique_locs = set()
            for loc in message.locations:
                if isinstance(loc, tuple):
                    filename, lineno = loc
                    filename = normalize_path(filename)
                    unique_locs.add("{}:{}".format(filename, lineno))
                else:
                    unique_locs.add(loc)

            for loc in sorted(unique_locs):
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

        # Write messages
        for message in self.translations.values():
            if message.msgid == "":  # Skip metadata message
                continue

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

            # Parse header comment
            if line.startswith("#") and not current_message:
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
        key = (msgid, context)
        self.translations[key] = message
        return message


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
        self.catalog = POTFile(path=pot_file)
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
                        if token_type == tokenize.NAME and i + 1 < len(tokens) and tokens[i + 1][1] == "=":
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
        for code, (_name, aliases) in LANGUAGE_CODES.items():
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
        return string.startswith(("http://", "https://", "ftp://"))

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

    def save(self):
        """Alias for save_pot() for compatibility with test_api.py."""
        self.save_pot()

    def save_pot(self, project=None, version=None, copyright_holder=None, bugs_address=None):
        """Save POT file with project information.

        Args:
            project: Project name
            version: Project version
            copyright_holder: Copyright holder
            bugs_address: Email address for bug reports
        """
        if not self.pot_file:
            raise ValueError("No POT file path specified")

        # Update metadata if provided
        if project:
            self.catalog.metadata["Project-Id-Version"] = "%s %s" % (project, version or "")
        if copyright_holder:
            self.catalog.metadata["Copyright-Holder"] = copyright_holder
        if bugs_address:
            self.catalog.metadata["Report-Msgid-Bugs-To"] = bugs_address

        # Save catalog to POT file
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
        language_name = {
            "en_US": "English (United States)",
            "zh_CN": "Chinese (Simplified)",
            "zh_TW": "Chinese (Traditional)",
            "ja_JP": "Japanese",
            "ko_KR": "Korean",
            "fr_FR": "French",
            "es_ES": "Spanish",
        }.get(language, language)

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
        language_name = {
            "en_US": "English (United States)",
            "zh_CN": "Chinese (Simplified)",
            "zh_TW": "Chinese (Traditional)",
            "ja_JP": "Japanese",
            "ko_KR": "Korean",
            "fr_FR": "French",
            "es_ES": "Spanish",
        }.get(language, language)

        # Add header comments with fuzzy flag
        year = datetime.datetime.now().year
        po_catalog.header_comment = (
            "# {} translations for PROJECT.\n"
            "# Copyright (C) {} ORGANIZATION\n"
            "# This file is distributed under the same license as the PROJECT project.\n"
            "# FIRST AUTHOR <EMAIL@ADDRESS>, {}.\n"
            "#\n"
            "#, fuzzy\n"
        ).format(language_name, year, year)
