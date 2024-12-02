#!/usr/bin/env python
"""Test cases for API module."""

# Import local modules
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
