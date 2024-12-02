"""Test cases for the transx CLI."""
# Import built-in modules
import os
import sys

# Import third-party modules
import pytest

# Import local modules
from transx.cli import main
from transx.constants import DEFAULT_CHARSET
from transx.constants import DEFAULT_MESSAGES_DOMAIN
from transx.constants import MO_FILE_EXTENSION
from transx.constants import PO_FILE_EXTENSION


@pytest.fixture
def sample_source_dir(tmp_path):
    """Create a sample source directory with Python files for testing."""
    # 创建示例Python文件
    source_dir = tmp_path / "src"
    source_dir.mkdir()

    # 创建主应用文件
    app_py = source_dir / "app.py"
    app_py.write_text("""
from transx import tr

def main():
    print(tr("Hello"))
    print(tr("Welcome", context="greeting"))
    print(tr("Goodbye {name}!", name="John"))
""")

    # 创建另一个模块文件
    utils_py = source_dir / "utils.py"
    utils_py.write_text("""
from transx import tr

def show_messages():
    print(tr("Loading...", context="status"))
    print(tr("Error: {msg}", context="error"))
""")

    return str(source_dir)

def run_cli(*args):
    """Helper function to run CLI commands in tests."""
    old_sys_argv = sys.argv
    try:
        sys.argv = ["transx"] + list(args)
        return main()
    finally:
        sys.argv = old_sys_argv

def test_extract_command(sample_source_dir, tmp_path):
    """Test the extract command with a directory of Python files."""
    output_pot = tmp_path / "messages.pot"

    # 运行提取命令
    exit_code = run_cli(
        "extract",
        sample_source_dir,
        "--output", str(output_pot),
        "--project", "Test Project",
        "--version", "1.0"
    )

    # 验证命令执行成功
    assert exit_code == 0
    assert output_pot.exists()

    # 验证POT文件内容
    pot_content = output_pot.read_text(encoding=DEFAULT_CHARSET)

    # 验证元数据
    assert "Project-Id-Version: Test Project 1.0" in pot_content
    assert f"Content-Type: text/plain; charset={DEFAULT_CHARSET}" in pot_content

    # 验证消息条目
    assert 'msgid "Hello"' in pot_content
    assert 'msgctxt "greeting"' in pot_content
    assert 'msgid "Welcome"' in pot_content
    assert 'msgid "Goodbye {name}!"' in pot_content
    assert 'msgctxt "status"' in pot_content
    assert 'msgid "Loading..."' in pot_content
    assert 'msgctxt "error"' in pot_content
    assert 'msgid "Error: {msg}"' in pot_content

def test_update_command(tmp_path):
    """Test the update command for creating/updating PO files."""
    # 创建示例POT文件
    messages_pot = tmp_path / "messages.pot"
    messages_pot.write_text(f"""msgid ""
msgstr ""
"Project-Id-Version: Test Project\\n"
"Content-Type: text/plain; charset={DEFAULT_CHARSET}\\n"

msgid "Hello"
msgstr ""

msgctxt "greeting"
msgid "Welcome"
msgstr ""
""")

    # 运行更新命令
    exit_code = run_cli(
        "update",
        str(messages_pot),
        "en", "zh_CN",
        "--output-dir", str(tmp_path)
    )

    # 验证命令执行成功
    assert exit_code == 0
    po_path = os.path.join("en", "LC_MESSAGES", DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
    assert (tmp_path / po_path).exists()
    po_path = os.path.join("zh_CN", "LC_MESSAGES", DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
    assert (tmp_path / po_path).exists()

    # 验证PO文件内容
    po_path = os.path.join("en", "LC_MESSAGES", DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
    en_po = tmp_path / po_path
    po_content = en_po.read_text(encoding=DEFAULT_CHARSET)

    # 验证元数据
    assert "Language: en" in po_content
    assert f"Content-Type: text/plain; charset={DEFAULT_CHARSET}" in po_content

    # 验证消息条目
    assert 'msgid "Hello"' in po_content
    assert 'msgctxt "greeting"' in po_content
    assert 'msgid "Welcome"' in po_content

def test_compile_command(tmp_path):
    """Test the compile command for creating MO files."""
    # 创建示例PO文件
    po_dir = tmp_path / "en" / "LC_MESSAGES"
    po_dir.mkdir(parents=True)
    po_file = po_dir / (DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
    po_file.write_text(f"""msgid ""
msgstr ""
"Content-Type: text/plain; charset={DEFAULT_CHARSET}\\n"
"Language: en\\n"

msgid "Hello"
msgstr "Hello"

msgctxt "greeting"
msgid "Welcome"
msgstr "Welcome"
""")

    # 运行编译命令
    exit_code = run_cli("compile", str(po_file))

    # 验证命令执行成功
    assert exit_code == 0
    mo_path = DEFAULT_MESSAGES_DOMAIN + MO_FILE_EXTENSION
    assert (po_dir / mo_path).exists()

def test_extract_invalid_path(tmp_path):
    """Test extract command with non-existent path."""
    exit_code = run_cli("extract", "/nonexistent/path")
    assert exit_code == 1

def test_update_invalid_pot(tmp_path):
    """Test update command with non-existent POT file."""
    exit_code = run_cli("update", "/nonexistent/messages.pot", "en")
    assert exit_code == 1

def test_compile_invalid_po(tmp_path):
    """Test compile command with non-existent PO file."""
    exit_code = run_cli("compile", "/nonexistent/messages.po")
    assert exit_code == 1

def test_no_command():
    """Test CLI without any command."""
    exit_code = run_cli()
    assert exit_code == 1
