#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Translation functions for TransX."""
# Import future modules
# fmt: off
# isort: skip
from __future__ import unicode_literals

# Import built-in modules
import abc
import logging
import os
import time


try:
    # Import built-in modules
    from urllib import urlencode

    # Import third-party modules
    from urllib2 import HTTPError
    from urllib2 import Request
    from urllib2 import URLError
    from urllib2 import urlopen
except ImportError:
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode

# Import local modules
from transx.api.locale import normalize_language_code
from transx.api.po import POFile
from transx.exceptions import TranslationError
from transx.internal.compat import PY2
from transx.internal.compat import binary_type
from transx.internal.compat import decompress_gzip
from transx.internal.compat import ensure_unicode
from transx.internal.compat import string_types
from transx.internal.compat import text_type


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
    po.metadata.update({
        "Language": lang,
        "Language-Team": "%s <LL@li.org>" % lang,
        "Plural-Forms": "nplurals=1; plural=0;" if lang.startswith("zh") else "nplurals=2; plural=(n != 1);"
    })

    # Optionally translate untranslated entries
    if translator:
        logger.info("Auto-translating untranslated strings for %s..." % lang)
        po.translate_messages(translator, target_lang=lang)

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
    """Google Translate API implementation based on deep-translator."""

    BASE_URL = "https://translate.google.com/m"

    def __init__(self, max_retries=5, initial_delay=1, max_delay=3600):
        """Initialize the translator.

        Args:
            max_retries (int): Maximum number of retry attempts
            initial_delay (int): Initial delay in seconds between retries
            max_delay (int): Maximum delay in seconds between retries
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self._last_request_time = 0
        self._min_request_interval = 0.5  # Minimum time between requests
        self._consecutive_failures = 0
        self._current_delay = initial_delay
        self.logger = logging.getLogger(__name__)

        # Map standard language codes to Google Translate supported codes
        self.language_code_map = {
            "zh_CN": "zh-CN",
            "ja_JP": "ja",
            "ko_KR": "ko",
            "fr_FR": "fr",
            "es_ES": "es"
        }

    def _wait_for_rate_limit(self):
        """Ensure minimum time between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()

    def _handle_rate_limit(self):
        """Handle rate limit with exponential backoff."""
        self._consecutive_failures += 1
        delay = min(self._current_delay * (2 ** self._consecutive_failures), self.max_delay)
        self.logger.warning("Rate limit hit. Waiting %s seconds before retry", delay)
        time.sleep(delay)

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
            text_type("\f"): text_type("{{FORMFEED}}")
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
            text_type("{{FORMFEED}}"): text_type("\f")
        }
        result = text
        for placeholder, char in replacements.items():
            result = result.replace(placeholder, char)
        return result

    def translate(self, text, source_lang="auto", target_lang="en"):
        """Translate text using Google Translate API.

        Args:
            text (str): Text to translate
            source_lang (str): Source language code (default: auto)
            target_lang (str): Target language code (default: en)

        Returns:
            str: Translated text

        Raises:
            TranslationError: If translation fails after all retries
        """
        # Handle empty or invalid input
        if not text or not isinstance(text, string_types):
            return text

        # Escape special characters
        escaped_text = self._escape_special_chars(text)

        # Convert language codes
        target_lang = self.language_code_map.get(target_lang, target_lang)
        if source_lang != "auto":
            source_lang = self.language_code_map.get(source_lang, source_lang)

        # Build request parameters
        params = {
            "sl": source_lang,
            "tl": target_lang,
            "q": escaped_text.encode("utf-8") if isinstance(escaped_text, text_type) else escaped_text,
        }

        # Ensure all parameters are str type
        encoded_params = {}
        for key, value in params.items():
            if isinstance(value, text_type):
                encoded_params[key] = value.encode("utf-8")
            else:
                encoded_params[key] = value

        url = self.BASE_URL + "?" + urlencode(encoded_params)

        self.logger.debug("Making request to URL: %s", url)
        self.logger.debug("Request params: %s", params)

        # Set request headers to mimic a mobile browser
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Mobile Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "*",
            "Connection": "keep-alive"
        }

        for _attempt in range(self.max_retries):
            try:
                # Wait for rate limit if needed
                self._wait_for_rate_limit()

                # Create and send request
                request = Request(url, headers=headers)
                response = urlopen(request)

                # Reset rate limit state after successful request
                self._reset_rate_limit_state()

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

                # Extract translation from response
                try:
                    # Try different possible result container patterns
                    patterns = [
                        ('class="result-container">', "</div>"),
                        ('class="translation">', "</div>"),
                        ('class="t0">', "</div>"),
                        ("<div dir='ltr'>", "</div>"),
                    ]

                    translated_text = None
                    for start_pattern, end_pattern in patterns:
                        start = response_data.find(start_pattern)
                        if start != -1:
                            start += len(start_pattern)
                            end = response_data.find(end_pattern, start)
                            if end != -1:
                                translated_text = response_data[start:end].strip()
                                break

                    if translated_text is None:
                        raise TranslationError("Could not find translation in response")

                    self.logger.debug("Extracted translation: %s", translated_text)

                    # Restore special characters
                    return self._unescape_special_chars(translated_text)

                except Exception as e:
                    self.logger.error("Failed to extract translation: %s", e)
                    raise TranslationError("Failed to extract translation: " + str(e))

            except HTTPError as e:
                self.logger.error("HTTP error occurred: %s", e)
                if e.code == 429:  # Too Many Requests
                    self._handle_rate_limit()
                    continue
                raise TranslationError("HTTP error occurred: " + str(e))

            except URLError as e:
                self.logger.error("URL error occurred: %s", e)
                self._handle_rate_limit()
                continue

            except Exception as e:
                self.logger.error("Translation error occurred: %s", e)
                raise TranslationError("Translation error occurred: " + str(e))

        raise TranslationError("Max retries exceeded")
