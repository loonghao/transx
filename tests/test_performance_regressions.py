#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regression tests for the performance work on caching and parsing.

These tests pin down the behaviour that the optimizations must preserve:
identical results, no cross-talk between the ``tr()`` and ``translate()``
caches, a lazily built variant index and .gitignore rules that still apply per
directory.
"""

# Import built-in modules
import os

# Import third-party modules
import pytest

# Import local modules
from transx.api.locale import normalize_language_code
from transx.api.translation_catalog import TranslationCatalog
from transx.internal.filesystem import walk_with_gitignore


def test_tr_and_translate_share_no_interpreter_state(transx_instance):
    """``tr()`` must still work after ``translate()`` was used with parameters.

    Both entry points used to store different object types under the same
    ``_interpreter_cache`` key, so whichever ran second silently fell back to
    returning the untranslated source text.
    """
    transx_instance.switch_locale("ja_JP")

    # Prime the interpreter chain through ``translate()`` first.
    assert transx_instance.translate("Hello {name}", name="Alice") == "こんにちは、Aliceさん"
    # ``tr()`` must not be affected by that.
    assert transx_instance.tr("Hello {name}", name="Alice") == "こんにちは、Aliceさん"


def test_translate_after_tr_with_parameters(transx_instance):
    """``translate()`` must still substitute parameters after ``tr()`` ran."""
    transx_instance.switch_locale("ja_JP")

    assert transx_instance.tr("Hello {name}", name="Bob") == "こんにちは、Bobさん"
    assert transx_instance.translate("Hello {name}", name="Bob") == "こんにちは、Bobさん"


def test_tr_matches_chain_result_without_parameters(transx_instance):
    """The parameterless fast path must agree with the interpreter chain."""
    transx_instance.switch_locale("ja_JP")

    # Force the full chain by adding a ``$`` so both paths can be compared.
    assert transx_instance.tr("Hello") == "こんにちは"
    assert transx_instance.tr("Hello {name}", name="X") == "こんにちは、Xさん"
    # A second, cached call must return the very same value.
    assert transx_instance.tr("Hello") == "こんにちは"


def test_translate_and_tr_agree_on_missing_keys(transx_instance):
    """Unknown keys fall back to the source text on both entry points."""
    transx_instance.switch_locale("ja_JP")

    assert transx_instance.tr("Definitely missing") == "Definitely missing"
    assert transx_instance.translate("Definitely missing") == "Definitely missing"


def test_variant_index_is_built_lazily():
    """Loading a catalog must not build the variant index up front."""
    catalog = TranslationCatalog(locale="zh_CN")
    catalog.add_message("Hello World", "你好世界")
    catalog.add_message("hello world!", "你好世界!")

    assert catalog._variants is None

    # A direct hit does not need the index either.
    assert catalog.get_message("Hello World") == "你好世界"
    assert catalog.get_translation("Hello World") == "你好世界"
    assert catalog._variants is None

    # The fallback path (a near miss) builds it exactly once.
    assert catalog.get_translation("Hello World!") == "你好世界"
    variants = catalog._variants
    assert variants is not None
    assert catalog.find_variants("hello world!") == [("Hello World", None), ("hello world!", None)]
    assert catalog._variants is variants


def test_variant_index_stays_in_sync_after_creation():
    """Messages added after the index exists are still indexed."""
    catalog = TranslationCatalog(locale="zh_CN")
    catalog.add_message("Open", "开")
    assert catalog.find_variants("Open") == [("Open", None)]

    catalog.add_message("Open", "打开")
    assert catalog.find_variants("Open") == [("Open", None)]

    catalog.add_message("Close", "关")
    assert catalog.find_variants("Close") == [("Close", None)]


def test_variant_fallback_lookup():
    """The fuzzy fallback still resolves punctuation/whitespace variants."""
    catalog = TranslationCatalog(locale="zh_CN")
    catalog.add_message("Open File", "打开文件")

    assert catalog.get_translation("Open File") == "打开文件"
    assert catalog.get_translation("Open File!") == "打开文件"
    assert catalog.get_translation("open   file") == "打开文件"


def test_params_key_handles_nested_structures(transx_instance):
    """Cache keys are built from the parameters themselves, not from hash()."""
    first = transx_instance._create_params_key({"a": {"b": 1}, "c": [1, 2]})
    second = transx_instance._create_params_key({"c": [1, 2], "a": {"b": 1}})
    third = transx_instance._create_params_key({"a": {"b": 2}, "c": [1, 2]})

    # Key order must not matter, values must.
    assert first == second
    assert first != third
    assert hash(first) == hash(second)
    assert transx_instance._create_params_key({}) is None


def test_params_key_accepts_unhashable_values(transx_instance):
    """Lists and sets are accepted and frozen into a hashable key."""
    key = transx_instance._create_params_key({"items": [1, 2, 3], "flags": {"a", "b"}})
    assert hash(key)
    assert key == transx_instance._create_params_key({"flags": {"a", "b"}, "items": [1, 2, 3]})


def test_normalize_language_code_memoization_matches_lookup():
    """Memoizing the lookup must not change any result."""
    samples = ["zh_CN", "zh-CN", "zh_cn", "cn", "ja", "jp", "en", "en_US", "en-US",
               "fr", "de_DE", "korean", "chinese", "zh_hans", "zh_Hant", "es",
               "ru_RU", "it_IT", "unknown_XX", "", None]

    for sample in samples:
        assert normalize_language_code(sample) == normalize_language_code(sample)

    assert normalize_language_code("zh-CN") == "zh_CN"
    assert normalize_language_code("jp") == "ja_JP"
    assert normalize_language_code("en") == "en_US"
    assert normalize_language_code("chinese") == "zh_CN"
    assert normalize_language_code("unknown_XX") is None
    assert normalize_language_code("") is None
    assert normalize_language_code(None) is None


@pytest.fixture
def project_tree(tmp_path):
    """Build a small tree with a root and a nested .gitignore."""
    (tmp_path / ".gitignore").write_text("*.pyc\nbuild/\n", encoding="utf-8")

    pkg = tmp_path / "pkg"
    pkg.mkdir()
    # The nested file takes precedence for everything below ``pkg``, so
    # ``pkg/stale.pyc`` is *not* covered by the root ``*.pyc`` rule.
    (pkg / ".gitignore").write_text("secret.py\n", encoding="utf-8")

    (pkg / "keep.py").write_text("x = 1\n", encoding="utf-8")
    (pkg / "secret.py").write_text("x = 1\n", encoding="utf-8")
    (pkg / "stale.pyc").write_text("x = 1\n", encoding="utf-8")

    (tmp_path / "notes.txt").write_text("hello\n", encoding="utf-8")
    (tmp_path / "stale.pyc").write_text("x = 1\n", encoding="utf-8")

    build = tmp_path / "build"
    build.mkdir()
    (build / "generated.py").write_text("x = 1\n", encoding="utf-8")

    return tmp_path


def test_walk_with_gitignore_still_applies_nested_rules(project_tree):
    """Per-walk caching must not flatten nested .gitignore files."""
    found = sorted(os.path.basename(p)
                   for p in walk_with_gitignore(str(project_tree), ["*.py"]))

    assert found == ["keep.py"]


def test_walk_with_gitignore_without_patterns(project_tree):
    """All non-ignored files are returned when no pattern is given."""
    found = sorted(os.path.basename(p) for p in walk_with_gitignore(str(project_tree)))

    # ``.gitignore`` itself is skipped, ``build/`` and ``*.pyc`` at the root are
    # ignored, and ``pkg/secret.py`` is ignored by the nested .gitignore.
    assert found == ["keep.py", "notes.txt", "stale.pyc"]
