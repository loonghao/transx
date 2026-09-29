#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hermetic tests for batched translation, budgeting and the circuit breaker.

Nothing here touches the network: ``urlopen`` is faked and ``time.sleep`` is
recorded instead of executed, matching the approach already used in
``tests/test_translate_rate_limit.py``.
"""

# Import future modules
from __future__ import unicode_literals

# Import built-in modules
import json
import time

# Import third-party modules
import pytest

# Import local modules
import transx.api.translate as translate_module
from transx.api.translate import GoogleTranslator
from transx.exceptions import TranslationError
from transx.internal.compat import PY2
from transx.internal.compat import unquote_plus

if PY2:  # pragma: no cover - exercised only on Python 2
    from urllib2 import HTTPError
else:
    from urllib.error import HTTPError


def _batch_response(translated):
    """Build a response body shaped like the real endpoint's.

    The endpoint echoes the newline separator back at the end of every segment
    except the last, which is what makes splitting the flattened payload
    reproduce the input count.

    Args:
        translated: Sequence of translated strings

    Returns:
        str: JSON response body
    """
    segments = []
    for index, text in enumerate(translated):
        suffix = "\n" if index < len(translated) - 1 else ""
        segments.append([text + suffix, "", None, None, 10])
    return json.dumps([segments, None, "en"], ensure_ascii=False)


class _FakeHeaders(object):
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, key, default=None):
        return self._values.get(key, default)


def _http_error(code, headers=None):
    return HTTPError("https://translate.googleapis.com/translate_a/single", code, "error", _FakeHeaders(headers), None)


class _Recorder(object):
    """Fakes ``urlopen``, capturing every payload the translator sends."""

    def __init__(self, handler):
        self.handler = handler
        self.payloads = []
        self.urls = []

    def __call__(self, request):
        self.urls.append(request.full_url)
        self.payloads.append(_extract_payload(request.full_url))
        return self.handler(self.payloads[-1])


def _extract_payload(url):
    """Pull the ``q`` parameter back out of a request URL."""

    query = url.split("?", 1)[1] if "?" in url else ""
    for pair in query.split("&"):
        if pair.startswith("q="):
            return unquote_plus(pair[2:])
    return ""


def _ok_handler(translated):
    """Answer every request with the given translation(s)."""

    def _handle(payload):
        return _Response(_batch_response(translated))

    return _handle


class _Response(object):
    headers = _FakeHeaders()

    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body.encode("utf-8")


@pytest.fixture
def translator(monkeypatch):
    """A translator with sleeps recorded and the minimum interval disabled."""
    instance = GoogleTranslator(batch_size=40, max_batch_chars=3000)
    slept = []
    monkeypatch.setattr(time, "sleep", slept.append)
    monkeypatch.setattr(translate_module.time, "sleep", slept.append)
    monkeypatch.setattr(instance, "_wait_for_rate_limit", lambda: None)
    instance._slept = slept
    return instance


def _install(monkeypatch, recorder):
    monkeypatch.setattr(translate_module, "urlopen", recorder)
    return recorder


# --- Separator handling ------------------------------------------------------


def test_batch_joins_with_real_newlines(translator, monkeypatch):
    """The payload must carry real newlines so the endpoint batches."""
    recorder = _install(monkeypatch, _Recorder(_ok_handler(["A", "B"])))

    translator.translate_batch(["Hello", "Goodbye"], "en", "es")

    assert recorder.payloads == ["Hello\nGoodbye"], recorder.payloads


def test_separator_survives_escaping(translator, monkeypatch):
    """Escaping must run before joining, never after.

    Reversed, ``_escape_special_chars`` would turn the separator into
    ``{{NEWLINE}}`` and batching would silently never take effect.
    """
    recorder = _install(monkeypatch, _Recorder(_ok_handler(["A", "B"])))

    # A newline inside the source text must not become a batch separator.
    translator.translate_batch(["line one\nline two", "second"], "en", "es")

    assert recorder.payloads == ["line one{{NEWLINE}}line two\nsecond"], recorder.payloads


def test_single_string_has_no_separator(translator, monkeypatch):
    """A one string batch must not gain a trailing separator."""
    recorder = _install(monkeypatch, _Recorder(_ok_handler(["A"])))

    translator.translate("Hello", "en", "es")

    assert recorder.payloads == ["Hello"], recorder.payloads


# --- Response alignment ------------------------------------------------------


def test_results_align_with_input(translator, monkeypatch):
    """Flattening and splitting must reproduce one result per input."""
    _install(monkeypatch, _Recorder(_ok_handler(["uno", "dos", "tres"])))

    assert translator.translate_batch(["one", "two", "three"], "en", "es") == ["uno", "dos", "tres"]


def test_sentence_split_batch_falls_back_per_item(translator, monkeypatch):
    """A multi sentence input can return more segments than inputs.

    The endpoint splits on sentences rather than on lines, so a batch can come
    back misaligned. Falling back to one request per string keeps every result
    matched to its input.
    """
    payloads = []

    def _handler(payload):
        payloads.append(payload)
        if "\n" in payload:
            # Two sentences in the first string become two segments.
            return _Response(_batch_response(["uno.", "dos.", "tres", "cuatro"]))
        return _Response(_batch_response([payload[::-1]]))

    recorder = _install(monkeypatch, _Recorder(_handler))

    results = translator.translate_batch(["Hello world. Goodbye world.", "Save file", "Open"], "en", "es")

    assert results == ["Hello world. Goodbye world."[::-1], "elif evaS", "nepO"]
    # The misaligned batch is retried one string at a time.
    assert len(recorder.payloads) == 4, recorder.payloads


def test_newlines_in_source_are_restored(translator, monkeypatch):
    """A newline belonging to the source text must come back unchanged."""
    _install(monkeypatch, _Recorder(_ok_handler(["uno{{NEWLINE}}dos"])))

    assert translator.translate("one\ntwo", "en", "es") == "uno\ndos"


def test_html_entities_are_decoded(translator, monkeypatch):
    """Entities in the response must be decoded per item."""
    _install(monkeypatch, _Recorder(_ok_handler(["caf&copy;"])))

    assert translator.translate("caf", "en", "es") == "caf©"


def test_missing_segments_raise(translator, monkeypatch):

    def _handler(payload):
        return _Response(json.dumps([[], None, "en"]))

    _install(monkeypatch, _Recorder(_handler))

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")


def test_non_json_response_raises(translator, monkeypatch):

    def _handler(payload):
        return _Response("<html>not json</html>")

    _install(monkeypatch, _Recorder(_handler))

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")


# --- Request budgeting -------------------------------------------------------


def test_item_budget_splits_batches(translator, monkeypatch):
    recorder = _install(monkeypatch, _Recorder(lambda payload: _Response(_batch_response(payload.split("\n")))))
    translator.batch_size = 3

    translator.translate_batch(["a", "b", "c", "d", "e"], "en", "es")

    assert recorder.payloads == ["a\nb\nc", "d\ne"], recorder.payloads


def test_character_budget_splits_batches(translator, monkeypatch):
    recorder = _install(monkeypatch, _Recorder(lambda payload: _Response(_batch_response(payload.split("\n")))))
    translator.batch_size = 100
    # Each string costs 6 characters: 5 of text plus the joining separator.
    translator.max_batch_chars = 12

    translator.translate_batch(["12345", "67890", "abcde"], "en", "es")

    # Two strings fit in 12 characters; the third starts a new request.
    assert recorder.payloads == ["12345\n67890", "abcde"], recorder.payloads


def test_budget_counts_the_separators(translator):
    """The separators between strings must count towards the budget."""
    translator.batch_size = 100
    translator.max_batch_chars = 12

    # Each item costs 6 (5 characters plus its separator), so two cost 12 and
    # fit exactly while the third would push the batch to 18.
    chunks = list(translator._iter_chunks(["12345", "67890", "abcde"]))

    assert chunks == [["12345", "67890"], ["abcde"]], chunks

    # One character less and only a single item fits: the separator is what
    # tips it over, which is the behaviour this test pins down.
    translator.max_batch_chars = 11
    chunks = list(translator._iter_chunks(["12345", "67890", "abcde"]))

    assert chunks == [["12345"], ["67890"], ["abcde"]], chunks


def test_budget_measures_escaped_and_encoded_length(translator):
    """Long CJK msgids must not push the request URL past the budget.

    A raw character count badly understates CJK: URL encoding turns one
    Chinese character into nine bytes. Budgeting on the raw count let a
    payload that "fit" 3000 characters reach the endpoint as a ~25KB URL and
    come back as a non-retryable 414.
    """
    translator.batch_size = 1000
    translator.max_batch_chars = 3000

    # 70 Chinese characters encode to 630 bytes each, plus one separator.
    chunks = list(translator._iter_chunks(["你好" * 35] * 40))

    assert len(chunks) == 10, len(chunks)
    assert all(len(chunk) <= 4 for chunk in chunks), [len(chunk) for chunk in chunks]


def test_cjk_request_url_stays_within_budget(translator, monkeypatch):
    """The same nail-down end to end: no request may exceed the budget."""
    recorder = _install(monkeypatch, _Recorder(lambda payload: _Response(_batch_response(payload.split("\n")))))

    translator.translate_batch(["你好" * 35] * 40, "en", "zh-CN")

    longest = max(len(url) for url in recorder.urls)
    # Before the fix the same input produced a single ~25KB URL.
    assert longest <= translator.max_batch_chars + 100, longest
    assert len(recorder.urls) > 1, len(recorder.urls)


def test_oversized_single_string_is_sent_alone(translator, monkeypatch):
    """A string larger than the budget must still be translated, not dropped."""
    recorder = _install(monkeypatch, _Recorder(lambda payload: _Response(_batch_response([payload]))))
    translator.max_batch_chars = 5

    long_text = "x" * 50
    assert translator.translate_batch([long_text, "ok"], "en", "es") == [long_text, "ok"]
    assert recorder.payloads == [long_text, "ok"], recorder.payloads


def test_endpoint_override_is_honoured(translator, monkeypatch):
    """TRANSX_TRANSLATE_ENDPOINT must redirect requests."""
    monkeypatch.setenv("TRANSX_TRANSLATE_ENDPOINT", "https://example.test/translate")
    recorder = _install(monkeypatch, _Recorder(_ok_handler(["uno"])))

    translator.translate("Hello", "en", "es")

    assert recorder.urls[0].startswith("https://example.test/translate?"), recorder.urls[0]
    assert "dt=t" in recorder.urls[0], recorder.urls[0]
    assert "client=gtx" in recorder.urls[0], recorder.urls[0]


# --- Circuit breaker ---------------------------------------------------------


def test_circuit_opens_after_exhausted_budget(translator, monkeypatch):
    """Burning a whole retry budget must open the circuit."""
    _install(monkeypatch, _Recorder(lambda payload: (_ for _ in ()).throw(_http_error(429))))

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    assert translator._circuit_open is True


def test_open_circuit_sends_no_requests(translator, monkeypatch):
    """Once open, no request may be sent and no time may be slept."""
    calls = []

    def _handler(payload):
        calls.append(payload)
        return _Response(_batch_response(["uno"]))

    _install(monkeypatch, _Recorder(_handler))
    translator._circuit_open = True
    translator._circuit_failures = 8

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    assert calls == []
    assert translator._slept == []


def test_circuit_opens_before_the_last_sleep(translator, monkeypatch):
    """Opening the circuit must skip the sleep that would otherwise follow."""
    _install(monkeypatch, _Recorder(lambda payload: (_ for _ in ()).throw(_http_error(429))))
    translator.max_retries = 3
    translator.circuit_threshold = 3

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    # Three attempts minus the final one, which opens the circuit instead.
    assert len(translator._slept) == 2, translator._slept


def test_success_closes_the_circuit(translator, monkeypatch):
    """A successful request must clear the circuit again."""
    _install(monkeypatch, _Recorder(lambda payload: (_ for _ in ()).throw(_http_error(429))))

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")
    assert translator._circuit_open is True

    translator.reset_circuit()
    _install(monkeypatch, _Recorder(_ok_handler(["uno"])))
    assert translator.translate("Hello", "en", "es") == "uno"
    assert translator._circuit_open is False
    assert translator._circuit_failures == 0


def test_reset_circuit_restores_state(translator):
    translator._circuit_open = True
    translator._circuit_failures = 9
    translator._consecutive_failures = 4

    translator.reset_circuit()

    assert translator._circuit_open is False
    assert translator._circuit_failures == 0
    assert translator._consecutive_failures == 0


def test_batch_of_many_strings_costs_few_requests(translator, monkeypatch):
    """200 strings at 40 per request must not need more than 5 requests."""

    def _handler(payload):
        return _Response(_batch_response(payload.split("\n")))

    recorder = _install(monkeypatch, _Recorder(_handler))

    texts = ["Message number %d" % index for index in range(200)]
    results = translator.translate_batch(texts, "en", "es")

    assert len(results) == 200
    assert len(recorder.payloads) <= 5, len(recorder.payloads)


def test_failure_count_tracks_untranslated_items(translator, monkeypatch):
    """Items lost to a failed batch must be counted for the exit code."""
    _install(monkeypatch, _Recorder(lambda payload: (_ for _ in ()).throw(_http_error(429))))
    translator.batch_size = 10

    with pytest.raises(TranslationError):
        translator.translate_batch(["a", "b", "c"], "en", "es")

    assert translator.failure_count == 3
