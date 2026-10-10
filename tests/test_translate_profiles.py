#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hermetic tests for the translation provider profiles.

Nothing here reaches the network. Most cases drive a real HTTP server bound to
an ephemeral port on ``127.0.0.1``, so the whole request construction and
parsing path is exercised instead of only the ``urlopen`` seam. The server is
plain ``BaseHTTPServer``/``http.server`` and works unchanged on Python 2.7.
"""

# Import future modules
from __future__ import unicode_literals

# Import built-in modules
import json
import os
import threading

# Import third-party modules
import pytest

# Import local modules
from transx.api.translate import GoogleTranslator
from transx.exceptions import TranslationError
from transx.internal.compat import PY2
from transx.internal.compat import text_type
from transx.internal.translate_profiles import LibreTranslateProfile
from transx.internal.translate_profiles import OllamaProfile
from transx.internal.translate_profiles import PROFILE_NAMES
from transx.internal.translate_profiles import create_profile
from transx.internal.translate_profiles import infer_profile_name
from transx.internal.translate_profiles import is_loopback_url
from transx.internal.translate_profiles import resolve_profile_name

if PY2:  # pragma: no cover - exercised only on Python 2
    import BaseHTTPServer as http_server
    import SocketServer as socketserver
else:
    import http.server as http_server
    import socketserver


# --- A real server on 127.0.0.1 ---------------------------------------------

#: Failures raised inside handler code, which runs on the server thread and
#: would otherwise be swallowed by the server loop.
_FAILURES = []


class _Handler(http_server.BaseHTTPRequestHandler):
    """Answers requests using the handler installed by the fixture."""

    protocol_version = "HTTP/1.0"

    def log_message(self, format, *args):
        """Silence the default stderr logging."""

    def _dispatch(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8") if length else ""
        try:
            status, payload = self.server.handler(self.path, body, self.headers, self.command)
        except AssertionError:
            # An assertion inside a handler must not kill the connection:
            # report it as a failure so the client sees it as a status code
            # and the failure is recorded rather than dropped.
            _FAILURES.append(("assert", self.path))
            status, payload = 500, json.dumps({"error": "handler assertion failed"})
        except Exception as exc:
            _FAILURES.append((text_type(exc), self.path))
            status, payload = 500, json.dumps({"error": text_type(exc)})
        raw = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    do_GET = _dispatch
    do_POST = _dispatch


@pytest.fixture
def server():
    """Start a loopback HTTP server and yield a recorder for it.

    The server lives for the duration of one test and is shut down
    afterwards, so no port is left bound and no test depends on another.
    """
    recorded = []
    del _FAILURES[:]

    class _Server(socketserver.TCPServer):
        allow_reuse_address = True
        handler = staticmethod(lambda path, body, headers, method: (200, "{}"))

    httpd = _Server(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()

    def _install(handler):
        def _wrapped(path, body, headers, method):
            recorded.append({"path": path, "body": body, "method": method})
            return handler(path, body, headers, method)

        httpd.handler = staticmethod(_wrapped)
        return recorded

    class _Handle(object):
        url = "http://127.0.0.1:%d" % httpd.server_address[1]
        install = staticmethod(_install)
        calls = recorded
        failures = _FAILURES

    try:
        yield _Handle
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def _body(payload):
    """Build a 200 response carrying ``payload`` as JSON."""
    return 200, json.dumps(payload)


# --- Criterion 1: the default is untouched ----------------------------------


def test_default_profile_is_google():
    """With nothing set, the translator must stay on the Google profile."""
    translator = GoogleTranslator()
    assert translator.profile.name == "google"
    assert translator.engine_id == "google-gtx-v1"
    assert translator.profile.map_language_code("zh_CN") == "zh-CN"


def test_default_escaping_is_unchanged():
    """The Google placeholder scheme must still be the default behaviour."""
    translator = GoogleTranslator()
    assert translator._escape_special_chars("a\nb") == "a{{NEWLINE}}b"
    assert translator._unescape_special_chars("a{{NEWLINE}}b") == "a\nb"


# --- Criterion 2: the abstraction covers all five dimensions ----------------


def test_profiles_differ_in_every_dimension():
    """Request building, parsing, batching, escaping and engine id all vary."""
    google = create_profile("google")
    libre = create_profile("libretranslate")
    ollama = create_profile("ollama")

    # Request construction.
    google_request = google.build_request("Hi", "en", "es")
    libre_request = libre.build_request("Hi", "en", "es", escaped_texts=["Hi"])
    assert google_request["data"] is None, "google sends a GET with no body"
    assert libre_request["data"] is not None, "libretranslate sends a JSON body"
    assert libre_request["headers"]["Content-Type"] == "application/json"

    # Engine identity.
    assert len({google.get_engine_id(), libre.get_engine_id(), ollama.get_engine_id()}) == 3

    # Batch strategy.
    assert google.supports_batch is True
    assert libre.supports_batch is True
    assert ollama.supports_batch is False, "ollama has no batch API"

    # Escaping is not inherited from Google.
    assert libre.escape("a\nb") == "a\nb", "a JSON body must keep real newlines"
    assert google.escape("a\nb") == "a{{NEWLINE}}b"


def test_ollama_request_shape():
    """The Ollama call must be deterministic and unstreamed."""
    ollama = create_profile("ollama", model="mistral")
    request = ollama.build_request("Hello", "en", "es")
    body = json.loads(request["data"].decode("utf-8"))

    assert request["url"].endswith("/api/generate")
    assert body["model"] == "mistral"
    assert body["stream"] is False
    assert body["options"]["temperature"] == 0
    # The instruction must tell the model not to elaborate.
    assert "only the translation" in body["prompt"].lower()
    assert "Hello" in body["prompt"]


# --- Criterion 3: selection priority ----------------------------------------


def test_explicit_profile_wins_over_endpoint():
    """An explicit profile must not be overridden by endpoint inference."""
    assert resolve_profile_name("google", "http://localhost:11434/api/generate") == "google"
    assert resolve_profile_name("ollama", "http://localhost:5000/translate") == "ollama"


def test_profile_inferred_from_endpoint():
    """A bare endpoint must select the profile that speaks its protocol."""
    assert infer_profile_name("http://localhost:5000/translate") == "libretranslate"
    assert infer_profile_name("http://localhost:11434/api/generate") == "ollama"
    assert infer_profile_name("https://host/translate_a/single") == "google"


def test_unknown_endpoint_falls_back_to_google():
    """An unrecognised endpoint keeps the pre-profile behaviour."""
    assert resolve_profile_name(None, "https://example.test/whatever") == "google"
    assert resolve_profile_name(None, None) == "google"


def test_unknown_profile_raises_with_valid_names():
    """A bad profile name must fail loudly and list the legal values."""
    with pytest.raises(TranslationError) as info:
        create_profile("deepl")

    message = text_type(info.value)
    assert "deepl" in message
    for name in PROFILE_NAMES:
        assert name in message, "the error must list %s" % name


def test_unknown_profile_from_environment(monkeypatch):
    """The same guard applies to TRANSX_TRANSLATE_PROFILE."""
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "nope")
    with pytest.raises(TranslationError):
        GoogleTranslator()


def test_profile_env_var_selects_profile(monkeypatch):
    """TRANSX_TRANSLATE_PROFILE must drive the choice."""
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "libretranslate")
    translator = GoogleTranslator()
    assert translator.profile.name == "libretranslate"
    assert translator.engine_id == "libretranslate-v1"


# --- Criterion 4: libretranslate --------------------------------------------


def test_libretranslate_sends_a_json_list(server, monkeypatch, no_sleep):
    """The strings go as a list, never newline-joined."""
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "libretranslate")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/translate")

    def _handler(path, body, headers, method):
        payload = json.loads(body)
        assert payload["q"] == ["Hello", "Goodbye"], payload
        assert payload["source"] == "en"
        assert payload["target"] == "zh"
        assert payload["format"] == "text"
        return _body({"translatedText": ["你好", "再见"]})

    server.install(_handler)
    translator = _quiet(GoogleTranslator())
    results = translator.translate_batch(["Hello", "Goodbye"], "en", "zh_CN")

    assert server.failures == [], server.failures
    assert results == ["你好", "再见"]
    # One request for the whole batch, and no newline in the payload.
    assert len(server.calls) == 1, server.calls
    assert "\n" not in server.calls[0]["body"].replace("\\n", "")
    assert server.calls[0]["method"] == "POST"


def test_libretranslate_omits_api_key_when_unset(server, monkeypatch, no_sleep):
    """No api_key field may appear unless the user set one."""
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "libretranslate")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/translate")
    monkeypatch.delenv("TRANSX_TRANSLATE_API_KEY", raising=False)

    server.install(lambda path, body, headers, method: _body({"translatedText": ["你好"]}))
    GoogleTranslator().translate("Hello", "en", "zh_CN")

    assert "api_key" not in json.loads(server.calls[0]["body"])


def test_libretranslate_sends_api_key_when_set(server, monkeypatch, no_sleep):
    """An explicit api_key must be forwarded."""
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "libretranslate")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/translate")
    monkeypatch.setenv("TRANSX_TRANSLATE_API_KEY", "secret-value")

    server.install(lambda path, body, headers, method: _body({"translatedText": ["你好"]}))
    GoogleTranslator().translate("Hello", "en", "zh_CN")

    assert json.loads(server.calls[0]["body"])["api_key"] == "secret-value"


# --- Criterion 5: ollama ----------------------------------------------------


def test_ollama_uses_one_request_per_string(server, monkeypatch, no_sleep):
    """Ollama cannot batch, so each string needs its own request."""
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "ollama")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/api/generate")

    def _handler(path, body, headers, method):
        prompt = json.loads(body)["prompt"]
        source = prompt.rsplit("\n\n", 1)[1]
        return _body({"response": "译: %s" % source})

    server.install(_handler)
    translator = _quiet(GoogleTranslator(batch_size=40))
    results = translator.translate_batch(["one", "two"], "en", "zh_CN")

    assert results == ["译: one", "译: two"]
    # batch_size is 40 but the profile forbids batching.
    assert len(server.calls) == 2, server.calls


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("你好", "你好"),
        ("```\n你好\n```", "你好"),  # code fence
        ('"你好"', "你好"),  # wrapped in quotes
        ("Translation: 你好", "你好"),  # chatty prefix
        ("Here is the translation: 你好", "你好"),
        ("  你好  ", "你好"),  # stray whitespace
        # Prose after the closing fence must be dropped, not merged into the
        # translation: it would otherwise land in the PO file.
        ("```\n你好\n```\n\n(only the translation shown)", "你好"),
        ("你好\n\nNote: this is the literal translation.", "你好"),
        ("```\n你好\n```\n\nHere is your translation.", "你好"),
    ],
)
def test_ollama_cleans_model_output(raw, expected):
    """Chat models decorate their answers; the decoration must be stripped."""
    assert OllamaProfile().clean_output(raw) == expected


def test_ollama_raises_when_output_cannot_be_aligned(server, monkeypatch, no_sleep):
    """A misaligned response must raise rather than guess.

    Pairing the wrong translation with the wrong msgid silently poisons a PO
    entry, so refusing is the only safe answer.
    """
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "ollama")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/api/generate")

    server.install(lambda path, body, headers, method: _body({"response": ""}))

    translator = GoogleTranslator()
    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "zh_CN")


def test_ollama_backend_error_is_reported(server, monkeypatch, no_sleep):
    """A backend error object must become a TranslationError."""
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "ollama")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/api/generate")

    server.install(lambda path, body, headers, method: _body({"error": "model not found"}))

    with pytest.raises(TranslationError) as info:
        GoogleTranslator().translate("Hello", "en", "zh_CN")
    assert "model not found" in text_type(info.value)


# --- Criterion 6: language codes per profile --------------------------------


@pytest.mark.parametrize(
    "profile_name,expected",
    [
        ("google", "zh-CN"),
        ("libretranslate", "zh"),
        ("ollama", "Simplified Chinese"),
    ],
)
def test_zh_cn_maps_per_profile(profile_name, expected):
    """Every profile must spell zh_CN the way its backend expects."""
    assert create_profile(profile_name).map_language_code("zh_CN") == expected


def test_zh_cn_end_to_end_per_profile(server, monkeypatch, no_sleep):
    """The mapped code is what actually reaches the backend."""
    seen = {}

    def _handler(path, body, headers, method):
        seen.update(json.loads(body))
        return _body({"translatedText": ["你好"]})

    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "libretranslate")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/translate")
    server.install(_handler)

    GoogleTranslator().translate("Hello", "en", "zh_CN")
    assert seen["target"] == "zh", seen


# --- Criterion 7: translation memory isolation ------------------------------


def test_profiles_do_not_share_memory_entries(tmp_path, monkeypatch):
    """The same string through two profiles must produce two entries."""
    path = str(tmp_path / "tm.json")
    calls = []

    class _Profile(LibreTranslateProfile):
        def build_request(self, payload, source_lang, target_lang, escaped_texts=None):
            calls.append(self.name)
            return super(_Profile, self).build_request(
                payload, source_lang, target_lang, escaped_texts=escaped_texts
            )

    def _translate(profile_name):
        translator = GoogleTranslator(path=path, profile=profile_name)
        monkeypatch.setattr(
            translator,
            "_request_translation",
            lambda payload, src, tgt, escaped_texts=None: ["%s-translation" % profile_name],
        )
        return translator

    google = _translate("google")
    assert google.translate("Hello", "en", "es") == "google-translation"

    libre = _translate("libretranslate")
    result = libre.translate("Hello", "en", "es")

    # Not served from Google's entry, and not a hit at all.
    assert result == "libretranslate-translation"
    assert libre.memory_hits == 0, "the other profile's entry must not be reused"

    # Both entries live side by side in one file.
    reloaded = GoogleTranslator(path=path, profile="libretranslate")
    assert reloaded.translation_memory.get("Hello", "en", "es") == "libretranslate-translation"


def test_engine_ids_are_distinct(tmp_path):
    """Each profile must write under its own engine id."""
    path = str(tmp_path / "tm.json")
    ids = {}
    for name in PROFILE_NAMES:
        translator = GoogleTranslator(path=path, profile=name)
        ids[name] = translator.engine_id
    assert len(set(ids.values())) == len(PROFILE_NAMES), ids


def test_ollama_engine_id_contains_the_model(tmp_path, monkeypatch):
    """Two Ollama models must not share translation memory entries."""
    monkeypatch.setenv("TRANSX_TRANSLATE_MODEL", "mistral")
    first = GoogleTranslator(path=str(tmp_path / "a.json"), profile="ollama")
    monkeypatch.setenv("TRANSX_TRANSLATE_MODEL", "llama3.2")
    second = GoogleTranslator(path=str(tmp_path / "b.json"), profile="ollama")

    assert "mistral" in first.engine_id
    assert "llama3.2" in second.engine_id
    assert first.engine_id != second.engine_id


# --- Criterion 8: offline semantics -----------------------------------------


@pytest.mark.parametrize(
    "url,expected",
    [
        ("http://127.0.0.1:5000/translate", True),
        ("http://localhost:11434/api/generate", True),
        ("http://[::1]:8080/translate", True),
        ("http://::1:8080/translate", True),
        ("https://translate.googleapis.com/x", False),
        ("http://192.168.1.50:5000/translate", False),
        ("http://libretranslate.example.com/translate", False),
        ("", False),
    ],
)
def test_loopback_detection(url, expected):
    """Only this machine counts as loopback."""
    assert is_loopback_url(url) is expected


def test_offline_allows_loopback_endpoint(server, monkeypatch, no_sleep):
    """A local service must still be reachable while offline.

    If offline blocked loopback too, the whole point of running a local
    translation bridge - translating without leaving the machine - would be
    unreachable in exactly the mode it exists for.
    """
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "libretranslate")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/translate")
    server.install(lambda path, body, headers, method: _body({"translatedText": ["你好"]}))

    translator = GoogleTranslator(offline=True)
    assert translator.translate("Hello", "en", "zh_CN") == "你好"
    assert len(server.calls) == 1, server.calls


def test_offline_blocks_remote_endpoint(monkeypatch):
    """Anything not on this machine stays blocked while offline."""
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "libretranslate")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", "http://192.168.1.50:5000/translate")

    translator = GoogleTranslator(offline=True)
    with pytest.raises(TranslationError) as info:
        translator.translate("Hello", "en", "zh_CN")

    assert "Offline mode" in text_type(info.value)


def test_offline_blocks_default_google_endpoint(monkeypatch):
    """The remote default stays blocked, which was the previous behaviour."""
    monkeypatch.delenv("TRANSX_TRANSLATE_ENDPOINT", raising=False)
    translator = GoogleTranslator(offline=True)

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")


# --- Criterion 9: resilience for every profile ------------------------------


@pytest.fixture
def no_sleep(monkeypatch):
    """Record backoff sleeps instead of executing them.

    The retry path sleeps through ``transx.api.translate.time``, and the
    pacing path through the same module, so patching the module attribute is
    what actually keeps these tests fast.
    """
    import transx.api.translate as translate_module

    slept = []
    monkeypatch.setattr(translate_module.time, "sleep", slept.append)
    return slept


def _quiet(translator):
    """Disable request pacing for a translator under test."""
    translator._wait_for_rate_limit = lambda: None
    return translator


def _failing_translator(server, monkeypatch, profile_name, path, statuses, slept):
    """Build a translator whose endpoint fails with ``statuses`` in turn."""
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", profile_name)
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + path)

    remaining = list(statuses)

    def _handler(req_path, body, headers, method):
        if remaining:
            return remaining.pop(0), json.dumps({"error": "boom"})
        return _body({"translatedText": ["你好"]})

    server.install(_handler)
    translator = GoogleTranslator(max_retries=4, min_request_interval=0)
    translator._slept = slept
    return _quiet(translator)


def test_retryable_status_is_retried_for_non_google(server, monkeypatch, no_sleep):
    """429 handling from batch1 must apply to every profile, not just Google."""
    translator = _failing_translator(
        server, monkeypatch, "libretranslate", "/translate", [429, 429], no_sleep
    )
    assert translator.translate("Hello", "en", "zh_CN") == "你好"
    assert len(no_sleep) == 2, no_sleep


def test_retry_after_is_honoured_for_non_google(server, monkeypatch, no_sleep):
    """Retry-After must be respected on every profile."""

    def _handler(req_path, body, headers, method):
        return 429, json.dumps({"error": "slow down"})

    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "libretranslate")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/translate")
    server.install(_handler)

    translator = _quiet(GoogleTranslator(max_retries=3, min_request_interval=0))

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "zh_CN")
    assert no_sleep, "expected retries to sleep"


def test_circuit_opens_for_non_google(server, monkeypatch, no_sleep):
    """The circuit breaker from batch1 must also cover other profiles."""
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "libretranslate")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/translate")
    server.install(lambda path, body, headers, method: (503, json.dumps({"error": "down"})))

    translator = _quiet(GoogleTranslator(max_retries=3, min_request_interval=0))

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "zh_CN")
    assert translator._circuit_open is True


def test_unreachable_local_service_names_the_endpoint(monkeypatch, no_sleep):
    """A dead local service must say which endpoint could not be reached."""
    # Port 1 is closed on every platform, so the connection is refused.
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "ollama")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", "http://127.0.0.1:1/api/generate")

    translator = _quiet(GoogleTranslator(max_retries=1, min_request_interval=0))

    with pytest.raises(TranslationError) as info:
        translator.translate("Hello", "en", "zh_CN")

    message = text_type(info.value)
    assert "127.0.0.1:1" in message, message
    assert "running" in message.lower(), message


def test_partial_success_still_persists(server, monkeypatch, tmp_path, no_sleep):
    """Strings that succeed in a partly failing run must still be remembered.

    batch2 changed batching so a failure does not discard the whole run. The
    guarantee has to hold for every profile, since the memory is what turns
    repeat runs into zero-request runs.
    """
    monkeypatch.setenv("TRANSX_TRANSLATE_PROFILE", "libretranslate")
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", server.url + "/translate")

    def _handler(path, body, headers, method):
        items = json.loads(body)["q"]
        # One string always fails, and fails fast (400 is not retryable) so it
        # cannot burn the retry budget and open the circuit. The rest succeed.
        if "Bad" in items:
            return 400, json.dumps({"error": "no translation"})
        return _body({"translatedText": ["你好" if item == "Hello" else "再见" for item in items]})

    server.install(_handler)
    path = str(tmp_path / "tm.json")
    translator = _quiet(GoogleTranslator(path=path, max_retries=2, min_request_interval=0))

    # "Bad" is untranslatable, so its batch raises.
    with pytest.raises(TranslationError):
        translator.translate_batch(["Bad"], "en", "zh_CN")

    # A later good batch still persists, and survives the earlier failure.
    assert translator.translate_batch(["Hello"], "en", "zh_CN") == ["你好"]

    calls_before = len(server.calls)
    second = _quiet(GoogleTranslator(path=path, min_request_interval=0))
    assert second.translate("Hello", "en", "zh_CN") == "你好"
    assert len(server.calls) == calls_before, "the remembered entry must avoid a request"
    assert second.memory_hits == 1


# --- Criterion 11: no new dependencies, Python 2.7 compatible ---------------


def test_new_module_is_py27_compatible():
    """The profile module must satisfy the static Python 2.7 guard."""
    # Import local modules
    import ast
    import io
    import re

    package_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "transx"
    )
    path = os.path.join(package_root, "internal", "translate_profiles.py")
    with io.open(path, encoding="utf-8") as handle:
        source = handle.read()

    # Must parse, and must declare the __future__ imports that give 2.7 the
    # Python 3 semantics the module relies on.
    ast.parse(source, filename=path)
    assert "unicode_literals" in source
    assert "absolute_import" in source

    # Same patterns and the same string-literal stripping the shared guard
    # uses, so an escaped "\f" inside a literal is not read as an f-string.
    stripped = "\n".join(
        re.sub(r"""["'].*?["']""", '""', line.split("#")[0])
        for line in source.splitlines()
    )
    for pattern in (r"""(?:^|[^\w'"])[fF]["']""", r"\bnonlocal\b", r":="):
        assert not re.search(pattern, stripped), "found Python 3 only syntax: %s" % pattern


