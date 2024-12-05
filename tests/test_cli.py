# -*- coding: utf-8 -*-
"""Test cases for the transx CLI."""
# Import built-in modules
import os
import sys

# Import third-party modules
import pytest

# Import local modules
from transx.api.locale import normalize_language_code
from transx.cli import main
from transx.constants import DEFAULT_CHARSET
from transx.constants import DEFAULT_MESSAGES_DOMAIN
from transx.constants import MO_FILE_EXTENSION
from transx.constants import PO_FILE_EXTENSION
from transx.internal.filesystem import read_file
from transx.internal.filesystem import write_file


@pytest.fixture
def sample_source_dir(tmpdir):
    """Create a sample source directory with Python files for testing."""
    source_dir = os.path.join(str(tmpdir), "src")
    if not os.path.exists(source_dir):
        os.makedirs(source_dir)

    # Create main application file
    app_py = os.path.join(source_dir, "app.py")
    write_file(app_py, """
from transx import tr

def main():
    print(tr("Hello"))
    print(tr("Welcome", context="greeting"))
    print(tr("Goodbye {name}!", name="John"))
""")

    # Create another module file
    utils_py = os.path.join(source_dir, "utils.py")
    write_file(utils_py, """
from transx import tr

def show_messages():
    print(tr("Loading...", context="status"))
    print(tr("Error: {msg}", context="error"))
""")

    return source_dir


def run_cli(*args):
    """Helper function to run CLI commands in tests."""
    old_sys_argv = sys.argv
    try:
        sys.argv = ["transx"] + list(args)
        return main()
    finally:
        sys.argv = old_sys_argv


def test_extract_command(tmpdir, sample_source_dir):
    """Test the extract command with a directory of Python files."""
    output_pot = os.path.join(str(tmpdir), "messages.pot")
    output_dir = os.path.join(str(tmpdir), "locales")

    # Run extract command
    exit_code = run_cli(
        "extract",
        sample_source_dir,
        "-o", output_pot,
        "-p", "Test Project",
        "-v", "1.0",
        "-l", "en,zh_CN",
        "-d", output_dir
    )

    # Verify command execution success
    assert exit_code == 0
    assert os.path.exists(output_pot)

    # Verify POT file content
    content = read_file(output_pot)
    assert "Hello" in content
    assert "Welcome" in content
    assert 'msgctxt "greeting"' in content
    assert "Project-Id-Version: Test Project 1.0" in content
    assert "Content-Type: text/plain; charset={}".format(DEFAULT_CHARSET) in content

    # Verify language files were created
    assert os.path.exists(os.path.join(output_dir, normalize_language_code("en"), "LC_MESSAGES", "messages.po"))
    assert os.path.exists(os.path.join(output_dir, normalize_language_code("zh_CN"), "LC_MESSAGES", "messages.po"))


