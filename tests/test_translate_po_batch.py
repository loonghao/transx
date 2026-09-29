#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hermetic tests for batched PO translation, checkpointing and exit codes.

``POFile.translate_messages`` must stay fail-soft, count what it could not
translate, and save after every batch. ``translate_command`` must turn those
counts into a non-zero exit status. No network is touched.
"""

# Import future modules
from __future__ import unicode_literals

# Import built-in modules
import os

# Import local modules
from transx.api.po import POFile
from transx.cli import translate_command
from transx.exceptions import TranslationError


class _FlakyTranslator(object):
    """Records the batches it receives and fails on demand."""

    def __init__(self, batch_size=2, fail_on=()):
        self.batch_size = batch_size
        self.fail_on = set(fail_on)
        self.batches = []
        self.saves = 0

    def translate_batch(self, texts, source_lang="auto", target_lang="en"):
        index = len(self.batches)
        self.batches.append(list(texts))
        if index in self.fail_on:
            raise TranslationError("backend unavailable")
        return ["es:%s" % text for text in texts]

    def translate(self, text, source_lang="auto", target_lang="en"):
        return self.translate_batch([text], source_lang, target_lang)[0]


class _LegacyTranslator(object):
    """A translator without batch support, as third party code may provide."""

    def __init__(self):
        self.calls = []

    def translate(self, text, source_lang="auto", target_lang="en"):
        self.calls.append(text)
        return "es:%s" % text


def _po_file(tmp_path, msgids):
    """Write a PO file holding ``msgids`` with empty translations."""
    path = str(tmp_path / "messages.po")
    lines = ['msgid ""', 'msgstr ""', '"Language: es\\n"', ""]
    for msgid in msgids:
        lines.append('msgid "%s"' % msgid)
        lines.append('msgstr ""')
        lines.append("")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    po = POFile(path, locale="es")
    po.load()
    return path, po


def test_translate_messages_batches_requests(tmp_path):
    """Untranslated messages must be handed over in batches, not one by one."""
    _path, po = _po_file(tmp_path, ["one", "two", "three", "four"])
    translator = _FlakyTranslator(batch_size=2)

    assert po.translate_messages(translator, target_lang="es") == 4

    assert translator.batches == [["one", "two"], ["three", "four"]]
    assert po.translation_failures == 0


def test_translate_messages_counts_failures_and_continues(tmp_path):
    """A failed batch must be counted, not abort the run."""
    _path, po = _po_file(tmp_path, ["one", "two", "three", "four"])
    translator = _FlakyTranslator(batch_size=2, fail_on={0})

    assert po.translate_messages(translator, target_lang="es") == 2

    # Every batch was attempted, so the failure did not stop the run.
    assert len(translator.batches) == 2
    assert po.translation_failures == 2
    assert po.translations[("three", None)].msgstr == "es:three"


def test_translate_messages_checkpoints_after_each_batch(tmp_path, monkeypatch):
    """Progress must be saved per batch so an interrupted run keeps it."""
    _path, po = _po_file(tmp_path, ["one", "two", "three", "four"])
    translator = _FlakyTranslator(batch_size=2)

    saves = []
    monkeypatch.setattr(po, "save", lambda: saves.append(len(saves)))

    po.translate_messages(translator, target_lang="es")

    assert len(saves) == 2, saves


def test_translate_messages_supports_legacy_translators(tmp_path):
    """A translator without translate_batch still works, one string at a time."""
    _path, po = _po_file(tmp_path, ["one", "two"])
    translator = _LegacyTranslator()

    assert po.translate_messages(translator, target_lang="es") == 2

    assert translator.calls == ["one", "two"]
    assert po.translation_failures == 0


def test_translate_messages_skips_already_translated(tmp_path):
    """Messages that already have a translation must not be sent again."""
    _path, po = _po_file(tmp_path, ["one", "two"])
    po.translations[("one", None)].msgstr = "uno"
    translator = _FlakyTranslator(batch_size=5)

    assert po.translate_messages(translator, target_lang="es") == 1

    assert translator.batches == [["two"]]


def test_translate_command_returns_zero_on_success(tmp_path):
    """A fully translated run must exit 0."""
    pot_path = tmp_path / "messages.pot"
    pot_path.write_text('msgid ""\nmsgstr ""\n\nmsgid "one"\nmsgstr ""\n', encoding="utf-8")

    args = _Args(files=[str(pot_path)], target_lang="es")

    saved = {}

    def _fake_translate_po_file(path, lang, translator=None):
        saved["called"] = (path, lang)
        return path

    import transx.cli as cli_module

    original = cli_module.translate_po_file
    cli_module.translate_po_file = _fake_translate_po_file
    try:
        assert translate_command(args) == 0
    finally:
        cli_module.translate_po_file = original

    assert saved["called"] == (str(pot_path), "es")


def test_translate_command_returns_one_on_message_failures(tmp_path):
    """Messages the translator could not translate must surface as exit 1."""
    path = tmp_path / "messages.po"
    path.write_text('msgid ""\nmsgstr ""\n', encoding="utf-8")

    class _Failing(object):
        failure_count = 3

    args = _Args(files=[str(path)], target_lang="es")

    import transx.cli as cli_module

    original_translator = cli_module.GoogleTranslator
    original_translate = cli_module.translate_po_file
    cli_module.GoogleTranslator = lambda **kwargs: _Failing()
    cli_module.translate_po_file = lambda path, lang, translator=None: path
    try:
        assert translate_command(args) == 1
    finally:
        cli_module.GoogleTranslator = original_translator
        cli_module.translate_po_file = original_translate


def test_translate_command_runs_every_file_before_failing(tmp_path):
    """One failing file must not stop the remaining files."""
    first = tmp_path / "a.po"
    second = tmp_path / "b.po"
    for path in (first, second):
        path.write_text('msgid ""\nmsgstr ""\n', encoding="utf-8")

    attempted = []

    import transx.cli as cli_module

    original = cli_module.translate_po_file

    def _fake(path, lang, translator=None):
        attempted.append(path)
        if path.endswith("a.po"):
            raise TranslationError("boom")
        return path

    cli_module.translate_po_file = _fake
    args = _Args(files=[str(first), str(second)], target_lang="es")
    try:
        assert translate_command(args) == 1
    finally:
        cli_module.translate_po_file = original

    # Both files were attempted before the command reported failure.
    assert len(attempted) == 2, attempted


class _Args(object):
    """Minimal stand-in for the argparse namespace translate_command needs."""

    def __init__(self, files=None, target_lang=None, languages=None, directory="locales"):
        self.files = files or []
        self.target_lang = target_lang
        self.languages = languages
        self.directory = directory


def test_translate_command_requires_target_lang(tmp_path):
    """Specific files without a target language stay a usage error."""
    args = _Args(files=["messages.po"], target_lang=None)
    assert translate_command(args) == 1


def test_po_file_roundtrip_persists_translations(tmp_path):
    """A checkpointed PO file must contain the translations on disk."""
    path, po = _po_file(tmp_path, ["one", "two", "three", "four"])
    translator = _FlakyTranslator(batch_size=2)

    po.translate_messages(translator, target_lang="es")
    po.save()

    with open(path, encoding="utf-8") as handle:
        content = handle.read()

    assert "es:one" in content
    assert os.path.isfile(path)
