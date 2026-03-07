#!/usr/bin/env python
"""Test cases for API module."""

# Import third-party modules
from pathlib import Path
from typing import cast

import pytest

# Import local modules
from transx.api.pot import POTFile
from transx.api.pot import PotExtractor

from transx.constants import DEFAULT_CHARSET
from transx.internal.filesystem import read_file
from transx.internal.filesystem import write_file


def _read_text(path: Path) -> str:
    return cast(str, read_file(str(path), encoding=DEFAULT_CHARSET))


def test_pot_extractor(tmp_path: Path):

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
    content = _read_text(pot_file)

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


def test_pot_extractor_supports_default_keywords(tmp_path: Path):

    """All DEFAULT_KEYWORDS should be extractable."""
    test_file = tmp_path / "keywords.py"
    write_file(str(test_file), """
def demo(n):
    print(_("simple"))
    print(gettext("gettext"))
    print(ngettext("item", "items", n))
    print(ugettext("ugettext"))
    print(ungettext("single", "plural", n))
    print(dgettext("domain", "domain message"))
    print(dngettext("domain", "domain single", "domain plural", n))
    print(pgettext("menu", "Open"))
    print(npgettext("menu", "File", "Files", n))
""", encoding=DEFAULT_CHARSET)

    pot_file = tmp_path / "messages.pot"
    with PotExtractor(source_files=[str(test_file)], pot_file=str(pot_file)) as extractor:
        extractor.extract_messages()
        extractor.save()

    content = _read_text(pot_file)

    assert 'msgid "simple"' in content

    assert 'msgid "gettext"' in content
    assert 'msgid "ugettext"' in content
    assert 'msgid "domain message"' in content
    assert 'msgctxt "menu"' in content
    assert 'msgid "Open"' in content
    assert 'msgid "item"' in content
    assert 'msgid_plural "items"' in content
    assert 'msgid "single"' in content
    assert 'msgid_plural "plural"' in content
    assert 'msgid "domain single"' in content
    assert 'msgid_plural "domain plural"' in content
    assert 'msgid "File"' in content
    assert 'msgid_plural "Files"' in content


def test_pot_extractor_additional_keywords_list_and_dict(tmp_path: Path):

    """Support additional keywords provided as list and dict."""
    test_file = tmp_path / "custom_keywords.py"
    write_file(str(test_file), """
def demo(n):
    print(trm("custom", context="custom_context"))
    print(my_pgettext("ctx", "custom_ctx"))
""", encoding=DEFAULT_CHARSET)

    pot_file = tmp_path / "messages.pot"
    with PotExtractor(
        source_files=[str(test_file)],
        pot_file=str(pot_file),
        additional_keywords=["trm"]
    ) as extractor:
        extractor.extract_messages()
        extractor.save()

    dict_pot_file = tmp_path / "messages_dict.pot"
    with PotExtractor(
        source_files=[str(test_file)],
        pot_file=str(dict_pot_file),
        additional_keywords={"my_pgettext": ((1, "c"), 2)}
    ) as extractor:
        extractor.extract_messages()
        extractor.save()

    content = _read_text(pot_file)
    assert 'msgid "custom"' in content
    assert 'msgctxt "custom_context"' in content

    dict_content = _read_text(dict_pot_file)
    assert 'msgid "custom_ctx"' in dict_content

    assert 'msgctxt "ctx"' in dict_content



def test_pot_extractor_invalid_additional_keyword_name(tmp_path: Path):

    """Invalid additional keyword names should raise ValueError."""
    pot_file = tmp_path / "messages.pot"
    with pytest.raises(ValueError) as exc_info:
        _ = PotExtractor(source_files=[], pot_file=str(pot_file), additional_keywords=["invalid-keyword"])
    assert "Invalid keyword name" in str(exc_info.value)




def test_pot_extractor_processes_files_in_deterministic_order(tmp_path: Path):

    """PotExtractor should process source files in sorted order."""
    b_file = tmp_path / "b_file.py"
    a_file = tmp_path / "a_file.py"
    write_file(str(b_file), 'print(tr("BBB"))\n', encoding=DEFAULT_CHARSET)
    write_file(str(a_file), 'print(tr("AAA"))\n', encoding=DEFAULT_CHARSET)

    pot_file = tmp_path / "messages.pot"
    with PotExtractor(
        source_files=[str(b_file), str(a_file)],
        pot_file=str(pot_file)
    ) as extractor:
        extractor.extract_messages()
        extractor.save()

    content = _read_text(pot_file)
    assert content.find('msgid "AAA"') < content.find('msgid "BBB"')



def test_pot_extractor_handles_nested_parentheses_with_top_level_kwargs(tmp_path: Path):
    """Nested calls in args should not terminate tr(...) parsing early."""
    test_file = tmp_path / "nested_calls.py"
    write_file(
        str(test_file),
        """
def build(a, b):
    return a + b


def demo():
    print(tr(build("A", "B"), context="nested_ctx"))
""",
        encoding=DEFAULT_CHARSET,
    )

    pot_file = tmp_path / "messages.pot"
    with PotExtractor(source_files=[str(test_file)], pot_file=str(pot_file)) as extractor:
        extractor.extract_messages()
        extractor.save()

    content = _read_text(pot_file)
    assert 'msgid "AB"' in content
    assert 'msgctxt "nested_ctx"' in content



