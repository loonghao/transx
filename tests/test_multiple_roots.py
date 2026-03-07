#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for multiple locale roots support (Issue #29)."""
# Import built-in modules
import logging
import os

# Import third-party modules
import pytest

# Import local modules
from transx import TransX
from transx.api.mo import compile_po_file
from transx.api.po import POFile


def _create_locale(root, locale, translations, compile_mo=True):

    """Helper: create PO (and optionally MO) files under *root*/*locale*/LC_MESSAGES/.

    Args:
        root: Root directory path.
        locale: Locale code (e.g. 'zh_CN').
        translations: dict mapping (msgid, context) -> msgstr.
        compile_mo: Whether to compile PO -> MO.
    """
    locale_dir = os.path.join(root, locale, "LC_MESSAGES")
    try:
        os.makedirs(locale_dir)
    except OSError:
        if not os.path.isdir(locale_dir):
            raise

    po_path = os.path.join(locale_dir, "messages.po")
    po = POFile(po_path, locale=locale)
    for (msgid, context), msgstr in translations.items():
        po.add(msgid, msgstr=msgstr, context=context)
    po.save()

    if compile_mo:
        mo_path = os.path.join(locale_dir, "messages.mo")
        compile_po_file(po_path, mo_path)


@pytest.fixture
def multi_root_dir(tmp_path):
    """Create a temporary directory structure with multiple locale roots."""
    root_a = os.path.join(str(tmp_path), "pkg_a", "locales")
    root_b = os.path.join(str(tmp_path), "pkg_b", "locales")
    root_c = os.path.join(str(tmp_path), "pkg_c", "locales")
    os.makedirs(root_a)
    os.makedirs(root_b)
    os.makedirs(root_c)
    return root_a, root_b, root_c


# ---------------------------------------------------------------------------
# T-01: Single string path (backward compatibility)
# ---------------------------------------------------------------------------
class TestSingleRoot:
    """Verify that passing a single string behaves identically to the old API."""

    def test_single_string_path(self, tmp_path):
        """T-01: Single str locales_root works exactly as before."""
        root = os.path.join(str(tmp_path), "locales")
        os.makedirs(root)
        _create_locale(root, "ja_JP", {
            (u"Hello", None): u"こんにちは",
        })

        tx = TransX(locales_root=root, default_locale="ja_JP")
        assert tx.locales_root == root
        assert tx.locales_roots == [root]
        assert tx.tr("Hello") == u"こんにちは"

    def test_none_defaults(self):
        """T-02: None falls back to default locales dir."""
        tx = TransX(locales_root=None, default_locale="en_US")
        assert os.path.basename(tx.locales_root) == "locales"
        assert len(tx.locales_roots) == 1

    def test_locales_root_backward_compat(self, tmp_path):
        """self.locales_root (singular) points to the first valid root."""
        root_a = os.path.join(str(tmp_path), "a")
        root_b = os.path.join(str(tmp_path), "b")
        os.makedirs(root_a)
        os.makedirs(root_b)

        tx = TransX(locales_root=[root_a, root_b], default_locale="en_US")
        assert tx.locales_root == root_a
        assert tx.locales_roots == [root_a, root_b]


# ---------------------------------------------------------------------------
# T-03 ~ T-06: Multiple roots - merging
# ---------------------------------------------------------------------------
class TestMultipleRoots:
    """Verify multi-root loading and first-wins merge strategy."""

    def test_list_of_roots(self, multi_root_dir):
        """T-03: List input loads translations from all roots."""
        root_a, root_b, _root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {
            (u"Hello", None): u"你好",
        })
        _create_locale(root_b, "zh_CN", {
            (u"Goodbye", None): u"再见",
        })

        tx = TransX(locales_root=[root_a, root_b], default_locale="zh_CN")
        assert tx.tr("Hello") == u"你好"
        assert tx.tr("Goodbye") == u"再见"

    def test_tuple_of_roots(self, multi_root_dir):
        """T-04: Tuple input also works."""
        root_a, root_b, _root_c = multi_root_dir

        _create_locale(root_a, "ja_JP", {
            (u"Hello", None): u"こんにちは",
        })
        _create_locale(root_b, "ja_JP", {
            (u"World", None): u"世界",
        })

        tx = TransX(locales_root=(root_a, root_b), default_locale="ja_JP")
        assert tx.tr("Hello") == u"こんにちは"
        assert tx.tr("World") == u"世界"

    def test_first_wins_same_translation(self, multi_root_dir):
        """T-05: Duplicate msgid with identical msgstr - silently accepted."""
        root_a, root_b, _root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {(u"OK", None): u"确定"})
        _create_locale(root_b, "zh_CN", {(u"OK", None): u"确定"})

        tx = TransX(locales_root=[root_a, root_b], default_locale="zh_CN")
        assert tx.tr("OK") == u"确定"

    def test_first_wins_different_translation(self, multi_root_dir, caplog):
        """T-06: Duplicate msgid with different msgstr - first wins + WARNING."""
        root_a, root_b, _root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {(u"Open", None): u"打开"})
        _create_locale(root_b, "zh_CN", {(u"Open", None): u"开启"})

        with caplog.at_level(logging.WARNING):
            tx = TransX(locales_root=[root_a, root_b], default_locale="zh_CN")

        # First-wins: root_a's translation is kept
        assert tx.tr("Open") == u"打开"
        # Verify warning was logged
        assert any("Duplicate msgid conflict" in r.message for r in caplog.records)

    def test_first_wins_with_context(self, multi_root_dir, caplog):
        """Duplicate msgid+context with different msgstr - first wins + WARNING.

        Uses PO-only mode and translate() to properly test context merging,
        since the current MO compilation does not encode msgctxt into binary.
        """
        root_a, root_b, _root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {(u"Open", u"button"): u"打开"}, compile_mo=False)
        _create_locale(root_b, "zh_CN", {(u"Open", u"button"): u"开启"}, compile_mo=False)

        with caplog.at_level(logging.WARNING):
            tx = TransX(locales_root=[root_a, root_b], default_locale="zh_CN", auto_compile=False)

        assert tx.translate("Open", context="button") == u"打开"
        conflict_records = [r for r in caplog.records if "Duplicate msgid conflict" in r.message]
        assert len(conflict_records) >= 1
        assert any("button" in r.message for r in conflict_records)


