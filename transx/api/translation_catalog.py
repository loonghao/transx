#!/usr/bin/env python
"""Translation catalog functionality."""

# Import built-in modules
import re
import sys

# Import local modules
from transx.constants import DEFAULT_CHARSET
from transx.constants import DEFAULT_MESSAGES_DOMAIN


# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode
    binary_type = str
else:
    text_type = str
    binary_type = bytes


class TranslationCatalog:
    """Represents a collection of translation messages."""

    def __init__(self, locale=None, domain=DEFAULT_MESSAGES_DOMAIN, charset=DEFAULT_CHARSET):
        """Initialize a new translation catalog.

        Args:
            locale: The locale this catalog is for
            domain: The message domain
            charset: Character encoding for the catalog
        """
        self.locale = locale
        self.domain = domain
        self.charset = charset
        self._messages = {}  # {msgid: (msgstr, context, is_plural)}
        self._variants = {}  # {normalized_key: [msgid1, msgid2, ...]}

    def _normalize_key(self, text):
        """Normalize text for variant matching."""
        if isinstance(text, binary_type):
            text = text.decode(self.charset)

        # Remove punctuation and whitespace
        text = re.sub(r"[^\w\s]", "", text.lower())
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def add_message(self, msgid, msgstr="", context=None, is_plural=False):
        """Add a message to the catalog."""
        # Ensure strings are unicode in both Python 2 and 3
        if isinstance(msgid, binary_type):
            msgid = msgid.decode(self.charset)
        if isinstance(msgstr, binary_type):
            msgstr = msgstr.decode(self.charset)

        # Add context separator if context is provided
        if context:
            msgid = context + "\x04" + msgid

        self._messages[msgid] = (msgstr, context, is_plural)

        # Add to variants index
        norm_key = self._normalize_key(msgid)
        if norm_key not in self._variants:
            self._variants[norm_key] = []
        if msgid not in self._variants[norm_key]:
            self._variants[norm_key].append(msgid)

    def get_message(self, msgid, context=None):
        """Get a message from the catalog."""
        if isinstance(msgid, binary_type):
            msgid = msgid.decode(self.charset)

        if msgid in self._messages:
            msgstr, msg_context, is_plural = self._messages[msgid]
            return msgstr
        return None

    def find_variants(self, text):
        """Find variant messages that are similar to the given text."""
        if isinstance(text, binary_type):
            text = text.decode(self.charset)

        norm_key = self._normalize_key(text)
        return self._variants.get(norm_key, [])