def test_pot_extractor_ignores_non_literal_context_kwarg(tmp_path: Path):
    """Non-literal context kwargs should not produce fake msgctxt values."""
    test_file = tmp_path / "dynamic_context.py"
    write_file(
        str(test_file),
        """
def demo(ctx):
    print(tr("Hello dynamic", context=ctx))
""",
        encoding=DEFAULT_CHARSET,
    )

    pot_file = tmp_path / "messages.pot"
    with PotExtractor(source_files=[str(test_file)], pot_file=str(pot_file)) as extractor:
        extractor.extract_messages()
        extractor.save()

    content = _read_text(pot_file)
    assert 'msgid "Hello dynamic"' in content
    assert 'msgctxt "{ctx}"' not in content



def test_pot_parse_header_metadata_round_trip_with_continuation():


    """Metadata header parsing should keep valid keys and merge continuation lines."""
    pot = POTFile()

    header = (
        "Project-Id-Version: Demo 1.0\n"
        "X-Unknown-Key: should be ignored\n"
        "Last-Translator: Jane\n"
        " Doe <jane@example.com>\n"
        "Content-Type: text/plain; charset=utf-8\n"
    )


    parsed = pot.parse_header(header)

    assert parsed["Project-Id-Version"] == "Demo 1.0"
    assert parsed["Last-Translator"] == "Jane Doe <jane@example.com>"
    assert parsed["Content-Type"] == "text/plain; charset=utf-8"
    assert "X-Unknown-Key" not in parsed


def test_readme_pot_extractor_workflow_smoke(tmp_path: Path):

    """README extractor workflow should be runnable, including add_source_directory()."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    app_file = src_dir / "app.py"
    write_file(
        str(app_file),
        """
from transx import tr


def main():
    print(tr("Open", context="menu"))
    print(tr("Hello"))
