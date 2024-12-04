#!/usr/bin/env python
"""Test cases for API module."""

# Import local modules
from transx.api.pot import PotExtractor
from transx.constants import DEFAULT_CHARSET
from transx.internal.filesystem import read_file
from transx.internal.filesystem import write_file


def test_pot_extractor(tmp_path):
    """Test POT file extraction."""
    # Create test files
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Python file with various translation patterns
    py_file = test_dir / "test.py"
    write_file(str(py_file), """
def greet():
    # Simple translation
    print(tr("Hello"))

    # Translation with context
    print(tr("Welcome", context="greeting"))

    # Translation with parameters
    print(tr("Hello, {name}!", name="Alice"))

    # Translation with environment variables
    print(tr("Current user: $USER"))

    # Translation with escaped dollar sign
    print(tr("Price: $$100"))
""", encoding=DEFAULT_CHARSET)

    # HTML file with template syntax
    html_file = test_dir / "test.html"
    write_file(str(html_file), """
<div>
    <!-- Simple translation -->
    <p>{{ tr("Hello") }}</p>

    <!-- Translation with context -->
    <p>{{ tr("Welcome", context="greeting") }}</p>

    <!-- Translation with parameters -->
    <p>{{ tr("Hello, {name}!", name=user_name) }}</p>

    <!-- Translation with environment variables -->
    <p>{{ tr("Current path: $PATH") }}</p>

    <!-- Translation with escaped dollar sign -->
    <p>{{ tr("Total: $$50") }}</p>
</div>
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

    # Verify basic translations are extracted
    assert 'msgid "Hello"' in content
    assert 'msgid "Welcome"' in content
    assert 'msgid "Hello, {name}!"' in content

    # Verify context is preserved
    assert 'msgctxt "greeting"' in content

    # Verify environment variables are preserved
    assert 'msgid "Current user: $USER"' in content
    assert 'msgid "Current path: $PATH"' in content

    # Verify escaped dollar signs are preserved
    assert 'msgid "Price: $$100"' in content
    assert 'msgid "Total: $$50"' in content

    # Verify metadata is present
    assert "Project-Id-Version: " in content
    assert "POT-Creation-Date: " in content
    assert "Content-Type: text/plain; charset=utf-8" in content