def test_update_command(tmpdir):
    """Test the update command for creating/updating PO files."""
    # Create example POT file
    messages_pot = os.path.join(str(tmpdir), "messages.pot")
    pot_content = """msgid ""
msgstr ""
"Project-Id-Version: Test Project\\n"
"Content-Type: text/plain; charset={}\\n"

msgid "Hello"
msgstr ""

msgctxt "greeting"
msgid "Welcome"
msgstr ""
""".format(DEFAULT_CHARSET)

    write_file(messages_pot, pot_content)

    # Run update command
    exit_code = run_cli(
        "update",
        messages_pot,
        "-l", "en,zh_CN",
        "-o", str(tmpdir)
    )

    # Verify command execution success
    assert exit_code == 0

    # Verify PO files exist
    en_po_path = os.path.join(str(tmpdir), normalize_language_code("en"), "LC_MESSAGES", DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
    zh_po_path = os.path.join(str(tmpdir), normalize_language_code("zh_CN"), "LC_MESSAGES", DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
    assert os.path.exists(en_po_path)
    assert os.path.exists(zh_po_path)

    # Verify PO file content
    content = read_file(en_po_path)

    # Verify metadata
    assert "Language: en" in content
    assert "Content-Type: text/plain; charset={}".format(DEFAULT_CHARSET) in content

    # Verify message entries
    assert 'msgid "Hello"' in content
    assert 'msgctxt "greeting"' in content
    assert 'msgid "Welcome"' in content


def test_compile_command(tmpdir):
    """Test the compile command for creating MO files."""
    # Create example PO file
    po_dir = os.path.join(str(tmpdir), normalize_language_code("en_US"), "LC_MESSAGES")
    os.makedirs(po_dir)
    po_file = os.path.join(po_dir, DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)

    po_content = """msgid ""
msgstr ""
"Content-Type: text/plain; charset={}\\n"
"Language: en\\n"

msgid "Hello"
msgstr "Hello"

msgctxt "greeting"
msgid "Welcome"
msgstr "Welcome"
""".format(DEFAULT_CHARSET)

    write_file(po_file, po_content)

    # Run compile command
    exit_code = run_cli("compile", po_file)

    # Verify command execution success
    assert exit_code == 0

    # Verify MO file exists
    mo_file = os.path.join(po_dir, DEFAULT_MESSAGES_DOMAIN + MO_FILE_EXTENSION)
    assert os.path.exists(mo_file)


def test_extract_invalid_path(tmpdir):
    """Test extract command with non-existent path."""
    exit_code = run_cli("extract", os.path.join(str(tmpdir), "nonexistent"))
    assert exit_code != 0


def test_update_invalid_pot(tmpdir):
    """Test update command with non-existent POT file."""
    exit_code = run_cli("update", os.path.join(str(tmpdir), "nonexistent.pot"))
    assert exit_code != 0


def test_compile_invalid_po(tmpdir):
    """Test compile command with non-existent PO file."""
    exit_code = run_cli("compile", os.path.join(str(tmpdir), "nonexistent.po"))
    assert exit_code != 0


def test_no_command():
    """Test CLI without any command."""
    with pytest.raises(SystemExit) as exc:
        run_cli()
    assert exc.value.code != 0


def test_list_command(tmpdir):
    """Test the list command for showing available locales."""
    # Create example locale directories with PO files
    locales = ["en_US", "zh_CN", "ja_JP"]
    for locale in locales:
        po_dir = os.path.join(str(tmpdir), normalize_language_code(locale), "LC_MESSAGES")
        os.makedirs(po_dir)
        po_file = os.path.join(po_dir, DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
        write_file(po_file, """msgid ""
msgstr ""
"Content-Type: text/plain; charset={}\\n"
"Language: {}\\n"
""".format(DEFAULT_CHARSET, locale))

    # Run list command
    exit_code = run_cli("list", "-d", str(tmpdir))
    assert exit_code == 0

    # Test with empty directory
    empty_dir = os.path.join(str(tmpdir), "empty")
    os.makedirs(empty_dir)
    exit_code = run_cli("list", "-d", empty_dir)
    assert exit_code == 0

    # Test with non-existent directory
    exit_code = run_cli("list", "-d", os.path.join(str(tmpdir), "nonexistent"))
    assert exit_code == 1


def test_extract_with_empty_source(tmpdir):
    """Test extract command with empty source files."""
    source_dir = os.path.join(str(tmpdir), "empty_src")
    os.makedirs(source_dir)

    # Create empty Python file
    empty_py = os.path.join(source_dir, "empty.py")
    write_file(empty_py, "")

    output_pot = os.path.join(str(tmpdir), "messages.pot")
    exit_code = run_cli("extract", source_dir, "-o", output_pot)
    assert exit_code == 0
    assert os.path.exists(output_pot)


def test_compile_multiple_files(tmpdir):
    """Test compile command with multiple PO files."""
    # Create multiple PO files
    files = []
    for locale in ["en_US", "zh_CN"]:
        po_dir = os.path.join(str(tmpdir), normalize_language_code(locale), "LC_MESSAGES")
        os.makedirs(po_dir)
        po_file = os.path.join(po_dir, DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
        write_file(po_file, """msgid ""
msgstr ""
"Content-Type: text/plain; charset={}\\n"
"Language: {}\\n"
""".format(DEFAULT_CHARSET, locale))
        files.append(po_file)

    # Run compile command with multiple files
    exit_code = run_cli("compile", *files)
    assert exit_code == 0

    # Verify all MO files were created
    for po_file in files:
        mo_file = po_file.replace(PO_FILE_EXTENSION, MO_FILE_EXTENSION)
        assert os.path.exists(mo_file)


def test_update_with_existing_translations(tmpdir):
    """Test update command with existing translations."""
    # Create POT file
    messages_pot = os.path.join(str(tmpdir), "messages.pot")
    pot_content = """msgid ""
msgstr ""
"Project-Id-Version: PROJECT VERSION\\n"
"POT-Creation-Date: 2024-01-01 00:00+0000\\n"
"Content-Type: text/plain; charset={}\\n"

msgid "Hello"
msgstr ""

msgid "Welcome"
msgstr ""

msgid "Old Message"
msgstr ""
""".format(DEFAULT_CHARSET)
    write_file(messages_pot, pot_content)

    # Create existing PO file with translations
    po_dir = os.path.join(str(tmpdir), "zh_CN", "LC_MESSAGES")
    os.makedirs(po_dir)
    po_file = os.path.join(po_dir, DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
    po_content = """msgid ""
msgstr ""
"Project-Id-Version: PROJECT VERSION\\n"
"Language: zh_CN\\n"
"Content-Type: text/plain; charset={}\\n"
"Plural-Forms: nplurals=1; plural=0;\\n"

msgid "Hello"
msgstr "你好"

msgid "Old Message"
msgstr "旧消息"
""".format(DEFAULT_CHARSET)
    write_file(po_file, po_content)

    # Run update command
    exit_code = run_cli("update", messages_pot, "-l", "zh_CN", "-o", str(tmpdir))
    assert exit_code == 0

    # Verify updated PO file content
    content = read_file(po_file)  # Already returns unicode
    assert u'msgstr "你好"' in content  # Existing translation preserved
    assert u'msgid "Welcome"' in content  # New message added
    assert u'msgstr "旧消息"' in content  # Old translation preserved