""",
        encoding=DEFAULT_CHARSET,
    )

    pot_file = tmp_path / "messages.pot"
    extractor = PotExtractor(pot_file=str(pot_file), additional_keywords=["trm"])
    extractor.add_source_file(str(app_file))
    extractor.add_source_directory(str(src_dir))
    extractor.extract_messages()
    extractor.save_pot(project="SmokeDemo", version="1.0")

    content = _read_text(pot_file)
    assert 'msgid "Open"' in content
    assert 'msgctxt "menu"' in content
    assert 'msgid "Hello"' in content
    assert "Project-Id-Version: SmokeDemo 1.0" in content


def test_pot_file_save_and_load(tmp_path: Path):
    """Test POTFile save and load round-trip."""
    pot_file = tmp_path / "test.pot"
    pot = POTFile(path=str(pot_file))

    # Add messages
    pot.add("Hello", "Hello", context="greeting")
    pot.add("World", "World")

    # Save
    pot.save()
    assert pot_file.exists()

    # Load into new instance
    pot2 = POTFile(path=str(pot_file))
    pot2.load()

    # Verify messages
    assert "World" in pot2.translations
    assert pot2.translations["World"].msgstr == "World"
    assert "greeting\x04Hello" in pot2.translations
    assert pot2.translations["greeting\x04Hello"].msgstr == "Hello"


def test_pot_file_update_metadata():

    """Test POTFile update_metadata method."""
    pot = POTFile()
    pot.update_metadata({"Project-Id-Version": "Test 1.0", "Language-Team": "Test Team"})

    assert pot.metadata["Project-Id-Version"] == "Test 1.0"
    assert pot.metadata["Language-Team"] == "Test Team"


def test_pot_extractor_save_alias(tmp_path: Path):
    """Test PotExtractor.save() is alias for save_pot()."""
    pot_file = tmp_path / "messages.pot"
    extractor = PotExtractor(pot_file=str(pot_file))
    extractor.save()  # Should not raise

    assert pot_file.exists()


def test_pot_extractor_build_keywords_error():
    """Test PotExtractor raises ValueError for invalid additional_keywords type."""
    with pytest.raises(ValueError) as exc_info:
        PotExtractor(additional_keywords="invalid_string")  # type: ignore
    assert "additional_keywords must be a dict or list/tuple/set" in str(exc_info.value)


def test_pot_extractor_should_skip_string(tmp_path: Path):
    """Test PotExtractor _should_skip_string filters correctly."""
    test_file = tmp_path / "skip_test.py"
    write_file(str(test_file), '''
print(tr("en_US"))  # Should be skipped (language code)
print(tr("locales"))  # Should be skipped (skip literal)
print(tr("http://example.com"))  # Should be skipped (URL)
print(tr("   "))  # Should be skipped (whitespace)
print(tr("123.45"))  # Should be skipped (number)
print(tr("---"))  # Should be skipped (separator)
print(tr("Keep this"))  # Should NOT be skipped
''', encoding=DEFAULT_CHARSET)

    pot_file = tmp_path / "messages.pot"
    extractor = PotExtractor(source_files=[str(test_file)], pot_file=str(pot_file))
    extractor.extract_messages()
    extractor.save()

    content = _read_text(pot_file)
    assert 'msgid "Keep this"' in content
    assert 'msgid "en_US"' not in content
    assert 'msgid "locales"' not in content
    assert 'msgid "http://example.com"' not in content


def test_pot_extractor_add_source_directory_nonexistent(tmp_path: Path):
    """Test add_source_directory handles non-existent directory gracefully."""
    pot_file = tmp_path / "messages.pot"
    extractor = PotExtractor(pot_file=str(pot_file))

    # Should not raise
    extractor.add_source_directory(str(tmp_path / "nonexistent"))
    assert extractor.source_files == []


def test_pot_extractor_context_manager(tmp_path: Path):
    """Test PotExtractor context manager."""
    test_file = tmp_path / "test.py"
    write_file(str(test_file), 'print(tr("Hello"))', encoding=DEFAULT_CHARSET)

    pot_file = tmp_path / "messages.pot"

    with PotExtractor(source_files=[str(test_file)], pot_file=str(pot_file)) as extractor:
        extractor.extract_messages()

    # File should be saved after exiting context
    assert pot_file.exists()
    content = _read_text(pot_file)
    assert 'msgid "Hello"' in content


def test_pot_extractor_copyright_and_bugs_address(tmp_path: Path):
    """Test save_pot with copyright_holder and bugs_address."""
    test_file = tmp_path / "test.py"
    write_file(str(test_file), 'print(tr("Hello"))', encoding=DEFAULT_CHARSET)

    pot_file = tmp_path / "messages.pot"
    extractor = PotExtractor(source_files=[str(test_file)], pot_file=str(pot_file))
    extractor.extract_messages()
    extractor.save_pot(
        project="TestProject",
        version="2.0",
        copyright_holder="Test Corp",
        bugs_address="bugs@test.com"
    )

    content = _read_text(pot_file)
    assert "Project-Id-Version: TestProject 2.0" in content
    assert "Copyright-Holder: Test Corp" in content
    assert "Report-Msgid-Bugs-To: bugs@test.com" in content


def test_pot_file_load_with_comments_and_locations(tmp_path: Path):
    """Test POTFile load with comments, locations and flags."""
    pot_file = tmp_path / "test.pot"
    content = '''# Test header comment
msgid ""
msgstr ""
"Project-Id-Version: Test 1.0\\n"

#. Automatic comment
#: test.py:10
#: test.py:20
#, fuzzy
msgid "Test message"
msgstr "Test translation"

# User comment
msgid "Second message"
msgstr "Second translation"
'''
    write_file(str(pot_file), content, encoding=DEFAULT_CHARSET)

    pot = POTFile(path=str(pot_file))
    pot.load()

    assert "Test message" in pot.translations
    msg = pot.translations["Test message"]
    assert msg.msgstr == "Test translation"
    assert "fuzzy" in msg.flags
    assert len(msg.locations) == 2

    # Second message should NOT have fuzzy flag
    msg2 = pot.translations["Second message"]
    assert "fuzzy" not in msg2.flags





def test_pot_file_multiline_msgid_msgstr(tmp_path: Path):
    """Test POTFile save/load with multiline msgid and msgstr."""
    pot_file = tmp_path / "test.pot"
    pot = POTFile(path=str(pot_file))

    multiline_text = "Line 1\\nLine 2\\nLine 3"
    pot.add(multiline_text, multiline_text)
    pot.save()

    pot2 = POTFile(path=str(pot_file))
    pot2.load()

    assert multiline_text in pot2.translations


def test_pot_file_escape_unescape():
    """Test POTFile escape and unescape methods."""
    pot = POTFile()

    # Test escape
    text = 'Hello "World"\\nNew\\tLine'
    escaped = pot._escape_string(text)
    assert '\\"' in escaped
    assert '\\\\n' in escaped
    assert '\\\\t' in escaped

    # Test unescape
    unescaped = pot._unescape_string('"' + escaped + '"')
    assert unescaped == text


def test_pot_extractor_skip_language_codes(tmp_path: Path):
    """Test that language codes are skipped during extraction."""
    test_file = tmp_path / "lang_test.py"
    write_file(str(test_file), '''
print(tr("zh_CN"))
print(tr("ja_JP"))
print(tr("en_US"))
print(tr("fr_FR"))
print(tr("Keep me"))
''', encoding=DEFAULT_CHARSET)

    pot_file = tmp_path / "messages.pot"
    extractor = PotExtractor(source_files=[str(test_file)], pot_file=str(pot_file))
    extractor.extract_messages()
    extractor.save()

    content = _read_text(pot_file)
    assert 'msgid "Keep me"' in content
    assert 'msgid "zh_CN"' not in content
    assert 'msgid "ja_JP"' not in content
    assert 'msgid "en_US"' not in content
    assert 'msgid "fr_FR"' not in content







