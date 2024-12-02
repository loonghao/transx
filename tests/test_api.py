#!/usr/bin/env python
"""Test cases for API module."""

# Import local modules
from transx.api.mo import _read_mo_file
from transx.api.mo import _read_po_file
from transx.api.mo import compile_po_file
from transx.api.po import POFile
from transx.api.pot import PotExtractor
from transx.constants import DEFAULT_CHARSET


def test_pot_extractor(tmp_path):
    """Test POT file extraction."""
    # Create test files
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    
    # Python file
    py_file = test_dir / "test.py"
    py_file.write_text("""
def greet():
    print(tr("Hello"))
    print(tr("Welcome", context="greeting"))
""", encoding=DEFAULT_CHARSET)
    
    # HTML file
    html_file = test_dir / "test.html"
    html_file.write_text("""
<div>{{ tr("Hello") }}</div>
<div>{{ tr("Welcome", context="greeting") }}</div>
""", encoding=DEFAULT_CHARSET)
    
    # Extract messages
    pot_file = tmp_path / "messages.pot"
    extractor = PotExtractor(str(pot_file))
    extractor.scan_directory(str(test_dir))
    extractor.save_pot(project="Test", version="1.0")
    
    # Verify POT file exists and contains correct content
    assert pot_file.exists()
    content = pot_file.read_text(encoding=DEFAULT_CHARSET)
    assert "Hello" in content
    assert "Welcome" in content
    assert 'msgctxt "greeting"' in content


def test_po_file_operations(tmp_path):
    """Test PO file operations."""
    # Create PO file
    po_file = tmp_path / "messages.po"
    po = POFile(str(po_file))
    
    # Add translations
    po.add_translation("Hello", "你好")
    po.add_translation("Welcome", "欢迎", context="greeting")
    po.add_translation("Goodbye", "再见")
    
    # Save PO file
    po.save()
    
    # Verify PO file exists and contains correct content
    assert po_file.exists()
    content = po_file.read_text(encoding=DEFAULT_CHARSET)
    assert "你好" in content
    assert "欢迎" in content
    assert "再见" in content
    
    # Test loading translations
    new_po = POFile(str(po_file))
    new_po.load()
    assert new_po.get_translation("Hello") == "你好"
    assert new_po.get_translation("Welcome", context="greeting") == "欢迎"
    assert new_po.get_translation("Goodbye") == "再见"


def test_mo_compilation(tmp_path):
    """Test MO file compilation."""
    # Create a test PO file
    po_file = tmp_path / "messages.po"
    po_content = """msgid ""
msgstr ""
"Project-Id-Version: 1.0\\n"
"Language: zh_CN\\n"
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Hello"
msgstr "你好"

msgctxt "greeting"
msgid "Welcome"
msgstr "欢迎"

msgid "Goodbye"
msgstr "再见"
"""
    po_file.write_text(po_content, encoding=DEFAULT_CHARSET)

    # Compile to MO file
    mo_file = tmp_path / "messages.mo"
    compile_po_file(str(po_file), str(mo_file))

    # Verify MO file exists
    assert mo_file.exists()

    # Read back the catalog and verify contents
    catalog, metadata = _read_mo_file(str(mo_file))
    
    # Check translations
    assert catalog.get("Hello") == "你好"
    assert catalog.get("greeting\x04Welcome") == "欢迎"
    assert catalog.get("Goodbye") == "再见"

    # Check metadata
    assert metadata["Project-Id-Version"] == "1.0"
    assert metadata["Language"] == "zh_CN"
    assert metadata["Content-Type"] == "text/plain; charset=UTF-8"


def test_po_to_mo_roundtrip(tmp_path):
    """Test PO to MO conversion roundtrip."""
    # Create source PO file
    po_file = tmp_path / "source.po"
    po_content = """msgid ""
msgstr ""
"Project-Id-Version: 1.0\\n"
"Language: fr\\n"
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Hello"
msgstr "Bonjour"

msgctxt "ui"
msgid "Menu"
msgstr "Menu"

msgid "World"
msgstr "Monde"
"""
    po_file.write_text(po_content, encoding=DEFAULT_CHARSET)

    # Compile to MO
    mo_file = tmp_path / "output.mo"
    compile_po_file(str(po_file), str(mo_file))

    # Create new PO from the same content
    verify_file = tmp_path / "verify.po"
    verify_file.write_text(po_content, encoding=DEFAULT_CHARSET)

    # Read both catalogs
    catalog1, metadata1 = _read_po_file(str(po_file))
    catalog2, metadata2 = _read_po_file(str(verify_file))

    # Compare catalogs
    assert catalog1 == catalog2
    assert metadata1 == metadata2
