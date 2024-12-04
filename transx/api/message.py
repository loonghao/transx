#!/usr/bin/env python
"""Message class for translation entries."""
# fmt: off
# isort: skip
# Import future modules
from __future__ import unicode_literals

# Import local modules
# fmt: on
from transx.internal.compat import ensure_unicode


class Message(object):
    """Representation of a single message in a catalog."""

    def __init__(self, msgid, msgstr="", context=None, locations=None, flags=None,
                 auto_comments=None, user_comments=None, previous_id=None, lineno=None, metadata=None):
        """Create a new Message instance.

        Args:
            msgid: The message ID (source text)
            msgstr: The message translation
            context: The message context
            locations: List of (filename, line) tuples
            flags: List of flags
            auto_comments: Automatic comments for the message
            user_comments: User comments for the message
            previous_id: Previous message ID (for fuzzy matching)
            lineno: Line number in the PO file
            metadata: Dictionary of metadata key-value pairs
        """
        # Handle plural forms
        if isinstance(msgid, (list, tuple)):
            self.msgid = ensure_unicode(msgid[0])  # Use first part for plural forms
            self.msgid_plural = ensure_unicode(msgid[1]) if len(msgid) > 1 else None
        else:
            self.msgid = ensure_unicode(msgid)
            self.msgid_plural = None

        # Handle plural translations
        if isinstance(msgstr, (list, tuple)):
            self.msgstr = ensure_unicode(msgstr[0])
            self.msgstr_plural = [ensure_unicode(s) for s in msgstr[1:]]
        else:
            self.msgstr = ensure_unicode(msgstr)
            self.msgstr_plural = []

        # Initialize other attributes
        self.context = ensure_unicode(context) if context else None
        self.locations = [(ensure_unicode(f), line_num) for f, line_num in locations or []]
        self.flags = set(flags or [])
        self.auto_comments = [ensure_unicode(c) for c in auto_comments or []]
        self.user_comments = [ensure_unicode(c) for c in user_comments or []]
        self.previous_id = ensure_unicode(previous_id) if previous_id else None
        self.lineno = lineno
        self.metadata = metadata or {}

    def __repr__(self):
        """Return a string representation of the message."""
        if self.msgid_plural:
            return "<Message(%r, %r, plural=%r)>" % (self.msgid, self.msgstr, self.msgid_plural)
        return "<Message(%r, %r)>" % (self.msgid, self.msgstr)

    def __str__(self):
        """Return the translated string."""
        return self.msgstr if self.msgstr else self.msgid

    def add_location(self, filename, lineno):
        """Add a source location to the message.

        Args:
            filename: Source file path
            lineno: Line number in the source file
        """
        self.locations.append((ensure_unicode(filename), lineno))

    def add_comment(self, comment, user=True):
        """Add a comment to the message.

        Args:
            comment: The comment text
            user: True if this is a user comment, False for automatic comments
        """
        comment = ensure_unicode(comment)
        if user:
            self.user_comments.append(comment)
        else:
            self.auto_comments.append(comment)

    def add_auto_comment(self, comment):
        """Add an automatic comment to the message."""
        self.add_comment(comment, user=False)

    def add_user_comment(self, comment):
        """Add a user comment to the message."""
        self.add_comment(comment, user=True)

    def add_flag(self, flag):
        """Add a flag to the message.

        Args:
            flag: The flag to add
        """
        self.flags.add(ensure_unicode(flag))

    def remove_flag(self, flag):
        """Remove a flag from the message.

        Args:
            flag: The flag to remove
        """
        self.flags.discard(ensure_unicode(flag))

    def is_fuzzy(self):
        """Check if this message is fuzzy."""
        return "fuzzy" in self.flags

    def is_obsolete(self):
        """Check if this message is obsolete."""
        return "obsolete" in self.flags

    def is_translated(self):
        """Check if this message has a translation."""
        return bool(self.msgstr)

    def merge(self, other):
        """Merge another message into this one.

        Args:
            other: Another Message instance to merge from
        """
        if other.msgstr:
            self.msgstr = other.msgstr
        if other.msgstr_plural:
            self.msgstr_plural = other.msgstr_plural[:]
        if other.flags:
            self.flags.update(other.flags)
        if other.auto_comments:
            self.auto_comments.extend(c for c in other.auto_comments if c not in self.auto_comments)
        if other.user_comments:
            self.user_comments.extend(c for c in other.user_comments if c not in self.user_comments)
        if other.locations:
            self.locations.extend(loc for loc in other.locations if loc not in self.locations)

    def clone(self):
        """Create a copy of this message."""
        msgid = [self.msgid, self.msgid_plural] if self.msgid_plural else self.msgid
        msgstr = [self.msgstr] + self.msgstr_plural if self.msgstr_plural else self.msgstr
        return Message(
            msgid=msgid,
            msgstr=msgstr,
            context=self.context,
            locations=self.locations[:],
            flags=self.flags.copy(),
            auto_comments=self.auto_comments[:],
            user_comments=self.user_comments[:],
            previous_id=self.previous_id,
            lineno=self.lineno,
            metadata=self.metadata.copy()
        )

    def __eq__(self, other):
        """Compare this message with another for equality."""
        if not isinstance(other, Message):
            return NotImplemented
        return (self.msgid == other.msgid and
                self.msgid_plural == other.msgid_plural and
                self.msgstr == other.msgstr and
                self.msgstr_plural == other.msgstr_plural and
                self.context == other.context)
