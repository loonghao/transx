import os
import pytest
from transx.api.po import POFile
from transx.api.message import Message
from transx.constants import METADATA_KEYS


@pytest.fixture
def temp_dir(tmp_path):
    """提供临时目录"""
    return tmp_path


@pytest.fixture
def po_file(temp_dir):
    """提供一个基本的 PO 文件实例"""
    po_file_path = temp_dir / "test.po"
    return POFile(str(po_file_path), locale="zh_CN")


@pytest.fixture
def pot_file(temp_dir):
    """提供一个基本的 POT 文件实例"""
    pot_file_path = temp_dir / "test.pot"
    pot = POFile(str(pot_file_path))
    return pot


def test_init_metadata(po_file):
    """测试元数据初始化"""
    assert METADATA_KEYS["PROJECT_ID_VERSION"] in po_file.metadata
    assert METADATA_KEYS["LANGUAGE"] in po_file.metadata
    assert po_file.metadata[METADATA_KEYS["LANGUAGE"]] == "zh_CN"
    assert "" in po_file.translations  # 头部消息应该存在
    # 检查所有元数据键是否在头部消息中
    assert all(key in po_file.translations[""].msgstr for key in METADATA_KEYS.values())


def test_add_message(po_file):
    """测试添加新消息"""
    msgid = "Hello, world!"
    msgstr = "你好，世界！"
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
    """测试保存和加载 PO 文件"""
    # 添加测试消息
    msgid = "Test message"
    msgstr = "测试消息"
    po_file.add(msgid=msgid, msgstr=msgstr)

    # 保存文件
    po_file.save()
    assert os.path.exists(po_file.path)

    # 在新实例中加载
    new_po = POFile(po_file.path)
    new_po.load()

    # 检查元数据
    assert po_file.metadata == new_po.metadata
    
    # 检查消息
    assert len(po_file.translations) == len(new_po.translations)
    assert msgid in new_po.translations
    assert new_po.translations[msgid].msgstr == msgstr


def test_update_from_pot(po_file, pot_file):
    """测试从 POT 文件更新"""
    # 在 POT 中添加消息
    pot_file.add("Message 1", locations=[("file1.py", 1)])
    pot_file.add("Message 2", locations=[("file2.py", 2)])
    pot_file.save()

    # 在 PO 文件中添加一个已有翻译
    po_file.add("Message 1", "消息1")
    po_file.save()

    # 从 POT 更新 PO
    with POFile(po_file.path, locale="zh_CN") as po:
        po.update(pot_file)

    # 加载更新后的 PO 文件
    updated_po = POFile(po_file.path)
    updated_po.load()

    # 检查现有翻译是否保留
    assert "Message 1" in updated_po.translations
    assert updated_po.translations["Message 1"].msgstr == "消息1"
    
    # 检查新消息是否添加
    assert "Message 2" in updated_po.translations
    assert updated_po.translations["Message 2"].msgstr == ""


def test_context_manager(po_file):
    """测试上下文管理器功能"""
    msgid = "Context test"
    msgstr = "上下文测试"
    
    with POFile(po_file.path, locale="zh_CN") as po:
        po.add(msgid, msgstr)
    
    # 文件应该自动保存
    assert os.path.exists(po_file.path)
    
    # 加载并验证
    new_po = POFile(po_file.path)
    new_po.load()
    assert msgid in new_po.translations
    assert new_po.translations[msgid].msgstr == msgstr


def test_header_update(po_file, pot_file):
    """测试头部元数据更新"""
    # 保存初始 PO 文件
    po_file.save()

    # 在 POT 文件中设置不同的元数据
    pot_file.metadata[METADATA_KEYS["PROJECT_ID_VERSION"]] = "New Version"
    pot_file.save()

    # 从 POT 更新 PO
    with POFile(po_file.path, locale="zh_CN") as po:
        po.update(pot_file)

    # 加载更新后的 PO 并检查元数据
    updated_po = POFile(po_file.path)
    updated_po.load()
    
    assert (
        updated_po.metadata[METADATA_KEYS["PROJECT_ID_VERSION"]] == 
        "New Version"
    )
    # 语言设置应该保留
    assert (
        updated_po.metadata[METADATA_KEYS["LANGUAGE"]] == 
        "zh_CN"
    )


def test_empty_file_creation(temp_dir):
    """测试创建空文件"""
    po_path = temp_dir / "empty.po"
    with POFile(str(po_path), locale="zh_CN") as po:
        pass
    
    assert os.path.exists(po_path)
    
    # 加载并验证头部
    po = POFile(str(po_path))
    po.load()
    assert "" in po.translations
    assert METADATA_KEYS["LANGUAGE"] in po.metadata
    assert po.metadata[METADATA_KEYS["LANGUAGE"]] == "zh_CN"


def test_invalid_header_handling(po_file):
    """测试处理无效的头部"""
    # 添加一个无效的头部消息
    po_file.translations[""] = Message(msgid="", msgstr="Invalid header")
    po_file.save()
    
    # 重新加载文件，应该重置为有效的头部
    new_po = POFile(po_file.path)
    new_po.load()
    
    assert "" in new_po.translations
    assert all(key in new_po.metadata for key in METADATA_KEYS.values())
    assert all(key in new_po.translations[""].msgstr for key in METADATA_KEYS.values())


@pytest.mark.parametrize("msgid,msgstr", [
    ("Hello", "你好"),
    ("", ""),  # 测试空消息
    ("A" * 1000, "B" * 1000),  # 测试长消息
    ("Line1\\nLine2", "行1\\n行2"),  # 测试多行消息
])
def test_message_variants(po_file, msgid, msgstr):
    """测试不同类型的消息"""
    po_file.add(msgid=msgid, msgstr=msgstr)
    po_file.save()
    
    loaded_po = POFile(po_file.path)
    loaded_po.load()
    
    if msgid:  # 跳过空消息ID（头部）的检查
        assert loaded_po.translations[msgid].msgstr == msgstr
