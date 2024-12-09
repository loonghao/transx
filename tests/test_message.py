"""Test cases for Message class."""
from __future__ import unicode_literals
import unittest
from transx.api.message import Message


class TestMessage(unittest.TestCase):
    """Test cases for Message class."""

    def test_simple_message(self):
        """Test creating a simple message."""
        msg = Message("Hello", "Bonjour")
        self.assertEqual(msg.msgid, "Hello")
        self.assertEqual(msg.msgstr, "Bonjour")
        self.assertIsNone(msg.msgid_plural)
        self.assertEqual(msg.msgstr_plural, [])
        self.assertIsNone(msg.context)
        self.assertEqual(msg.locations, [])
        self.assertEqual(msg.flags, set())
        self.assertEqual(msg.auto_comments, [])
        self.assertEqual(msg.user_comments, [])
        self.assertIsNone(msg.previous_id)
        self.assertEqual(msg.metadata, {})

    def test_plural_message(self):
        """Test creating a message with plural forms."""
        msg = Message(
            ["One file", "%d files"],
            ["Un fichier", "%d fichiers"]
        )
        self.assertEqual(msg.msgid, "One file")
        self.assertEqual(msg.msgid_plural, "%d files")
        self.assertEqual(msg.msgstr, "Un fichier")
        self.assertEqual(msg.msgstr_plural, ["%d fichiers"])

    def test_context(self):
        """Test message with context."""
        msg = Message("Open", "Ouvrir", context="Menu")
        self.assertEqual(msg.context, "Menu")
        self.assertEqual(str(msg), "Ouvrir")

    def test_locations(self):
        """Test message locations."""
        msg = Message("Test", locations=[("file.py", 10)])
        self.assertEqual(msg.locations, [("file.py", 10)])
        
        # Test adding locations
        msg.add_location("other.py", 20)
        self.assertEqual(msg.locations, [("file.py", 10), ("other.py", 20)])

    def test_comments(self):
        """Test message comments."""
        msg = Message(
            "Test",
            auto_comments=["Auto comment"],
            user_comments=["User comment"]
        )
        self.assertEqual(msg.auto_comments, ["Auto comment"])
        self.assertEqual(msg.user_comments, ["User comment"])

        # Test adding comments
        msg.add_auto_comment("Another auto")
        msg.add_user_comment("Another user")
        self.assertEqual(msg.auto_comments, ["Auto comment", "Another auto"])
        self.assertEqual(msg.user_comments, ["User comment", "Another user"])

        # Test generic add_comment method
        msg.add_comment("Auto via generic", user=False)
        msg.add_comment("User via generic", user=True)
        self.assertEqual(msg.auto_comments[-1], "Auto via generic")
        self.assertEqual(msg.user_comments[-1], "User via generic")

    def test_flags(self):
        """Test message flags."""
        msg = Message("Test", flags=["fuzzy", "python-format"])
        self.assertEqual(msg.flags, {"fuzzy", "python-format"})

        # Test adding flags
        msg.add_flag("no-python-format")
        self.assertEqual(msg.flags, {"fuzzy", "python-format", "no-python-format"})

    def test_metadata(self):
        """Test message metadata."""
        metadata = {
            "Project-Id-Version": "1.0",
            "Language": "fr"
        }
        msg = Message("Test", metadata=metadata)
        self.assertEqual(msg.metadata, metadata)

    def test_string_representation(self):
        """Test string representations of messages."""
        # Test simple message
        msg1 = Message("Hello", "Bonjour")
        self.assertEqual(str(msg1), "Bonjour")
        self.assertEqual(repr(msg1), "<Message('Hello', 'Bonjour')>")

        # Test plural message
        msg2 = Message(["One", "Many"], ["Un", "Plusieurs"])
        self.assertEqual(str(msg2), "Un")
        self.assertEqual(repr(msg2), "<Message('One', 'Un', plural='Many')>")

        # Test untranslated message
        msg3 = Message("Untranslated")
        self.assertEqual(str(msg3), "Untranslated")

    def test_unicode_handling(self):
        """Test handling of unicode strings."""
        msg = Message(
            "Hello ",
            "Bonjour ",
            context="Context ",
            locations=[("file_.py", 1)],
            auto_comments=["Comment "],
            user_comments=["User "],
            previous_id="Prev "
        )
        self.assertEqual(msg.msgid, "Hello ")
        self.assertEqual(msg.msgstr, "Bonjour ")
        self.assertEqual(msg.context, "Context ")
        self.assertEqual(msg.locations[0][0], "file_.py")
        self.assertEqual(msg.auto_comments[0], "Comment ")
        self.assertEqual(msg.user_comments[0], "User ")
        self.assertEqual(msg.previous_id, "Prev ")


if __name__ == "__main__":
    unittest.main()
