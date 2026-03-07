#!/usr/bin/env python
"""POT extractor for TransX."""

# fmt: off
# isort: skip
# Import future modules
from __future__ import unicode_literals

# Import built-in modules
import datetime
import os
import re
import tokenize

# Import local modules
from transx.api.message import Message
from transx.api.pot.base_file import POTFile
from transx.constants import DEFAULT_KEYWORDS
from transx.constants import HEADER_COMMENT
from transx.constants import LANGUAGE_CODES
from transx.internal.compat import PY2
from transx.internal.compat import safe_eval_string
from transx.internal.compat import string_types
from transx.internal.compat import tokenize_source


class PotExtractor(object):
    """Extract translatable strings from Python source files."""

    _IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    _TR_LIKE_SPEC = "__transx_tr_like__"


    def __init__(self, source_files=None, pot_file=None, additional_keywords=None):
        """Initialize a new PotExtractor instance.

        Args:
            source_files: List of source files to extract from
            pot_file: Path to output POT file
            additional_keywords: Optional extra extraction keywords (list/tuple or dict)
        """
        self.source_files = source_files or []
        self.pot_file = pot_file
        self.catalog = POTFile(path=pot_file)
        self.current_file = None
        self.current_line = 0
        self.keywords = self._build_keywords(additional_keywords)
        self._language_codes = self._build_language_code_set()
        self._skip_literals = {"locales", "LC_MESSAGES", "__main__", "__init__", "__file__"}
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
        self.catalog.header_comment = HEADER_COMMENT.format(year, year)

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

    def add_source_directory(self, directory, extensions=(".py",)):
        """Recursively add source files from a directory.

        Args:
            directory: Directory path to scan
            extensions: File extensions to include
        """
        if not os.path.isdir(directory):
            return

        normalized_exts = tuple(ext.lower() for ext in extensions)
        for root, _dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(normalized_exts):
                    file_path = os.path.join(root, filename)
                    if file_path not in self.source_files:
                        self.source_files.append(file_path)

    def extract_messages(self):

        """Extract translatable strings from source files."""
        for file_path in sorted(self.source_files):

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

    def _is_valid_keyword_name(self, name):
        """Check whether a keyword name is a valid Python identifier."""
        if not isinstance(name, string_types):
            return False
        return bool(self._IDENTIFIER_RE.match(name))


    def _build_keywords(self, additional_keywords):
        """Build merged extraction keywords from defaults and user provided values."""
        keywords = dict(DEFAULT_KEYWORDS)
        if additional_keywords is None:
            return keywords

        if isinstance(additional_keywords, dict):
            items = additional_keywords.items()
        elif isinstance(additional_keywords, (list, tuple, set)):
            items = [(name, self._TR_LIKE_SPEC) for name in additional_keywords]

        else:
            raise ValueError("additional_keywords must be a dict or list/tuple/set")

        for name, spec in items:
            if not self._is_valid_keyword_name(name):
                raise ValueError("Invalid keyword name: %r" % (name,))
            keywords[name] = spec

        return keywords

    def _build_language_code_set(self):
        """Build fast lookup set for language codes and aliases."""
        language_codes = set()
        for code, (_name, aliases) in LANGUAGE_CODES.items():
            language_codes.add(code)
            language_codes.update(aliases)
        return language_codes

    def _extract_by_spec(self, func_name, args, kwargs, spec):

        """Extract message from parsed arguments using keyword spec."""
        if func_name == "tr" or spec == self._TR_LIKE_SPEC:
            if not args:
                return None
            msgid = args[0]
            context = kwargs.get("context")
            if not msgid:
                return None
            return Message(msgid=msgid, context=context)


        if spec is None:
            if not args:
                return None
            return Message(msgid=args[0])

        if not isinstance(spec, tuple):
            return None

        context = None
        message_args = []

        for entry in spec:
            if isinstance(entry, tuple) and len(entry) == 2 and entry[1] == "c":
                idx = entry[0] - 1
                if 0 <= idx < len(args):
                    context = args[idx]
            elif isinstance(entry, int):
                idx = entry - 1
                if 0 <= idx < len(args):
                    message_args.append(args[idx])

        if not message_args:
            return None

        if len(message_args) >= 2:
            return Message(msgid=(message_args[0], message_args[1]), context=context)

        return Message(msgid=message_args[0], context=context)

    def _process_tokens(self, content):
        """Process tokens from source file."""

        tokens = tokenize_source(content)
        tokens = list(tokens)  # Convert iterator to list for look-ahead

        i = 0
        while i < len(tokens):
            token_type, token_string, start, _end, _line = tokens[i]


            # Look for translation function calls
            if token_type == tokenize.NAME and token_string in self.keywords:

                self.current_line = start[0]  # Update current line number
                func_name = token_string
                # Skip the function name token
                i += 1
                if i >= len(tokens):
                    break

                # Look for opening parenthesis
                token_type, token_string, start, _end, _line = tokens[i]

                if token_type == tokenize.OP and token_string == "(":
                    # Skip the opening parenthesis
                    i += 1
                    if i >= len(tokens):
                        break

                    # Get arguments
                    args = []
                    kwargs = {}
                    current_string = []
                    paren_depth = 1
                    while i < len(tokens):
                        token_type, token_string, start, _end, _line = tokens[i]

                        if token_type == tokenize.OP:
                            if token_string == "(":
                                paren_depth += 1
                            elif token_string == ")":
                                paren_depth -= 1
                                if paren_depth == 0:
                                    if current_string:
                                        string_content = "".join(current_string)
                                        if string_content:
                                            args.append(string_content)
                                    break

                        # Handle keyword arguments (top-level only)
                        if (
                            paren_depth == 1
                            and token_type == tokenize.NAME
                            and i + 1 < len(tokens)
                        ):
                            next_token = tokens[i + 1]
                            if next_token[1] == "=":
                                if current_string:
                                    string_content = "".join(current_string)
                                    if string_content:
                                        args.append(string_content)
                                    current_string = []
                                kwarg_name = token_string
                                i += 2  # Skip '=' token
                                if i < len(tokens) and tokens[i][0] == tokenize.STRING:
                                    kwargs[kwarg_name] = safe_eval_string(tokens[i][1])
                                i += 1
                                continue


                        # Handle string concatenation and f-strings
                        if token_type == tokenize.STRING:
                            # Check for f-string prefix
                            if token_string.startswith(('f"', "f'", 'F"', "F'")):
                                # Extract the string content without the f-prefix
                                raw_string = token_string[2:-1]  # Remove f-prefix and quotes
                                # For now, we just keep the placeholders as they are
                                current_string.append(raw_string)
                            else:
                                string_value = safe_eval_string(token_string)
                                if string_value is not None:
                                    current_string.append(string_value)

                        # Split positional arguments by top-level commas
                        if token_type == tokenize.OP and token_string == "," and paren_depth == 1:
                            if current_string:
                                string_content = "".join(current_string)
                                if string_content:
                                    args.append(string_content)
                                current_string = []
                            i += 1
                            continue

                        i += 1


                    # Process arguments based on keyword spec
                    spec = self.keywords.get(func_name)
                    msg = self._extract_by_spec(func_name, args, kwargs, spec)
                    if msg is not None and not self._should_skip_string(msg.msgid):
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

        # Skip language codes and aliases
        if string in self._language_codes:
            return True

        # Skip known non-translatable literals
        if string in self._skip_literals:
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
