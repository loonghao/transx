#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test PO file functionality."""

# Import built-in modules
import os

# Import third-party modules
import pytest

# Import local modules
from transx.api.message import Message
from transx.api.po import POFile
from transx.constants import METADATA_KEYS


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory"""
    return tmp_path


@pytest.fixture
def po_file(temp_dir):
    """Provide a basic PO file instance"""
    po_file_path = temp_dir / "test.po"
    return POFile(str(po_file_path), locale="zh_CN")


@pytest.fixture
def pot_file(temp_dir):
    """Provide a basic POT file instance"""
    pot_file_path = temp_dir / "test.pot"
    pot = POFile(str(pot_file_path))
    return pot


def test_init_metadata(po_file):
    """Test metadata initialization"""
    assert METADATA_KEYS["PROJECT_ID_VERSION"] in po_file.metadata
    assert METADATA_KEYS["LANGUAGE"] in po_file.metadata
    assert po_file.metadata[METADATA_KEYS["LANGUAGE"]] == "zh_CN"
    assert "" in po_file.translations  # Header message should exist
    # Check if all metadata keys are in the header message
    assert all(key in po_file.translations[""].msgstr for key in METADATA_KEYS.values())


def test_add_message(po_file):
    """Test adding new message"""
    msgid = u"Hello, world!"
    msgstr = u"Hello, world!"  # Example translation
    po_file.add(
        msgid=msgid,
        msgstr=msgstr,
        locations=[("test.py", 1)],
        auto_comments=["Test comment"]
    )

    assert msgid in po_file.translations
    message = po_file.translations[msgid]
    assert message.msgstr == msgstr
    assert message.locations == [("test.py", 1)]
    assert message.auto_comments == ["Test comment"]


def test_save_and_load(po_file, temp_dir):
    """Test saving and loading PO file"""
    # Add test message
    msgid = u"Test message"
    msgstr = u"Test message"  # Example translation
    po_file.add(msgid=msgid, msgstr=msgstr)

    # Save file
    po_file.save()
    assert os.path.exists(po_file.path)

    # Load in new instance
    new_po = POFile(po_file.path)
    new_po.load()

    # Check metadata
    assert po_file.metadata == new_po.metadata

    # Check messages
    assert len(po_file.translations) == len(new_po.translations)
    assert msgid in new_po.translations
    assert new_po.translations[msgid].msgstr == msgstr


def test_update_from_pot(po_file, pot_file):
    """Test updating from POT file"""
    # Add messages to POT
    pot_file.add("Message 1", locations=[("file1.py", 1)])
    pot_file.add("Message 2", locations=[("file2.py", 2)])
    pot_file.save()

    # Add existing translation to PO file
    po_file.add("Message 1", "Message One")
    po_file.save()

    # Update PO from POT
    with POFile(po_file.path, locale="zh_CN") as po:
        po.update(pot_file)

    # Load updated PO file
    updated_po = POFile(po_file.path)
    updated_po.load()

    # Check if existing translation is preserved
    assert "Message 1" in updated_po.translations
    assert updated_po.translations["Message 1"].msgstr == "Message One"

    # Check if new message is added
    assert "Message 2" in updated_po.translations
    assert updated_po.translations["Message 2"].msgstr == ""


def test_header_update(po_file, pot_file):
    """Test header metadata update"""
    # Save initial PO file
    po_file.save()

    # Set different metadata in POT file
    pot_file.metadata[METADATA_KEYS["PROJECT_ID_VERSION"]] = "New Version"
    pot_file.save()

    # Update PO from POT
    with POFile(po_file.path, locale="zh_CN") as po:
        po.update(pot_file)

    # Load updated PO and check metadata
    updated_po = POFile(po_file.path)
    updated_po.load()

    assert (
        updated_po.metadata[METADATA_KEYS["PROJECT_ID_VERSION"]] ==
        "New Version"
    )
    # Language setting should be preserved
    assert (
        updated_po.metadata[METADATA_KEYS["LANGUAGE"]] ==
        "zh_CN"
    )


def test_empty_file_creation(temp_dir):
    """Test empty file creation"""
    po_path = temp_dir / "empty.po"
    with POFile(str(po_path), locale="zh_CN") as po:
        pass

    assert os.path.exists(po_path)

    # Load and verify header
    po = POFile(str(po_path))
    po.load()
    assert "" in po.translations
    assert METADATA_KEYS["LANGUAGE"] in po.metadata
    assert po.metadata[METADATA_KEYS["LANGUAGE"]] == "zh_CN"


@pytest.mark.parametrize("msgid,msgstr", [
    (u"Hello", u"Bonjour"),  # Basic message
    (u"", u""),  # Empty message
    (u"A" * 1000, u"B" * 1000),  # Long message
    (u"Line1\nLine2", u"Ligne1\nLigne2"),  # Multiline message with actual newline
])
def test_message_variants(po_file, msgid, msgstr):
    """Test different types of messages"""
    po_file.add(msgid=msgid, msgstr=msgstr)
    po_file.save()

    loaded_po = POFile(po_file.path)
    loaded_po.load()
    if msgid:  # Skip empty message ID (header) check
        message = loaded_po.get_message(msgid)
        assert message is not None
        assert message.msgstr == msgstr


def test_invalid_header_handling(po_file):
    """Test handling invalid header"""
    # Add an invalid header message
    po_file.translations[""] = Message(msgid="", msgstr="Invalid header")
    po_file.save()

    # Reload file, should reset to valid header
    new_po = POFile(po_file.path)
    new_po.load()

    assert "" in new_po.translations
    assert all(key in new_po.metadata for key in METADATA_KEYS.values())
    assert all(key in new_po.translations[""].msgstr for key in METADATA_KEYS.values())


def test_special_chars_preservation(po_file):
    """Test that special characters are preserved during translation."""
    test_cases = [
        # Escape sequence
        (u"Hello\\nWorld", u"Hello\\nWorld"),
        # Path with quotes
        (u'Path: "C:\\Program Files\\App"', u'Path: "C:\\Program Files\\App"'),
        # HTML escaping
        (u"Text: &quot;Hello&quot;", u"Text: &quot;Hello&quot;"),
        # Mixed cases
        (u'Error in "C:\\temp\\{filename}\\log.txt"', u'Error in "C:\\temp\\{filename}\\log.txt"'),
    ]

    for original, expected in test_cases:
        # Protect special characters
        processed, special_chars = po_file._preserve_special_chars(original)

        # Verify special characters were replaced with markers
        for char in ["\\", '"', "{", "}", "&quot;"]:
            if char in original:
                assert char not in processed

        # Mock translation (directly use expected translation)
        translated = expected

        # Restore special characters
        result = po_file._restore_special_chars(translated, special_chars)

        # Verify special characters were correctly restored
        for char in ["\\", '"', "{", "}", "&quot;"]:
            assert result.count(char) == expected.count(char)


def test_placeholder_preservation(po_file):
    """Test that placeholders are preserved during translation."""
    # Test both {name} and ${name} style placeholders
    original = u"Hello {name}, your balance is ${amount}"
    processed, placeholders = po_file._preserve_placeholders(original)

    # Verify placeholders were replaced with markers
    assert "{name}" not in processed
    assert "${amount}" not in processed
    assert len(placeholders) == 2

    # Simulate translation (replace words but keep markers)
    translated = processed.replace("Hello", "Bonjour").replace("balance", "solde").replace("is", "est")

    # Restore placeholders
    result = po_file._restore_placeholders(translated, placeholders)

    # Verify placeholders are back and text is translated
    assert "{name}" in result
    assert "${amount}" in result
    assert "Bonjour" in result
    assert "solde" in result