# ---------------------------------------------------------------------------
# T-07: Non-existent root paths
# ---------------------------------------------------------------------------
class TestNonExistentRoots:
    """Verify behavior when some roots don't exist."""

    def test_skip_nonexistent_roots(self, multi_root_dir):
        """T-07: Non-existent paths are skipped; valid paths still work."""
        root_a, _root_b, _root_c = multi_root_dir
        nonexistent = os.path.join(os.path.dirname(root_a), "nonexistent")

        _create_locale(root_a, "zh_CN", {(u"Hello", None): u"你好"})

        tx = TransX(locales_root=[nonexistent, root_a], default_locale="zh_CN")
        assert tx.tr("Hello") == u"你好"

    def test_all_nonexistent_roots(self, tmp_path):
        """All roots are nonexistent - graceful fallback."""
        p1 = os.path.join(str(tmp_path), "nope1")
        p2 = os.path.join(str(tmp_path), "nope2")

        tx = TransX(locales_root=[p1, p2], default_locale="en_US")
        # Should not crash; just return original text
        assert tx.tr("Hello") == "Hello"


# ---------------------------------------------------------------------------
# T-08: available_locales union
# ---------------------------------------------------------------------------
class TestAvailableLocales:
    """Verify available_locales returns the union across all roots."""

    def test_union_of_locales(self, multi_root_dir):
        """T-08: available_locales is the sorted union from all roots."""
        root_a, root_b, root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {(u"A", None): u"A"})
        _create_locale(root_b, "ja_JP", {(u"B", None): u"B"})
        _create_locale(root_c, "ko_KR", {(u"C", None): u"C"})

        tx = TransX(locales_root=[root_a, root_b, root_c], default_locale="en_US")
        locales = tx.available_locales
        assert "zh_CN" in locales
        assert "ja_JP" in locales
        assert "ko_KR" in locales

    def test_dedup_locales(self, multi_root_dir):
        """Same locale in multiple roots appears only once."""
        root_a, root_b, _root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {(u"A", None): u"A"})
        _create_locale(root_b, "zh_CN", {(u"B", None): u"B"})

        tx = TransX(locales_root=[root_a, root_b], default_locale="en_US")
        assert tx.available_locales.count("zh_CN") == 1


# ---------------------------------------------------------------------------
# T-09: switch_locale across roots
# ---------------------------------------------------------------------------
class TestSwitchLocale:
    """Verify locale switching loads from all roots."""

    def test_switch_locale_multi_root(self, multi_root_dir):
        """T-09: switch_locale loads merged catalog for new locale."""
        root_a, root_b, _root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {(u"Hello", None): u"你好"})
        _create_locale(root_b, "zh_CN", {(u"World", None): u"世界"})
        _create_locale(root_a, "ja_JP", {(u"Hello", None): u"こんにちは"})
        _create_locale(root_b, "ja_JP", {(u"World", None): u"世界"})

        tx = TransX(locales_root=[root_a, root_b], default_locale="zh_CN")
        assert tx.tr("Hello") == u"你好"
        assert tx.tr("World") == u"世界"

        tx.switch_locale("ja_JP")
        assert tx.tr("Hello") == u"こんにちは"
        assert tx.tr("World") == u"世界"


