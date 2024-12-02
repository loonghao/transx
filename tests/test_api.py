#!/usr/bin/env python
"""Test cases for API module."""

# Import local modules
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
    # Create a test PO file
    po_file = tmp_path / "messages.po"
    po_content = """msgid ""
msgstr ""
"Project-Id-Version: TransX 1.0\\n"
"PO-Revision-Date: 2024-12-02 08:42+0000\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Generated-By: TransX\\n"
"Language: zh_CN\\n"

#. Greeting message
msgid "Hello"
msgstr "你好"

#. Welcome message
msgctxt "greeting"
msgid "Welcome"
msgstr "欢迎"

msgid "Goodbye"
msgstr "再见"

#. Special characters test
msgid "Hello\\nWorld"
msgstr "你好\\n世界"

msgid "Tab\\here"
msgstr "制表符\\t在这里"
"""
    po_file.write_text(po_content, encoding=DEFAULT_CHARSET)

    # Test loading
    po = POFile(str(po_file), locale="zh_CN")
    po.load()

    # Check metadata
    assert po.metadata["Project-Id-Version"] == "TransX 1.0"
    assert po.metadata["Language"] == "zh_CN"
    assert po.metadata["Content-Type"] == "text/plain; charset=utf-8"

    # Check translations
    assert po.get_translation("Hello") == "你好"
    assert po.get_translation("Welcome", context="greeting") == "欢迎"
    assert po.get_translation("Goodbye") == "再见"
    assert po.get_translation("Hello\nWorld") == "你好\n世界"
    assert po.get_translation("Tab\there") == "制表符\t在这里"

    # Test saving to a new file
    new_po_file = tmp_path / "new_messages.po"
    po.save(str(new_po_file))

    # Load the saved file and verify
    new_po = POFile(str(new_po_file))
    new_po.load()

    # Check metadata in new file
    assert new_po.metadata["Project-Id-Version"] == "TransX 1.0"
    assert new_po.metadata["Language"] == "zh_CN"

    # Check translations in new file
    assert new_po.get_translation("Hello") == "你好"
    assert new_po.get_translation("Welcome", context="greeting") == "欢迎"
    assert new_po.get_translation("Goodbye") == "再见"
    assert new_po.get_translation("Hello\nWorld") == "你好\n世界"
    assert new_po.get_translation("Tab\there") == "制表符\t在这里"


def test_po_to_mo_roundtrip(tmp_path):
    """Test PO to MO conversion roundtrip."""
    # Create source PO file
    po_file = tmp_path / "messages.po"
    po_content = """msgid ""
msgstr ""
"Project-Id-Version: TransX 1.0\\n"
"PO-Revision-Date: 2024-12-02 08:42+0000\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Generated-By: TransX\\n"
"Language: zh_CN\\n"

msgid "Analyzing results"
msgstr "分析结果"

msgid "Error: File not found"
msgstr "错误：未找到文件"

msgid "Hello"
msgstr "你好"

msgid "Starting workflow"
msgstr "启动工作流程"

msgid "Task completed successfully"
msgstr "任务已成功完成"

msgid "Validating input data"
msgstr "验证输入数据"

msgid "Warning: Low disk space"
msgstr "警告：磁盘空间不足"

msgid "Workflow completed"
msgstr "工作流程已完成"

msgid "Hello\\nWorld"
msgstr "你好\\n世界"

msgid "Tab\\here"
msgstr "制表符\\t在这里"
"""
    po_file.write_text(po_content, encoding=DEFAULT_CHARSET)

    # Compile to MO file
    mo_file = tmp_path / "messages.mo"
    compile_po_file(str(po_file), str(mo_file))

    # Verify MO file exists
    assert mo_file.exists()

    # Create a new PO file from the MO file
    new_po_file = tmp_path / "new_messages.po"
    new_po = POFile(str(new_po_file))

    # Load translations from MO file
    with open(str(mo_file), "rb") as f:
        catalog, metadata = MOFile()._parse(f)
        for msgid, msgstr in catalog.items():
            new_po.add_translation(msgid, msgstr)
        new_po.metadata.update(metadata)

    new_po.save()

    # Compare original and new PO files
    orig_po = POFile(str(po_file))
    orig_po.load()

    # Check metadata
    assert new_po.metadata["Project-Id-Version"] == orig_po.metadata["Project-Id-Version"]
    assert new_po.metadata["Language"] == orig_po.metadata["Language"]
    assert new_po.metadata["Content-Type"] == orig_po.metadata["Content-Type"]

    # Check translations
    assert new_po.get_translation("Analyzing results") == "分析结果"
    assert new_po.get_translation("Error: File not found") == "错误：未找到文件"
    assert new_po.get_translation("Hello") == "你好"
    assert new_po.get_translation("Starting workflow") == "启动工作流程"
    assert new_po.get_translation("Task completed successfully") == "任务已成功完成"
    assert new_po.get_translation("Validating input data") == "验证输入数据"
    assert new_po.get_translation("Warning: Low disk space") == "警告：磁盘空间不足"
    assert new_po.get_translation("Workflow completed") == "工作流程已完成"
    assert new_po.get_translation("Hello\nWorld") == "你好\n世界"
    assert new_po.get_translation("Tab\there") == "制表符\t在这里"
