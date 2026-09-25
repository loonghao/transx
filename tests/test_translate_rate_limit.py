#!/usr/bin/env python
"""Regression tests for GH #38 - "Too Many Requests" during translation.

The live Google endpoint rate limits aggressively and the old retry logic could
not cope: it used a pure exponential backoff with no jitter, ignored the
``Retry-After`` response header, and gave up after only a handful of attempts.

These tests are fully hermetic - ``urlopen`` is faked and ``time.sleep`` is
recorded instead of executed, so nothing touches the network.
"""

# Import future modules
from __future__ import unicode_literals

# Import built-in modules
import time

# Import third-party modules
import pytest

# Import local modules
import transx.api.translate as translate_module
from transx.api.translate import GoogleTranslator
from transx.exceptions import TranslationError
from transx.internal.compat import PY2

if PY2:  # pragma: no cover - exercised only on Python 2
    from urllib2 import HTTPError
else:
    from urllib.error import HTTPError


class _FakeHeaders(object):
    """Minimal stand-in for the ``headers`` attribute of an HTTPError."""

    def __init__(self, values=None):
        self._values = values or {}

    def get(self, key, default=None):
        return self._values.get(key, default)


def _http_error(code, headers=None):
    """Build an HTTPError carrying optional headers."""
    return HTTPError("https://translate.google.com/m", code, "error", _FakeHeaders(headers), None)


@pytest.fixture
def translator(monkeypatch):
    """A GoogleTranslator that records sleeps instead of sleeping."""
    instance = GoogleTranslator(max_retries=6, initial_delay=2, max_delay=3600)
    slept = []

    monkeypatch.setattr(time, "sleep", slept.append)
    monkeypatch.setattr(instance, "_wait_for_rate_limit", lambda: None)
    instance._slept = slept
    return instance


def _raise(translator, error):
    """Make every request fail with ``error``."""

    def _fake_urlopen(request):
        raise error

    translate_module.urlopen = _fake_urlopen
    return translate_module


def _ok_response(translator, body='<div class="result-container">Hola</div>'):
    """Make every request succeed with ``body``."""

    class _Response(object):
        headers = _FakeHeaders()

        def read(self):
            return body.encode("utf-8")

    def _fake_urlopen(request):
        return _Response()

    translate_module.urlopen = _fake_urlopen
    return translate_module


# --- Retry-After handling ----------------------------------------------------


def test_retry_after_seconds_is_honoured(translator, monkeypatch):
    """A numeric Retry-After must become the wait, not the computed backoff."""
    module = _raise(translator, _http_error(429, {"Retry-After": "30"}))
    monkeypatch.setattr(module.time, "sleep", translator._slept.append)

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    # The server asked for 30s, so every wait must be exactly 30s.
    assert translator._slept, "expected at least one backoff sleep"
    assert all(wait == 30 for wait in translator._slept), translator._slept


def test_retry_after_http_date_is_honoured(translator, monkeypatch):
    """An HTTP-date Retry-After must be converted into a sensible wait."""
    future = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time.time() + 45))
    module = _raise(translator, _http_error(429, {"Retry-After": future}))
    monkeypatch.setattr(module.time, "sleep", translator._slept.append)

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    assert translator._slept, "expected at least one backoff sleep"
    # ~45s out; allow slack for the clock moving during the test.
    assert all(40 <= wait <= 46 for wait in translator._slept), translator._slept


def test_retry_after_beyond_max_delay_is_ignored(translator, monkeypatch):
    """A Retry-After longer than max_delay must fall back to backoff."""
    translator.max_delay = 10
    module = _raise(translator, _http_error(429, {"Retry-After": "99999"}))
    monkeypatch.setattr(module.time, "sleep", translator._slept.append)

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    assert translator._slept, "expected at least one backoff sleep"
    assert all(wait <= 10 for wait in translator._slept), translator._slept


def test_invalid_retry_after_falls_back_to_backoff(translator, monkeypatch):
    """An unparseable Retry-After must not break the retry loop."""
    module = _raise(translator, _http_error(429, {"Retry-After": "soon"}))
    monkeypatch.setattr(module.time, "sleep", translator._slept.append)

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    assert translator._slept, "expected at least one backoff sleep"
    assert all(wait >= 0 for wait in translator._slept), translator._slept