# ---------------------------------------------------------------------------
# T-10: Mixed PO / MO file formats
# ---------------------------------------------------------------------------
class TestMixedFormats:
    """Verify roots with only PO or only MO files."""

    def test_po_only_root(self, multi_root_dir):
        """T-10a: Root with only PO files (no MO) still loads."""
        root_a, root_b, _root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {(u"Hello", None): u"你好"}, compile_mo=False)
        _create_locale(root_b, "zh_CN", {(u"World", None): u"世界"})

        tx = TransX(locales_root=[root_a, root_b], default_locale="zh_CN", auto_compile=False)
        assert tx.tr("Hello") == u"你好"
        assert tx.tr("World") == u"世界"


# ---------------------------------------------------------------------------
# T-11: Context disambiguation across roots
# ---------------------------------------------------------------------------
class TestContextAcrossRoots:
    """Verify msgctxt is properly handled in multi-root merge."""

    def test_different_context_different_roots(self, multi_root_dir):
        """T-11: Same msgid with different contexts from different roots.

        Uses PO-only mode and translate() to properly test context disambiguation.
        """
        root_a, root_b, _root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {(u"Open", u"button"): u"打开"}, compile_mo=False)
        _create_locale(root_b, "zh_CN", {(u"Open", u"menu"): u"打开文件"}, compile_mo=False)

        tx = TransX(locales_root=[root_a, root_b], default_locale="zh_CN", auto_compile=False)
        assert tx.translate("Open", context="button") == u"打开"
        assert tx.translate("Open", context="menu") == u"打开文件"


# ---------------------------------------------------------------------------
# T-12: strict_mode interaction
# ---------------------------------------------------------------------------
class TestStrictMode:
    """Verify strict_mode behavior with multiple roots."""

    def test_strict_mode_at_least_one_root_has_locale(self, multi_root_dir):
        """T-12a: strict_mode doesn't raise if at least one root has the locale."""
        root_a, root_b, _root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {(u"Hello", None): u"你好"})
        # root_b has no zh_CN directory

        tx = TransX(locales_root=[root_a, root_b], default_locale="zh_CN", strict_mode=True)
        assert tx.tr("Hello") == u"你好"

    def test_strict_mode_no_root_has_locale(self, tmp_path):
        """T-12b: strict_mode raises when no root has the requested locale."""
        root_a = os.path.join(str(tmp_path), "a")
        root_b = os.path.join(str(tmp_path), "b")
        os.makedirs(root_a)
        os.makedirs(root_b)

        # Import local modules
        from transx.exceptions import LocaleNotFoundError

        with pytest.raises(LocaleNotFoundError):
            TransX(locales_root=[root_a, root_b], default_locale="xx_XX", strict_mode=True)


# ---------------------------------------------------------------------------
# T-extra: Duplicate root dedup
# ---------------------------------------------------------------------------
class TestDuplicateRoots:
    """Verify duplicate root paths are deduplicated."""

    def test_duplicate_roots_dedup(self, tmp_path):
        """Duplicate paths in the list are deduplicated."""
        root = os.path.join(str(tmp_path), "locales")
        os.makedirs(root)
        _create_locale(root, "zh_CN", {(u"Hello", None): u"你好"})

        tx = TransX(locales_root=[root, root, root], default_locale="zh_CN")
        assert len(tx.locales_roots) == 1
        assert tx.tr("Hello") == u"你好"


# ---------------------------------------------------------------------------
# T-extra: Three roots merge
# ---------------------------------------------------------------------------
class TestThreeRoots:
    """Verify merging across three roots."""

    def test_three_roots_merge(self, multi_root_dir):
        """Translations from 3 roots are all accessible."""
        root_a, root_b, root_c = multi_root_dir

        _create_locale(root_a, "ja_JP", {(u"File", None): u"ファイル"})
        _create_locale(root_b, "ja_JP", {(u"Edit", None): u"編集"})
        _create_locale(root_c, "ja_JP", {(u"View", None): u"表示"})

        tx = TransX(locales_root=[root_a, root_b, root_c], default_locale="ja_JP")
        assert tx.tr("File") == u"ファイル"
        assert tx.tr("Edit") == u"編集"
        assert tx.tr("View") == u"表示"

    def test_three_roots_conflict_priority(self, multi_root_dir, caplog):
        """First root always wins, regardless of how many later roots conflict."""
        root_a, root_b, root_c = multi_root_dir

        _create_locale(root_a, "zh_CN", {(u"OK", None): u"确定"})
        _create_locale(root_b, "zh_CN", {(u"OK", None): u"好的"})
        _create_locale(root_c, "zh_CN", {(u"OK", None): u"可以"})

        with caplog.at_level(logging.WARNING):
            tx = TransX(locales_root=[root_a, root_b, root_c], default_locale="zh_CN")

        assert tx.tr("OK") == u"确定"
        # Two conflicts should be logged (root_b and root_c)
        conflict_records = [r for r in caplog.records if "Duplicate msgid conflict" in r.message]
        assert len(conflict_records) == 2
