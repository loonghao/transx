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

#: A loopback endpoint, so offline mode exercises the miss path instead of
#: refusing the request outright. See ``_build``. The path deliberately does
#: not match a profile hint, so these tests keep the default Google profile
#: whose response shape they mock.
LOOPBACK_ENDPOINT = "http://127.0.0.1:65001/translate_a/single"

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


def _build(monkeypatch, path, offline=False, endpoint=LOOPBACK_ENDPOINT):
    """Build a translator whose memory lives at ``path``.

    Offline mode now allows a loopback endpoint, because blocking it would
    make local translation services unusable in exactly the mode they exist
    for. These tests therefore point the translator at a loopback URL, so
    "offline" still means "no string leaves this machine" while the offline
    miss path under test stays reachable.

    Args:
        monkeypatch: pytest fixture used to neutralise the rate limiter
        path: Explicit translation memory file path
        offline (bool): When True no request may leave this machine
        endpoint: Endpoint URL to use

    Returns:
        GoogleTranslator: Instance that will not sleep or wait
    """
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", endpoint)
    instance = GoogleTranslator(path=path, offline=offline)
    monkeypatch.setattr(instance, "_wait_for_rate_limit", lambda: None)
    monkeypatch.setattr(translate_module.time, "sleep", lambda seconds: None)
    return instance


@pytest.fixture
def translator(monkeypatch, tmp_path):
    """A translator whose memory lives in a temporary directory."""
    return _build(monkeypatch, str(tmp_path / "tm.json"))


def _install(monkeypatch, handler):
    recorder = _Recorder(handler)
    monkeypatch.setattr(translate_module, "urlopen", recorder)
    return recorder


def _raise_connection_error():
    """A handler that fails the way an unreachable local service does.

    Used by the offline tests: the loopback endpoint is reachable in
    principle, so offline mode must let the request through and then fall back
    to the source text when it fails.
    """
    if PY2:  # pragma: no cover - exercised only on Python 2
        from urllib2 import URLError
    else:
        from urllib.error import URLError

    def _handle():
        raise URLError("connection refused")

    return _handle


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
#
# Offline mode allows a loopback endpoint. It means "no string leaves this
# machine", not "no request at all": a local translation service is already on
# the machine, so blocking it would make the offline path useless. The tests
# below cover both halves - loopback is allowed, and anything else is refused.


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
    # Nothing is listening on the loopback endpoint, so every request fails
    # and the miss path is what runs.
    _install(monkeypatch, _raise_connection_error())

    assert translator.translate("Hello", "en", "es") == "Hello"
    assert translator.failure_count == 1


def test_offline_batch_keeps_going(translator, monkeypatch):
    _install(monkeypatch, _ok(["Hola"]))
    translator.translate("Hello", "en", "es")

    translator.offline = True
    _install(monkeypatch, _raise_connection_error())

    assert translator.translate_batch(["Hello", "Goodbye"], "en", "es") == ["Hola", "Goodbye"]
    assert translator.failure_count == 1


def test_offline_miss_is_not_remembered(monkeypatch, tmp_path):
    """An offline fallback is a placeholder, not a translation.

    Storing the source text as if it were the translation would make every
    later run - online ones included - reuse it, so the string would never be
    translated and failure_count would stay at zero forever.
    """
    path = str(tmp_path / "offline.json")
    instance = _build(monkeypatch, path, offline=True)
    _install(monkeypatch, _raise_connection_error())

    assert instance.translate("Goodbye moon", "en", "es") == "Goodbye moon"
    assert instance.failure_count == 1

    assert instance.translation_memory.get("Goodbye moon", "en", "es") is None
    assert not os.path.exists(path), "an offline miss must not persist the source text"


def test_online_run_after_offline_miss_still_asks_the_backend(monkeypatch, tmp_path):
    """A gap left by an offline run must stay visible to the next online run.

    Two instances sharing one memory file stand in for two runs. The second
    one is online, so it has to actually request the string the offline run
    could not translate instead of replaying the source text.
    """
    path = str(tmp_path / "shared.json")

    offline = _build(monkeypatch, path, offline=True)
    _install(monkeypatch, _raise_connection_error())
    assert offline.translate("Goodbye moon", "en", "es") == "Goodbye moon"
    assert offline.failure_count == 1

    online = _build(monkeypatch, path)
    recorder = _install(monkeypatch, _ok(["Adios luna"]))

    assert online.translate("Goodbye moon", "en", "es") == "Adios luna"
    assert len(recorder.calls) == 1, "the gap must still be sent to the backend"
    assert online.memory_hits == 0


def test_offline_never_reaches_a_remote_host(monkeypatch, tmp_path):
    """Offline must refuse any endpoint that is not on this machine.

    Loopback is allowed because a local service never sends a string off the
    machine. Anything else is exactly what offline mode exists to prevent.
    """
    path = str(tmp_path / "remote.json")
    instance = _build(
        monkeypatch, path, offline=True, endpoint="https://translate.googleapis.com/x"
    )

    def _explode():
        raise AssertionError("offline mode must not reach the network")

    _install(monkeypatch, _explode)

    with pytest.raises(TranslationError):
        instance.translate("anything", "en", "es")


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
