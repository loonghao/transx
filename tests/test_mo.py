#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test MO file reading."""

# Import built-in modules
import os

# Import third-party modules
import pytest

# Import local modules
from transx.api.mo import MOFile
from transx.internal.compat import PY2
from transx.internal.compat import ensure_unicode


def test_mo_file_reading(test_data_dir):
    """Test reading MO file with Chinese characters."""
    mo_file_path = os.path.join(test_data_dir, "locales", "zh_CN", "messages.mo")

    # Test file exists
    assert os.path.exists(mo_file_path), "MO file not found at %s" % mo_file_path

    # Open file in binary mode and test reading
    with open(mo_file_path, "rb") as f:
        mo = MOFile(f)

    # Test that translations dictionary is not empty
    assert mo.translations, "No translations found in MO file"

    # Expected translations (a subset of all translations)
    expected_translations = {
        u"": u"Project-Id-Version: TransX Demo 1.0\n"
            u"Report-Msgid-Bugs-To: transx@example.com\n"
            u"POT-Creation-Date: 2024-12-05 00:06+0800\n"
            u"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
            u"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
            u"Language: zh_CN\n"
            u"Language-Team: zh_CN <LL@li.org>\n"
            u"Plural-Forms: nplurals=1; plural=0;\n"
            u"MIME-Version: 1.0\n"
            u"Content-Type: text/plain; charset=utf-8\n"
            u"Content-Transfer-Encoding: 8bit\n"
            u"Generated-By: Babel 2.16.0\n",
        u"    导出帧数集": u"导出帧数集",
        u"    我们的文件": u"我们的文件",
        u"  一键导出动画 ": u"一键导出动画",
        u"  一键导出蒙皮 ": u"一键导出蒙皮",
        u"  创建 动画 选择集": u"创建 动画 选择集",
        u"  创建 蒙皮 选择集": u"创建 蒙皮 选择集",
        u"  导出相机": u"导出相机",
        u"  批量导出蒙皮和动画 ": u"批量导出蒙皮和动画",
        u"  蒙皮添加Root_r ": u"蒙皮添加Root_r",
        u"  骨骼添加Root_r": u"骨骼添加Root_r",
    }

    # Test specific translations
    for msgid, expected_msgstr in expected_translations.items():
        # Convert msgid to text_type for comparison
        msgid_key = ensure_unicode(msgid) if isinstance(msgid, str) else msgid
        assert msgid_key in mo.translations, "Missing translation for: %s" % msgid
        actual_msgstr = mo.translations[msgid_key].msgstr

        # Ensure proper encoding for comparison
        if PY2:
            expected_msgstr = ensure_unicode(expected_msgstr)
            actual_msgstr = ensure_unicode(actual_msgstr)

        assert actual_msgstr == expected_msgstr, \
            "Translation mismatch for '%s'\nExpected: %s\nActual: %s" % (
                msgid, expected_msgstr, actual_msgstr)

    # Test encoding handling
    for msgid, message in mo.translations.items():
        # Ensure all strings can be properly encoded/decoded
        if PY2:
            try:
                ensure_unicode(msgid).encode("utf-8")
                ensure_unicode(message.msgstr).encode("utf-8")
            except UnicodeEncodeError as e:
                pytest.fail("Failed to encode/decode: %s" % str(e))
