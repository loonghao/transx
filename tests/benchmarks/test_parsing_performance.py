"""Benchmark tests for TransX parsing and catalog loading performance."""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import os

# Import third-party modules
import pytest

# Import local modules
from transx.api.mo import MOFile
from transx.api.mo import compile_po_file
from transx.api.po import POFile
from transx.api.pot import POTFile
from transx.api.translation_catalog import TranslationCatalog
from transx.core import TransX

#: Number of entries in the generated catalogs.
CATALOG_SIZE = 1000


def _build_catalog_source():
    """Build the textual content of a catalog with CATALOG_SIZE entries."""
    lines = [
        'msgid ""',
        'msgstr ""',
        '"Project-Id-Version: benchmark 1.0\\n"',
        '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Language: zh_CN\\n"',
        "",
    ]
    for i in range(CATALOG_SIZE):
        lines.append("#: src/module%d.py:%d" % (i % 20, i + 1))
        lines.append('msgid "Message number %d with some text"' % i)
        lines.append('msgstr "消息编号 %d 带有一些文本"' % i)
        lines.append("")
    return "\n".join(lines)


@pytest.fixture(scope="module")
def catalog_paths(tmp_path_factory):
    """Create a temporary PO/POT/MO triple plus a locales root."""
    root = tmp_path_factory.mktemp("parse_benchmark")
    content = _build_catalog_source()

    po_path = root / "messages.po"
    po_path.write_text(content, encoding="utf-8")
    pot_path = root / "messages.pot"
    pot_path.write_text(content, encoding="utf-8")
    mo_path = root / "messages.mo"
    compile_po_file(str(po_path), str(mo_path))

    locale_dir = root / "locales" / "zh_CN" / "LC_MESSAGES"
    locale_dir.mkdir(parents=True)
    (locale_dir / "messages.po").write_text(content, encoding="utf-8")
    compile_po_file(str(locale_dir / "messages.po"), str(locale_dir / "messages.mo"))

    return {
        "po": str(po_path),
        "pot": str(pot_path),
        "mo": str(mo_path),
        "locales_root": str(root / "locales"),
    }


def test_mo_parsing(benchmark, catalog_paths):
    """Benchmark .mo parsing."""

    def parse_mo():
        mo = MOFile()
        mo.load(catalog_paths["mo"])
        return mo

    mo = benchmark(parse_mo)
    assert len(mo.translations) == CATALOG_SIZE + 1


def test_po_parsing(benchmark, catalog_paths):
    """Benchmark .po parsing."""

    def parse_po():
        po = POFile(catalog_paths["po"])
        po.load()
        return po

    po = benchmark(parse_po)
    assert len(po.translations) == CATALOG_SIZE + 1


def test_pot_parsing(benchmark, catalog_paths):
    """Benchmark .pot parsing."""

    def parse_pot():
        pot = POTFile(catalog_paths["pot"])
        pot.load()
        return pot

    pot = benchmark(parse_pot)
    assert len(pot.translations) == CATALOG_SIZE + 1


def test_po_to_mo_compilation(benchmark, catalog_paths):
    """Benchmark compiling a PO file into MO format."""
    target = os.path.join(os.path.dirname(catalog_paths["mo"]), "compiled.mo")
    benchmark(lambda: compile_po_file(catalog_paths["po"], target))
    assert os.path.exists(target)


def test_catalog_build(benchmark, catalog_paths):
    """Benchmark building a TranslationCatalog from a MO file."""

    def build():
        mo = MOFile()
        mo.load(catalog_paths["mo"])
        catalog = TranslationCatalog(locale="zh_CN")
        for msgid, message in mo.translations.items():
            if msgid:
                catalog.add_message(msgid, message.msgstr)
        return catalog

    catalog = benchmark(build)
    assert len(catalog._messages) == CATALOG_SIZE


def test_mo_catalog_lookup(benchmark, catalog_paths):
    """Benchmark resolving every entry of a freshly loaded catalog."""
    transx = TransX(locales_root=catalog_paths["locales_root"], default_locale="zh_CN")
    keys = ["Message number %d with some text" % i for i in range(CATALOG_SIZE)]

    def lookup_all():
        return [transx.tr(key) for key in keys]

    result = benchmark(lookup_all)
    assert result[0] == "消息编号 0 带有一些文本"
