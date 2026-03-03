#!/usr/bin/env python
"""Test cases for API module."""

# Import third-party modules
import pytest

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


def test_pot_extractor_supports_default_keywords(tmp_path):
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

    content = read_file(str(pot_file), encoding=DEFAULT_CHARSET)

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


def test_pot_extractor_additional_keywords_list_and_dict(tmp_path):
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

    content = read_file(str(pot_file), encoding=DEFAULT_CHARSET)
    assert 'msgid "custom"' in content
    assert 'msgctxt "custom_context"' in content

    dict_content = read_file(str(dict_pot_file), encoding=DEFAULT_CHARSET)
    assert 'msgid "custom_ctx"' in dict_content
    assert 'msgctxt "ctx"' in dict_content



def test_pot_extractor_invalid_additional_keyword_name(tmp_path):
    """Invalid additional keyword names should raise ValueError."""
    pot_file = tmp_path / "messages.pot"
    with pytest.raises(ValueError) as exc_info:
        PotExtractor(source_files=[], pot_file=str(pot_file), additional_keywords=["invalid-keyword"])
    assert "Invalid keyword name" in str(exc_info.value)



def test_pot_extractor_processes_files_in_deterministic_order(tmp_path):
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

    content = read_file(str(pot_file), encoding=DEFAULT_CHARSET)
    assert content.find('msgid "AAA"') < content.find('msgid "BBB"')


