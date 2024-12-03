#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest

from transx.api.mo import MOFile
from transx.api.po import POFile
from transx.core import TransX
from transx.filesystem import write_file


class TestCoreLoading(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.locale = "zh_CN"
        self.locale_dir = os.path.join(self.temp_dir, self.locale, "LC_MESSAGES")
        os.makedirs(self.locale_dir)
        
        # Create a simple PO file
        self.po_path = os.path.join(self.locale_dir, "messages.po")
        write_file(self.po_path, """msgid ""
msgstr ""
"Project-Id-Version: Test\\n"
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Hello"
msgstr "你好"
""")
        
        # Create TransX instance
        self.transx = TransX(locales_root=self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_po_file_loading(self):
        """Test loading translations from PO file."""
        # Load catalog for zh_CN locale
        self.assertTrue(self.transx.load_catalog(self.locale))
        
        # Test translation
        self.assertEqual(self.transx.translate("Hello"), "你好")
    
    def test_mo_file_loading(self):
        """Test loading translations from MO file."""
        # First create MO file from PO file
        mo_path = os.path.join(self.locale_dir, "messages.mo")
        po = POFile(self.po_path)
        po.load()
        mo = MOFile()
        mo.translations = po.translations
        mo.save(mo_path)
        
        # Create new TransX instance to force MO file loading
        transx = TransX(locales_root=self.temp_dir)
        self.assertTrue(transx.load_catalog(self.locale))
        
        # Test translation
        self.assertEqual(transx.translate("Hello"), "你好")


if __name__ == "__main__":
    unittest.main()
