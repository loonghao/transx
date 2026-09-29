#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Translation functions for TransX."""

# Import future modules
# fmt: off
# isort: skip
from __future__ import unicode_literals

# Import built-in modules
import abc
import calendar
from email.utils import parsedate
import json
import logging
import os
import random
import time


try:
    # Import built-in modules
    from urllib import urlencode

    # Import third-party modules
    from HTMLParser import HTMLParser
    from urllib2 import HTTPError
    from urllib2 import Request
    from urllib2 import URLError
    from urllib2 import urlopen
except ImportError:
    from html import unescape as html_unescape
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen




# Import local modules
from transx.api.locale import normalize_language_code
from transx.api.po import POFile
from transx.constants import REQUEST_HEADERS
from transx.exceptions import TranslationError
from transx.internal.compat import PY2
from transx.internal.compat import binary_type
from transx.internal.compat import decompress_gzip
from transx.internal.compat import ensure_unicode
from transx.internal.compat import quote_plus
from transx.internal.compat import string_types
from transx.internal.compat import text_type
from transx.internal.translation_memory import TranslationMemory
from transx.internal.translation_memory import offline_enabled
from transx.internal.translation_memory import resolve_tm_path


# fmt: on


class Translator(object):
    """Base class for all translators."""

    if PY2:
        __metaclass__ = abc.ABCMeta
    else:
        __metaclass__ = abc.ABC

    @abc.abstractmethod
    def translate(self, text, source_lang="auto", target_lang="en"):
        """Translate text from source language to target language.

        Args:
            text (str): Text to translate
            source_lang (str): Source language code (default: auto)
            target_lang (str): Target language code (default: en)

        Returns:
            str: Translated text
        """
        raise NotImplementedError


class DummyTranslator(Translator):
    """A dummy translator that returns the input text unchanged."""

    def translate(self, text, source_lang="auto", target_lang="en"):
        """Return input text unchanged."""
        return text


def _bind_locale_root(translator, locale_root):
    """Point a translator's memory at the locale root, if it has one.

    The memory path is only resolved once, when it is first needed, so a
    translator built without an explicit path keeps following the locale root
    it is later given instead of quietly settling for the user level default.

    Args:
        translator: Translator whose memory should be redirected
        locale_root: Directory holding the ``<locale>/LC_MESSAGES`` tree
    """
    memory = getattr(translator, "translation_memory", None)
    if memory is None or not locale_root:
        return
    if getattr(translator, "_tm_path_explicit", False):
        return
    memory.path = resolve_tm_path(locale_root=locale_root)


def translate_po_file(pot_file_path, lang, output_dir=None, translator=None):
    logger = logging.getLogger(__name__)

    if not os.path.exists(pot_file_path):
        raise IOError("POT file not found: %s" % pot_file_path)

    # Load POT file
    pot = POFile(pot_file_path)
    pot.load()

    output_dir = output_dir or os.path.dirname(pot_file_path)
    # Create output directory if not exists
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Normalize language code
    lang = normalize_language_code(lang)

    # Create language-specific output directory
    if output_dir:
        lang_dir = os.path.join(output_dir, lang, "LC_MESSAGES")
        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir)
        po_file_path = os.path.join(lang_dir, "messages.po")
    else:
        # Use same directory as POT file
        pot_dir = os.path.dirname(pot_file_path)
        po_file_path = os.path.join(pot_dir, "%s.po" % lang)

    # Create PO file from POT
    po = POFile(po_file_path, locale=lang)
    po.load() if os.path.exists(po_file_path) else None

    # Update PO from POT
    po.update(pot)

    # Set language-specific metadata
    po.metadata.update(
        {
            "Language": lang,
            "Language-Team": "%s <LL@li.org>" % lang,
            "Plural-Forms": "nplurals=1; plural=0;" if lang.startswith("zh") else "nplurals=2; plural=(n != 1);",
        }
    )

    # Optionally translate untranslated entries
    if translator:
        _bind_locale_root(translator, output_dir)
        logger.info("Auto-translating untranslated strings for %s..." % lang)
        translated = po.translate_messages(translator, target_lang=lang)
        failures = getattr(po, "translation_failures", 0)
        if failures:
            logger.error(
                "Auto-translation for %s finished with %d failure(s) (%d translated)",
                lang,
                failures,
                translated,
            )

    # Save PO file
    po.save()
    return po_file_path


