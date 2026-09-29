#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the persistent translation memory.

Every test is hermetic: no network, and the memory is pointed at a temporary
directory. The offline behaviour is the point of the feature, so several cases
assert that no request is attempted at all.
"""

# Import future modules
from __future__ import unicode_literals

# Import built-in modules
import io
import json
import os

# Import third-party modules
import pytest

# Import local modules
import transx.api.translate as translate_module
from transx.api.translate import GoogleTranslator
from transx.exceptions import TranslationError
from transx.internal.compat import PY2
from transx.internal.translation_memory import TM_VERSION
from transx.internal.translation_memory import TranslationMemory
from transx.internal.translation_memory import make_key
from transx.internal.translation_memory import offline_enabled
from transx.internal.translation_memory import resolve_tm_path

if PY2:  # pragma: no cover - exercised only on Python 2
    from urllib2 import HTTPError
else:
    from urllib.error import HTTPError


class _FakeHeaders(object):
    def get(self, key, default=None):
        return default


class _Response(object):
    headers = _FakeHeaders()

    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body.encode("utf-8")


def _batch_response(translated):
    """Build a response body shaped like the real endpoint's."""
    segments = []
    for index, text in enumerate(translated):
        suffix = "\n" if index < len(translated) - 1 else ""
        segments.append([text + suffix, "", None, None, 10])
    return json.dumps([segments, None, "en"], ensure_ascii=False)


class _Recorder(object):
    def __init__(self, handler):
        self.handler = handler
        self.calls = []

    def __call__(self, request):
        self.calls.append(request.full_url)
        return self.handler()


def _ok(translations):
    def _handle():
        return _Response(_batch_response(translations))

    return _handle


@pytest.fixture
def translator(monkeypatch, tmp_path):
    """A translator whose memory lives in a temporary directory."""
    instance = GoogleTranslator(path=str(tmp_path / "tm.json"))
    monkeypatch.setattr(instance, "_wait_for_rate_limit", lambda: None)
    monkeypatch.setattr(translate_module.time, "sleep", lambda seconds: None)
    return instance


def _install(monkeypatch, handler):
    recorder = _Recorder(handler)
    monkeypatch.setattr(translate_module, "urlopen", recorder)
    return recorder


# --- Key design --------------------------------------------------------------


def test_key_depends_on_every_field():
    base = make_key("Hello", "en", "es", "engine-a")
    assert base != make_key("Hello!", "en", "es", "engine-a")
    assert base != make_key("Hello", "fr", "es", "engine-a")
    assert base != make_key("Hello", "en", "fr", "engine-a")


def test_key_depends_on_engine():
    """A different engine must not reuse another engine's translations."""
    assert make_key("Hello", "en", "es", "engine-a") != make_key("Hello", "en", "es", "engine-b")


def test_key_is_stable():
    assert make_key("Hello", "en", "es", "e") == make_key("Hello", "en", "es", "e")


# --- Query before network ----------------------------------------------------


def test_hit_sends_no_request(translator, monkeypatch):
    """A remembered string must be served without any HTTP call."""
    recorder = _install(monkeypatch, _ok(["Hola"]))
    translator.translate("Hello", "en", "es")

    assert len(recorder.calls) == 1
    translator.memory_hits = 0

    # Second time round the answer is already known.
    assert translator.translate("Hello", "en", "es") == "Hola"
    assert len(recorder.calls) == 1, "cache hit must not hit the network"
    assert translator.memory_hits == 1


def test_partial_hits_only_send_the_misses(translator, monkeypatch):
    """Only strings missing from the memory may be sent."""
    _install(monkeypatch, _ok(["Hola"]))
    translator.translate("Hello", "en", "es")

    recorder = _install(monkeypatch, _ok(["Adios"]))
    results = translator.translate_batch(["Hello", "Goodbye"], "en", "es")

    assert results == ["Hola", "Adios"]
    assert len(recorder.calls) == 1, "only the miss should be requested"


def test_miss_is_remembered(translator, monkeypatch):
    _install(monkeypatch, _ok(["Hola"]))
    translator.translate("Hello", "en", "es")

    assert len(translator.translation_memory) == 1


def test_empty_translation_is_not_cached(translator, monkeypatch):
    """A failed translation must not poison the memory."""

    def _handle():
        return _Response(_batch_response(["   "]))

    _install(monkeypatch, _handle)

    translator.translate("Hello", "en", "es")

    assert len(translator.translation_memory) == 0


# --- Persistence -------------------------------------------------------------


