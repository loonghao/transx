#!/usr/bin/env python
"""Test cases for API module."""

# Import local modules
from transx.api.po import POFile
from transx.api.pot import PotExtractor
from transx.api.translate import GoogleTranslator
from transx.constants import DEFAULT_CHARSET
from transx.filesystem import read_file, write_file


def test_pot_extractor(tmp_path):
    """Test POT file extraction."""
    # Create test files
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    
    # Python file
    py_file = test_dir / "test.py"
    write_file(str(py_file), """
def greet():
    print(tr("Hello"))
    print(tr("Welcome", context="greeting"))
""", encoding=DEFAULT_CHARSET)
    
    # HTML file
    html_file = test_dir / "test.html"
    write_file(str(html_file), """
<div>{{ tr("Hello") }}</div>
<div>{{ tr("Welcome", context="greeting") }}</div>
""", encoding=DEFAULT_CHARSET)
    
    # Create POT file path
    pot_file = tmp_path / "messages.pot"
    
    # Create extractor with source files
    source_files = [str(py_file), str(html_file)]
    extractor = PotExtractor(source_files=source_files, pot_file=str(pot_file))
    
    # Extract messages from files
    extractor.extract_messages()
    
    # Save POT file
    extractor.save()
    
    # Verify POT file exists and contains correct content
    assert pot_file.exists()
    content = read_file(str(pot_file), encoding=DEFAULT_CHARSET)
    assert "Hello" in content
    assert "Welcome" in content
    assert 'msgctxt "greeting"' in content
    assert "Project-Id-Version: " in content


def test_po_file_operations(tmp_path):
    """Test PO file operations."""
    po_file = tmp_path / "messages.po"
    
    # Create PO file
    po = POFile(str(po_file))
    
    # Add translations
    po.add(msgid="Hello", msgstr="Hello")  # Basic greeting
    po.add(msgid="Welcome", msgstr="Welcome", context="greeting")  # Contextual greeting
    po.save()
    
    # Read PO file back
    po2 = POFile(str(po_file))
    po2.load()
    assert po2.translations["Hello"].msgstr == "Hello"
    assert po2.translations["greeting\x04Welcome"].msgstr == "Welcome"


def test_auto_translation(tmp_path):
    """Test automatic translation using Google Translator."""
    # Create PO file
    po_file = tmp_path / "messages.po"
    po = POFile(str(po_file))
    
    # Add untranslated messages
    po.add(msgid="Hello", msgstr="")  # Basic greeting
    po.add(msgid="Welcome", msgstr="", context="greeting")  # Contextual greeting
    po.save()
    
    # Create translator
    translator = GoogleTranslator()
    
    # Translate messages
    po.translate_messages(translator=translator, target_lang="fr")  # Translate to French
    
    # Verify translations are not empty
    assert po.translations["Hello"].msgstr != ""
    assert po.translations["greeting\x04Welcome"].msgstr != ""
    
    # Save translated file
    po.save()
    
    # Verify translations persist
    po2 = POFile(str(po_file))
    po2.load()
    assert po2.translations["Hello"].msgstr == po.translations["Hello"].msgstr
    assert po2.translations["greeting\x04Welcome"].msgstr == po.translations["greeting\x04Welcome"].msgstr