def translate_po_files(pot_file_path, languages, output_dir=None, translator=None):
    """Create PO files from POT file.

    Args:
        pot_file_path: Path to the POT file
        languages: List of language codes
        output_dir: Optional output directory for PO files
        translator: Optional translator instance for automatic translation
    """
    logger = logging.getLogger(__name__)

    if not os.path.exists(pot_file_path):
        raise IOError("POT file not found: %s" % pot_file_path)

    # Create PO files for each language
    for lang in languages:
        po_file_path = translate_po_file(pot_file_path, lang, output_dir, translator)
        logger.debug("Created/updated PO file: %s", po_file_path)


class GoogleTranslator(Translator):
    """Google Translate implementation backed by the JSON endpoint.

    The endpoint is undocumented and offers no quota guarantee. It does
    however accept several strings in one request when they are joined with a
    newline, which cuts the request count by roughly the batch size.

    Only a real newline works as the separator. A word-like token is
    translated rather than passed through: joining with ``"||SEP||"`` returns
    "September" in the middle of the output. The separator is inserted after
    ``_escape_special_chars`` has turned every newline that belongs to the
    source text into ``{{NEWLINE}}``, so a real newline in the payload can
    only ever be a separator.
    """

    BASE_URL = "https://translate.googleapis.com/translate_a/single"

    #: Environment variable that replaces BASE_URL, for self-hosted endpoints.
    ENDPOINT_ENV_VAR = "TRANSX_TRANSLATE_ENDPOINT"

    #: Identifies this engine in the translation memory, so entries cached
    #: from another backend are never reused under this one's name.
    ENGINE_ID = "google-gtx-v1"

    #: HTTP statuses that mean "try again later" rather than "give up".
    RETRYABLE_STATUS_CODES = frozenset([429, 500, 502, 503, 504])

    #: Default cap on the number of strings sent in a single request.
    DEFAULT_BATCH_SIZE = 40

    #: Default cap on the characters sent in a single request. The endpoint
    #: answers 414 once the URL grows too long, and 414 is not retryable, so
    #: oversized payloads are split into smaller batches instead of retried.
    DEFAULT_MAX_BATCH_CHARS = 3000

    def __init__(
        self,
        max_retries=8,
        initial_delay=2,
        max_delay=3600,
        min_request_interval=1.0,
        batch_size=DEFAULT_BATCH_SIZE,
        max_batch_chars=DEFAULT_MAX_BATCH_CHARS,
        circuit_threshold=None,
        translation_memory=None,
        path=None,
        offline=None,
        locale_root=None,
    ):
        """Initialize the translator.

        Args:
            max_retries (int): Maximum number of retry attempts
            initial_delay (int): Initial delay in seconds between retries
            max_delay (int): Maximum delay in seconds between retries
            min_request_interval (float): Minimum seconds between two requests
            batch_size (int): Maximum number of strings per request
            max_batch_chars (int): Maximum characters of payload per request
            circuit_threshold (int): Consecutive retryable failures that open
                the circuit. Defaults to ``max_retries``, so a single request
                that burns its whole retry budget opens it.
            translation_memory: Pre-built memory to use; one is created when
                omitted
            path: Explicit translation memory file path
            offline: When True no request is ever sent; misses fall back to
                the source text. Defaults to the TRANSX_OFFLINE environment
                variable.
            locale_root: Directory used to resolve a default memory path
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self._last_request_time = 0
        self._min_request_interval = min_request_interval
        self._consecutive_failures = 0
        self._current_delay = initial_delay
        self.logger = logging.getLogger(__name__)

        self.batch_size = max(1, int(batch_size))
        self.max_batch_chars = max(1, int(max_batch_chars))
        # Opening the circuit means "stop talking to the backend": later calls
        # must fail immediately instead of sleeping through another backoff.
        self.circuit_threshold = max_retries if circuit_threshold is None else circuit_threshold
        self._circuit_failures = 0
        self._circuit_open = False

        #: Number of strings this translator failed to translate.
        self.failure_count = 0

        self.offline = offline_enabled(offline)
        # An explicit path (or TRANSX_TM_PATH) must win over any locale root
        # discovered later, so remember that it was forced.
        self._tm_path_explicit = bool(path or os.environ.get(TranslationMemory.PATH_ENV_VAR))
        self._locale_root = locale_root
        if translation_memory is not None:
            self.translation_memory = translation_memory
        else:
            # Without a path, an env var or a locale root there is nowhere
            # sensible to persist, and falling back to a shared file in the
            # user's home directory would silently couple unrelated runs
            # together. Stay inert until a location is actually known.
            self.translation_memory = TranslationMemory(
                path=path,
                engine_id=self.ENGINE_ID,
                locale_root=locale_root,
                enabled=bool(path or self._tm_path_explicit or locale_root),
            )
        #: Number of strings served by the memory instead of the network.
        self.memory_hits = 0
        self.translation_memory.load()

        # Map standard language codes to Google Translate supported codes
        self.language_code_map = {"zh_CN": "zh-CN", "ja_JP": "ja", "ko_KR": "ko", "fr_FR": "fr", "es_ES": "es"}

    def reset_circuit(self):
        """Close the circuit and forget every failure counter."""
        self._circuit_open = False
        self._circuit_failures = 0
        self._consecutive_failures = 0
        self._current_delay = self.initial_delay

    def _wait_for_rate_limit(self):
        """Ensure minimum time between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()

    def _parse_retry_after(self, value):
        """Convert a ``Retry-After`` header value into a number of seconds.

        The header is either a delta in seconds or an HTTP date. Anything
        unparseable, negative, or absurdly large is rejected so the caller can
        fall back to the computed backoff.

        Args:
            value: Raw ``Retry-After`` header value, already stripped

        Returns:
            float: Seconds to wait, or ``None`` when the value is unusable
        """
        if not value:
            return None

        try:
            seconds = float(value)
        except (TypeError, ValueError):
            seconds = None

        if seconds is None:
            # Fall back to the HTTP-date form, e.g. "Wed, 21 Oct 2015 07:28:00 GMT".
            try:
                parsed = parsedate(value)
                if parsed is None:
                    return None
                seconds = calendar.timegm(parsed) - time.time()
            except (TypeError, ValueError, OverflowError):
                return None

        if seconds < 0:
            return 0.0
        if seconds > self.max_delay:
            return None
        return seconds

    def _backoff_delay(self, retry_after=None):
        """Compute how long to wait after a retryable failure.

        The delay is exponential in the number of consecutive failures and is
        then randomized (full jitter). Jitter matters because every client that
        gets rate limited at the same moment would otherwise retry in lockstep
        and immediately trip the limit again. A server supplied ``Retry-After``
        always wins, since it knows its own window.

        Args:
            retry_after: Seconds requested by the server, if any

        Returns:
            float: Seconds to wait
        """
        self._consecutive_failures += 1

        if retry_after is not None:
            delay = retry_after
            reason = "Retry-After header"
        else:
            ceiling = min(self._current_delay * (2 ** (self._consecutive_failures - 1)), self.max_delay)
            # Full jitter: randomize across the whole window instead of always
            # waiting the full amount.
            delay = random.uniform(0, ceiling) if ceiling else 0
            reason = "exponential backoff"

        delay = max(0.0, min(float(delay), float(self.max_delay)))
        self.logger.warning(
            "Rate limit hit (%s, attempt %s). Waiting %.2f seconds before retry",
            reason,
            self._consecutive_failures,
            delay,
        )
        return delay

    def _handle_rate_limit(self, retry_after=None):
        """Sleep off a rate limit using the computed backoff.

        Args:
            retry_after: Seconds requested by the server, if any
        """
        time.sleep(self._backoff_delay(retry_after))

    def _is_last_attempt(self, attempt):
        """Return True when no further retry will happen after ``attempt``.

        Sleeping through the full backoff only to give up anyway just stalls
        the caller, so the final failure skips the wait and surfaces the error.

        Args:
            attempt: Zero-based index of the attempt that just failed

        Returns:
            bool: True if this was the last permitted attempt
        """
        return attempt >= self.max_retries - 1

    def _reset_rate_limit_state(self):
        """Reset rate limiting state after successful request."""
        self._consecutive_failures = 0
        self._current_delay = self.initial_delay

    def _escape_special_chars(self, text):
        """Escape special characters for translation.

        Args:
            text (str): Text to escape

        Returns:
            str: Escaped text
        """
        text = ensure_unicode(text)

        replacements = {
            text_type("\n"): text_type("{{NEWLINE}}"),
            text_type("\r"): text_type("{{RETURN}}"),
            text_type("\t"): text_type("{{TAB}}"),
            text_type("\\"): text_type("{{BACKSLASH}}"),
            text_type('\\"'): text_type("{{QUOTE}}"),
            text_type("\b"): text_type("{{BACKSPACE}}"),
            text_type("\f"): text_type("{{FORMFEED}}"),
        }
        result = text
        for char, placeholder in replacements.items():
            result = result.replace(char, placeholder)
        return result

    def _unescape_special_chars(self, text):
        """Restore special characters after translation.

        Args:
            text (str): Text to unescape

        Returns:
            str: Unescaped text
        """
        text = ensure_unicode(text)

        replacements = {
            text_type("{{NEWLINE}}"): text_type("\n"),
            text_type("{{RETURN}}"): text_type("\r"),
            text_type("{{TAB}}"): text_type("\t"),
            text_type("{{BACKSLASH}}"): text_type("\\"),
            text_type("{{QUOTE}}"): text_type('\\"'),
            text_type("{{BACKSPACE}}"): text_type("\b"),
            text_type("{{FORMFEED}}"): text_type("\f"),
        }
        result = text
        for placeholder, char in replacements.items():
            result = result.replace(placeholder, char)
        return result

    def _unescape_html_entities(self, text):
        """Decode HTML entities that may appear in translator responses."""
        text = ensure_unicode(text)
        if not text:
            return text

        try:
            if PY2:
                return ensure_unicode(HTMLParser().unescape(text))
            return ensure_unicode(html_unescape(text))
        except Exception:
            return text

    def _resolve_base_url(self):
        """Return the endpoint to call.

        ``TRANSX_TRANSLATE_ENDPOINT`` overrides the default so a self-hosted
        or future endpoint can be used without a code change.

        Returns:
            str: Endpoint URL
        """
        return os.environ.get(self.ENDPOINT_ENV_VAR) or self.BASE_URL

    def _build_url(self, payload, source_lang, target_lang):
        """Build the request URL for an already escaped payload.

        Args:
            payload: Escaped text, newline-joined when it holds a batch
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            str: Full request URL
        """
        params = [
            ("client", "gtx"),
            ("sl", source_lang),
            ("tl", target_lang),
            ("dt", "t"),
            ("q", payload.encode("utf-8")),
        ]
        return self._resolve_base_url() + "?" + urlencode(params)

    def _extract_translation(self, response_data):
        """Flatten the translated segments of a JSON response.

        The endpoint answers with nested arrays; the translated text of each
        segment sits at ``data[0][i][0]``. Segments are joined without a
        separator so the newlines the endpoint echoes back survive for the
        caller to split on.

        Args:
            response_data (str): Decoded response body

        Returns:
            str: Concatenated translated payload

        Raises:
            TranslationError: If the body holds no usable translation
        """
        try:
            data = json.loads(response_data)
        except ValueError as e:
            raise TranslationError("Failed to parse translation response: %s" % e)

        segments = data[0] if isinstance(data, list) and data else None
        if not segments:
            raise TranslationError("Could not find translation in response")

        parts = []
        for segment in segments:
            if not segment:
                continue
            text = segment[0]
            if text is None:
                continue
            parts.append(ensure_unicode(text))

        if not parts:
            raise TranslationError("Could not find translation in response")

        return "".join(parts)

    def _record_failure(self, attempt):
        """Account for a retryable failure.

        Returns:
            bool: True when the retry loop should stop immediately
        """
        self._circuit_failures += 1
        if self._circuit_failures >= self.circuit_threshold:
            self._circuit_open = True
            self.logger.error(
                "Translation circuit open after %d consecutive failures; "
                "remaining strings will fail without further requests.",
                self._circuit_failures,
            )
            return True
        return self._is_last_attempt(attempt)

    def _request_translation(self, payload, source_lang, target_lang):
        """Send one request and return the translated payload.

        Args:
            payload: Escaped text, newline-joined when it holds a batch
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            str: Translated payload, separators preserved

        Raises:
            TranslationError: If the circuit is open or every attempt failed
        """
        if self.offline:
            raise TranslationError(
                "Offline mode is enabled; refusing to send a translation request."
            )

        if self._circuit_open:
            raise TranslationError(
                "Translation circuit is open after %d consecutive failures; "
                "no further requests will be sent." % self._circuit_failures
            )

        url = self._build_url(payload, source_lang, target_lang)
        self.logger.debug("Making request to URL: %s", url)

        for attempt in range(self.max_retries):
            try:
                # Wait for rate limit if needed
                self._wait_for_rate_limit()

                # Create and send request
                request = Request(url, headers=REQUEST_HEADERS)
                response = urlopen(request)

                # Read and process response
                response_data = response.read()

                # Check if response is gzip compressed
                if response.headers.get("content-encoding", "").lower() == "gzip":
                    try:
                        response_data = decompress_gzip(response_data)
                    except Exception as e:
                        self.logger.error("Failed to decompress response: %s", e)
                        raise TranslationError("Failed to decompress response: " + str(e))

                # Decode response data
                if isinstance(response_data, binary_type):
                    response_data = response_data.decode("utf-8", errors="ignore")

                self.logger.debug("Raw response: %s", response_data)

                translated = self._extract_translation(response_data)

                # A success clears every failure counter, including the circuit.
                self._reset_rate_limit_state()
                self._circuit_failures = 0
                self._circuit_open = False

                self.logger.debug("Extracted translation: %s", translated)
                return translated

            except HTTPError as e:
                self.logger.error("HTTP error occurred: %s", e)
                if e.code not in self.RETRYABLE_STATUS_CODES:
                    raise TranslationError("HTTP error occurred: " + str(e))
                # Honour Retry-After when the server sends one; it is the
                # only reliable signal for how long the window lasts.
                retry_after = self._parse_retry_after(e.headers.get("Retry-After") if e.headers else None)
                if self._record_failure(attempt):
                    break
                self._handle_rate_limit(retry_after)

            except URLError as e:
                self.logger.error("URL error occurred: %s", e)
                if self._record_failure(attempt):
                    break
                self._handle_rate_limit()

            except TranslationError:
                raise

            except Exception as e:
                self.logger.error("Translation error occurred: %s", e)
                raise TranslationError("Translation error occurred: " + str(e))

        if self._circuit_open:
            raise TranslationError(
                "Translation circuit open after %d consecutive failures; the "
                "translation backend is rate limiting requests." % self._circuit_failures
            )
        raise TranslationError(
            "Max retries exceeded after {0} attempts; the translation backend is "
            "rate limiting requests. Retry later, or reduce the request rate by "
            "translating fewer strings per run.".format(self.max_retries)
        )

    def _iter_chunks(self, texts):
        """Split strings into batches bounded by count and by characters.

        A string longer than ``max_batch_chars`` is sent on its own rather
        than dropped, so no input is ever skipped.

        Args:
            texts: Sequence of strings

        Yields:
            list: The next batch of strings
        """
        chunk = []
        chars = 0

        for text in texts:
            # Budget what actually goes on the wire: the escaped text
            # after URL encoding, plus the separator that joins it to
            # the next string. Counting raw characters understates CJK
            # badly - one Chinese character encodes to nine bytes - and
            # an oversized payload is answered with a 414 that is not
            # retryable and does not open the circuit.
            cost = len(quote_plus(self._escape_special_chars(text))) + 1
            if chunk and (len(chunk) >= self.batch_size or chars + cost > self.max_batch_chars):
                yield chunk
                chunk = []
                chars = 0
            chunk.append(text)
            chars += cost

        if chunk:
            yield chunk

    def translate_batch(self, texts, source_lang="auto", target_lang="en"):
        """Translate several strings using as few requests as possible.

        Strings are escaped individually and only then joined with a newline,
        because ``_escape_special_chars`` would otherwise swallow the
        separator and batching would silently never take effect.

        The endpoint splits results on sentences rather than on lines, so the
        payload is flattened and split back on the echoed newlines. When that
        does not reproduce the input count the batch falls back to one request
        per string, which keeps results aligned with the input.

        Args:
            texts: Sequence of strings to translate
            source_lang (str): Source language code (default: auto)
            target_lang (str): Target language code (default: en)

        Returns:
            list: One translated string per input, in the original order

        Raises:
            TranslationError: If a batch cannot be translated
        """
        results = []

        for chunk in self._iter_chunks([ensure_unicode(text) for text in texts]):
            cached = self.translation_memory.get_all(chunk, source_lang, target_lang)
            pending = [text for text, hit in zip(chunk, cached) if hit is None]

            # Nothing to ask the backend about: the whole chunk was remembered.
            if not pending:
                self.memory_hits += len(chunk)
                results.extend(cached)
                continue

            offline_fallback = False
            try:
                translated_pending = self._translate_batch_online(pending, source_lang, target_lang)
            except TranslationError:
                if not self.offline:
                    raise
                # Offline misses are expected: keep the source text so the
                # catalog stays complete and report the gap instead of dying.
                # _translate_batch_online already counted the failure.
                self.logger.debug("Offline with no remembered translation for %d string(s)", len(pending))
                translated_pending = list(pending)
                offline_fallback = True

            if offline_fallback:
                # The source text is a placeholder for a missing translation,
                # not a translation. Remembering it would make every later run
                # - online ones included - reuse it, so the string would never
                # be translated and failure_count would stay at zero. The gap
                # has to stay visible instead of being cached away.
                pass
            else:
                self.translation_memory.put_all(pending, source_lang, target_lang, translated_pending)
            self.memory_hits += len(chunk) - len(pending)

            # Re-merge in the original order, since only the misses were sent.
            merged = list(cached)
            iterator = iter(translated_pending)
            for index, hit in enumerate(merged):
                if hit is None:
                    merged[index] = next(iterator)
            results.extend(merged)

        self.translation_memory.save()
        return results

    def _translate_batch_online(self, texts, source_lang, target_lang):
        """Translate strings that were not in the translation memory."""
        results = []

        for chunk in self._iter_chunks([ensure_unicode(text) for text in texts]):
            # Escape first, join second: the separator must survive escaping.
            escaped = [self._escape_special_chars(text) for text in chunk]
            payload = "\n".join(escaped)

            try:
                translated = self._request_translation(payload, source_lang, target_lang)
            except Exception:
                self.failure_count += len(chunk)
                raise

            parts = translated.split("\n")
            if len(parts) != len(chunk):
                self.logger.debug(
                    "Batch of %d came back as %d parts; translating one by one",
                    len(chunk),
                    len(parts),
                )
                try:
                    parts = [self._request_translation(item, source_lang, target_lang) for item in escaped]
                except Exception:
                    self.failure_count += len(chunk)
                    raise

            for part in parts:
                part = self._unescape_html_entities(part)
                translated_text = self._unescape_special_chars(part)
                if not translated_text:
                    self.failure_count += 1
                results.append(translated_text)

        return results

    def translate(self, text, source_lang="auto", target_lang="en"):
        """Translate a single string using Google Translate.

        Args:
            text (str): Text to translate
            source_lang (str): Source language code (default: auto)
            target_lang (str): Target language code (default: en)

        Returns:
            str: Translated text

        Raises:
            TranslationError: If translation fails after all retries
            ValueError: If language codes are invalid
        """
        # Handle empty or invalid input
        if text is None:
            return text_type("")
        if not isinstance(text, string_types):
            text = text_type(str(text))
        if not text:
            return text_type("")

        # Handle None language codes
        source_lang = "auto" if source_lang is None else source_lang
        target_lang = "en" if target_lang is None else target_lang

        # Validate language codes
        if source_lang != "auto":
            source_lang = self.language_code_map.get(source_lang, source_lang)
            if not isinstance(source_lang, string_types) or len(source_lang.strip()) < 2:
                return text  # Return original text for invalid source language

        target_lang = self.language_code_map.get(target_lang, target_lang)
        if not isinstance(target_lang, string_types) or len(target_lang.strip()) < 2:
            return text  # Return original text for invalid target language

        try:
            return self.translate_batch([text], source_lang, target_lang)[0]
        except TranslationError:
            if not self.offline:
                raise
            # Offline misses are expected, not exceptional: keep the source
            # text so the catalog stays complete. translate_batch already
            self.logger.debug("Offline with no remembered translation for: %s", text)
            # counted the miss, so it is not counted again here.
            return text