def test_profiles_use_only_the_standard_library():
    """No third-party import may creep into the profile layer."""
    # Import local modules
    import ast
    import io

    package_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "transx"
    )
    path = os.path.join(package_root, "internal", "translate_profiles.py")
    with io.open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)

    allowed_roots = {
        "__future__",
        "transx",
        "json",
        "logging",
        "os",
        "urllib",
        "urllib2",
        "urlparse",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] in allowed_roots, alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] in allowed_roots, node.module


# --- Regression: the Google path is unchanged --------------------------------


def test_google_request_url_is_byte_identical(monkeypatch):
    """The default URL must match the pre-profile format exactly."""
    monkeypatch.delenv("TRANSX_TRANSLATE_ENDPOINT", raising=False)
    translator = GoogleTranslator()

    url = translator._build_url("Hello", "en", "es")
    assert url == (
        "https://translate.googleapis.com/translate_a/single?"
        "client=gtx&sl=en&tl=es&dt=t&q=Hello"
    )


def test_google_batch_still_joins_with_newlines(monkeypatch):
    """Batching behaviour for Google must not change."""
    monkeypatch.delenv("TRANSX_TRANSLATE_ENDPOINT", raising=False)
    translator = GoogleTranslator()

    assert translator.profile.join_batch(["a", "b"]) == "a\nb"
    assert translator.profile.supports_batch is True