def test_parse_retry_after_rejects_garbage():
    """``_parse_retry_after`` must return None for unusable values."""
    translator = GoogleTranslator()
    assert translator._parse_retry_after(None) is None
    assert translator._parse_retry_after("") is None
    assert translator._parse_retry_after("not-a-date") is None
    assert translator._parse_retry_after("-5") == 0.0
    assert translator._parse_retry_after("12") == 12


# --- Jitter and backoff growth ----------------------------------------------


def test_backoff_is_randomized(translator):
    """Repeated failures must not all wait the identical amount (jitter)."""
    translator._slept.clear()
    delays = set()
    for _ in range(12):
        translator._consecutive_failures = 0
        delays.add(translator._backoff_delay())
    assert len(delays) > 1, "backoff was not randomized: %s" % delays


def test_backoff_grows_with_consecutive_failures(translator):
    """The backoff ceiling must increase as failures accumulate."""
    translator._consecutive_failures = 0
    translator._current_delay = 2
    translator.max_delay = 10**6

    ceilings = []
    for _ in range(4):
        # Sample the ceiling by averaging many jittered draws.
        draws = []
        for _ in range(200):
            translator._consecutive_failures = len(ceilings)
            draws.append(translator._backoff_delay())
        ceilings.append(sum(draws) / len(draws))

    assert ceilings == sorted(ceilings), ceilings
    assert ceilings[-1] > ceilings[0], ceilings


def test_backoff_never_exceeds_max_delay(translator):
    """``max_delay`` must clamp the wait even after many failures."""
    translator.max_delay = 5
    translator.initial_delay = 2
    for failures in range(1, 12):
        translator._consecutive_failures = failures - 1
        assert translator._backoff_delay() <= 5


def test_no_sleep_on_final_attempt(translator, monkeypatch):
    """Giving up must not sleep first - that only stalls the caller."""
    module = _raise(translator, _http_error(429))
    monkeypatch.setattr(module.time, "sleep", translator._slept.append)
    translator.max_retries = 3

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    assert len(translator._slept) == 2, translator._slept


# --- Retryable status codes --------------------------------------------------


@pytest.mark.parametrize("code", [429, 500, 502, 503, 504])
def test_retryable_status_codes_are_retried(translator, monkeypatch, code):
    """Transient server statuses must be retried rather than raised."""
    module = _raise(translator, _http_error(code))
    monkeypatch.setattr(module.time, "sleep", translator._slept.append)

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    assert len(translator._slept) == translator.max_retries - 1, translator._slept


def test_non_retryable_status_raises_immediately(translator, monkeypatch):
    """A 404 must fail fast instead of burning the retry budget."""
    module = _raise(translator, _http_error(404))
    monkeypatch.setattr(module.time, "sleep", translator._slept.append)

    with pytest.raises(TranslationError):
        translator.translate("Hello", "en", "es")

    assert translator._slept == [], translator._slept


def test_translation_succeeds_after_transient_failures(translator, monkeypatch):
    """A request that succeeds on retry must return the translation."""
    calls = {"count": 0}

    def _flaky_urlopen(request):
        calls["count"] += 1
        if calls["count"] < 3:
            raise _http_error(429, {"Retry-After": "1"})

        class _Response(object):
            headers = _FakeHeaders()

            def read(self):
                return b'<div class="result-container">Hola</div>'

        return _Response()

    monkeypatch.setattr(translate_module, "urlopen", _flaky_urlopen)
    monkeypatch.setattr(translate_module.time, "sleep", translator._slept.append)

    assert translator.translate("Hello", "en", "es") == "Hola"
    assert calls["count"] == 3
    assert translator._slept == [1, 1], translator._slept


def test_successful_request_resets_backoff_state(translator, monkeypatch):
    """A success must clear the failure counter so the next failure starts small."""
    _ok_response(translator)
    translator._consecutive_failures = 4
    translator.translate("Hello", "en", "es")
    assert translator._consecutive_failures == 0


def test_min_request_interval_default_is_conservative():
    """The default pacing must be slower than the old 0.5s to avoid 429s."""
    assert GoogleTranslator()._min_request_interval >= 1.0
