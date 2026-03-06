#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example: use multiple locale roots with TransX."""
# Import future modules
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# Import built-in modules
import os
import tempfile

# Import local modules
from transx import TransX
from transx.api.po import POFile


def _create_po(root, locale, translations):
    """Create a minimal PO file under root/locale/LC_MESSAGES/messages.po."""
    locale_dir = os.path.join(root, locale, "LC_MESSAGES")
    if not os.path.exists(locale_dir):
        os.makedirs(locale_dir)

    po_path = os.path.join(locale_dir, "messages.po")
    po = POFile(po_path, locale=locale)
    for (msgid, context), msgstr in translations.items():
        po.add(msgid, msgstr=msgstr, context=context)
    po.save()


def main():
    """Run multiple locale roots example."""
    workspace = tempfile.mkdtemp(prefix="transx_multi_roots_")
    root_a = os.path.join(workspace, "package_a", "locales")
    root_b = os.path.join(workspace, "package_b", "locales")

    _create_po(root_a, "zh_CN", {
        (u"Open", u"button"): u"打开",
        (u"Hello", None): u"你好",
    })
    _create_po(root_b, "zh_CN", {
        (u"Open", u"menu"): u"打开文件",
        (u"Export", None): u"导出",
    })

    tx = TransX(locales_root=[root_a, root_b], default_locale="zh_CN", auto_compile=False)

    print("locales_root (compat):", tx.locales_root)
    print("locales_roots:", tx.locales_roots)
    print("available_locales:", tx.available_locales)
    print("Hello:", tx.tr("Hello"))
    print("Export:", tx.tr("Export"))

    # Context lookups use translate() in current implementation.
    print("Open(button):", tx.translate("Open", context="button"))
    print("Open(menu):", tx.translate("Open", context="menu"))


if __name__ == "__main__":
    main()
