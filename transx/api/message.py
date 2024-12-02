#!/usr/bin/env python
"""Message class for translation entries."""
from __future__ import unicode_literals


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
        if isinstance(msgid, (list, tuple)):
            self.msgid = msgid[0]  # Use first part for plural forms
        else:
            self.msgid = msgid
        self.msgstr = msgstr
        self.context = context
        self.locations = locations or []
        self.flags = set(flags or [])
        self.auto_comments = list(auto_comments or [])
        self.user_comments = list(user_comments or [])
        self.previous_id = previous_id
        self.lineno = lineno
        self.metadata = metadata or {}

    def __repr__(self):
        return '<Message(%r, %r)>' % (self.msgid, self.msgstr)

    def add_location(self, filename, lineno):
        """Add a source location to the message."""
        self.locations.append((filename, lineno))

    def add_comment(self, comment, user=True):
        """Add a comment to the message.
        
        Args:
            comment: The comment text
            user: True if this is a user comment, False for automatic comments
        """
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
        """Add a flag to the message."""
        self.flags.add(flag)

    @property
    def is_fuzzy(self):
        """Check if the message is marked as fuzzy."""
        return "fuzzy" in self.flags

    def clone(self):
        """Create a copy of this message."""
        return Message(
            msgid=self.msgid,
            msgstr=self.msgstr,
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
                self.msgstr == other.msgstr and
                self.context == other.context)