def test_memory_survives_a_new_translator(monkeypatch, tmp_path):
    """A fresh process must be able to reuse what was remembered."""
    path = str(tmp_path / "tm.json")
    first = GoogleTranslator(path=path)
    monkeypatch.setattr(first, "_wait_for_rate_limit", lambda: None)
    monkeypatch.setattr(translate_module.time, "sleep", lambda seconds: None)
    _install(monkeypatch, _ok(["Hola"]))
    first.translate("Hello", "en", "es")

    second = GoogleTranslator(path=path)
    recorder = _install(monkeypatch, _ok(["unused"]))

    assert second.translate("Hello", "en", "es") == "Hola"
    assert recorder.calls == []


def test_file_is_json_versioned_and_sorted(tmp_path):
    path = str(tmp_path / "tm.json")
    memory = TranslationMemory(path=path, engine_id="e")
    memory.put("Hello", "en", "es", "Hola")
    memory.save()

    with io.open(path, encoding="utf-8") as handle:
        data = json.load(handle)

    assert data["version"] == TM_VERSION
    assert list(data["entries"]) == sorted(data["entries"])
    assert list(data["entries"]) == [make_key("Hello", "en", "es", "e")]
    stored = next(iter(data["entries"].values()))
    assert stored["msgstr"] == "Hola"
    assert stored["src"] == "Hello"


def test_written_file_is_byte_stable(tmp_path):
    """The committed file must not churn between runs."""
    path = str(tmp_path / "tm.json")

    def _write():
        memory = TranslationMemory(path=path, engine_id="e")
        memory.load()
        memory.put("B", "en", "es", "Be")
        memory.put("A", "en", "es", "Ae")
        memory.save()
        with io.open(path, encoding="utf-8") as handle:
            return handle.read()

    assert _write() == _write()


def test_atomic_write_leaves_no_temp_files(tmp_path):
    path = str(tmp_path / "tm.json")
    memory = TranslationMemory(path=path, engine_id="e")
    memory.put("Hello", "en", "es", "Hola")
    memory.save()

    leftovers = [name for name in os.listdir(str(tmp_path)) if name.startswith(".tm-")]
    assert leftovers == [], leftovers


def test_save_creates_missing_parent_dir(tmp_path):
    path = str(tmp_path / "nested" / "dir" / "tm.json")
    memory = TranslationMemory(path=path, engine_id="e")
    memory.put("Hello", "en", "es", "Hola")

    assert memory.save() is True
    assert os.path.isfile(path)


# --- Corrupt and unknown files -----------------------------------------------


def test_corrupt_file_recovers(tmp_path):
    path = str(tmp_path / "tm.json")
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write("{ this is not json")

    memory = TranslationMemory(path=path, engine_id="e")
    memory.load()

    assert memory.recovered_from_error is True
    assert len(memory) == 0
    assert os.path.isfile(path + ".corrupt")


def test_unknown_version_recovers(tmp_path):
    path = str(tmp_path / "tm.json")
    with io.open(path, "w", encoding="utf-8") as handle:
        json.dump({"version": 999, "entries": {}}, handle)

    memory = TranslationMemory(path=path, engine_id="e")
    memory.load()

    assert memory.recovered_from_error is True
    assert len(memory) == 0


def test_corrupt_file_does_not_break_translation(tmp_path, monkeypatch):
    """A bad memory must degrade to a normal online translation."""
    path = str(tmp_path / "tm.json")
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write("garbage")

    translator = GoogleTranslator(path=path)
    monkeypatch.setattr(translator, "_wait_for_rate_limit", lambda: None)
    _install(monkeypatch, _ok(["Hola"]))

    assert translator.translate("Hello", "en", "es") == "Hola"


def test_missing_file_is_not_an_error(tmp_path):
    memory = TranslationMemory(path=str(tmp_path / "absent.json"), engine_id="e")
    memory.load()

    assert memory.recovered_from_error is False
    assert len(memory) == 0


# --- Offline -----------------------------------------------------------------


def test_offline_hit_needs_no_network(translator, monkeypatch):
    _install(monkeypatch, _ok(["Hola"]))
    translator.translate("Hello", "en", "es")

    translator.offline = True
    recorder = _install(monkeypatch, _ok(["unused"]))

    assert translator.translate("Hello", "en", "es") == "Hola"
    assert recorder.calls == []


def test_offline_miss_falls_back_to_source(translator, monkeypatch):
    """An offline miss must return the source text, not raise."""
    translator.offline = True
    recorder = _install(monkeypatch, _ok(["unused"]))

    assert translator.translate("Hello", "en", "es") == "Hello"
    assert recorder.calls == []
    assert translator.failure_count == 1


def test_offline_batch_keeps_going(translator, monkeypatch):
    _install(monkeypatch, _ok(["Hola"]))
    translator.translate("Hello", "en", "es")

    translator.offline = True
    recorder = _install(monkeypatch, _ok(["unused"]))

    assert translator.translate_batch(["Hello", "Goodbye"], "en", "es") == ["Hola", "Goodbye"]
    assert recorder.calls == []
    assert translator.failure_count == 1


def test_offline_never_opens_the_socket(translator, monkeypatch):
    def _explode():
        raise AssertionError("offline mode must not reach urlopen")

    _install(monkeypatch, _explode)
    translator.offline = True

    assert translator.translate("anything", "en", "es") == "anything"


def test_offline_from_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("TRANSX_OFFLINE", "1")
    assert offline_enabled() is True

    monkeypatch.delenv("TRANSX_OFFLINE")
    assert offline_enabled() is False


def test_offline_flag_overrides_environment(monkeypatch):
    monkeypatch.setenv("TRANSX_OFFLINE", "1")
    assert offline_enabled(False) is False


# --- Engine separation -------------------------------------------------------


def test_entries_do_not_leak_across_engines(tmp_path):
    """A different engine must not see another engine's entries."""
    path = str(tmp_path / "tm.json")

    first = TranslationMemory(path=path, engine_id="engine-a")
    first.load()
    first.put("Hello", "en", "es", "Hola-A")
    first.save()

    second = TranslationMemory(path=path, engine_id="engine-b")
    second.load()

    assert second.get("Hello", "en", "es") is None
    assert first.get("Hello", "en", "es") == "Hola-A"


def test_saving_one_engine_keeps_the_other(tmp_path):
    path = str(tmp_path / "tm.json")

    first = TranslationMemory(path=path, engine_id="engine-a")
    first.load()
    first.put("Hello", "en", "es", "Hola-A")
    first.save()

    second = TranslationMemory(path=path, engine_id="engine-b")
    second.load()
    second.put("Hello", "en", "es", "Hola-B")
    second.save()

    reloaded_a = TranslationMemory(path=path, engine_id="engine-a")
    reloaded_a.load()
    assert reloaded_a.get("Hello", "en", "es") == "Hola-A"


# --- Path resolution ---------------------------------------------------------


def test_explicit_path_wins(monkeypatch):
    monkeypatch.setenv("TRANSX_TM_PATH", "/from/env.json")
    assert resolve_tm_path(locale_root="/root", explicit_path="/explicit.json") == "/explicit.json"


def test_env_path_beats_locale_root(monkeypatch):
    monkeypatch.setenv("TRANSX_TM_PATH", "/from/env.json")
    assert resolve_tm_path(locale_root="/root") == "/from/env.json"


def test_locale_root_default(monkeypatch):
    monkeypatch.delenv("TRANSX_TM_PATH", raising=False)
    resolved = resolve_tm_path(locale_root="/root")
    assert resolved == os.path.join("/root", ".transx", "tm.json")


def test_user_level_fallback(monkeypatch):
    monkeypatch.delenv("TRANSX_TM_PATH", raising=False)
    resolved = resolve_tm_path()
    assert resolved.endswith(os.path.join(".transx", "tm.json"))


# --- Context manager ---------------------------------------------------------


def test_context_manager_persists(tmp_path):
    path = str(tmp_path / "tm.json")
    with TranslationMemory(path=path, engine_id="e") as memory:
        memory.put("Hello", "en", "es", "Hola")

    reloaded = TranslationMemory(path=path, engine_id="e")
    reloaded.load()
    assert reloaded.get("Hello", "en", "es") == "Hola"


def test_disabled_memory_is_inert(tmp_path):
    memory = TranslationMemory(path=str(tmp_path / "tm.json"), engine_id="e", enabled=False)
    memory.load()
    memory.put("Hello", "en", "es", "Hola")

    assert memory.get("Hello", "en", "es") is None
    assert memory.save() is False
    assert not os.path.exists(str(tmp_path / "tm.json"))


def test_translation_error_still_raises_when_online(translator, monkeypatch):
    """A real online failure must keep failing, offline behaviour aside."""
    from transx.internal.compat import unquote_plus

    def _handle():
        raise HTTPError("http://x", 429, "rate limited", _FakeHeaders(), None)

    _install(monkeypatch, _handle)

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    assert unquote_plus  # compat import kept for py2.7 parity
