#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Translation provider profiles.

A profile captures everything that is specific to one translation backend, so
:class:`~transx.api.translate.GoogleTranslator` stays a single engine that
talks to whichever profile it was given instead of growing a branch per
provider.

Pointing ``TRANSX_TRANSLATE_ENDPOINT`` at a different host only ever replaced
the URL. Building the request, reading the response and splitting a batch all
stayed hardcoded to Google's conventions, so a self-hosted endpoint received
Google-shaped requests and answered with bodies nothing could parse. The five
dimensions below are what actually has to vary:

* request construction - method, URL, query/body and headers
* response parsing - where the translated text sits in the body
* batch strategy - one request per batch, or one per string
* escaping - Google's placeholder scheme is not universal
* engine identity - what ends up in every translation memory key

Adding a provider means subclassing :class:`TranslateProfile` and registering
it in :data:`PROFILES`.

Only the standard library is used here: this module has to import on Python
2.7, where ``pathlib``, ``typing`` and f-strings do not exist.
"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# Import built-in modules
import json
import logging
import os


try:
    # Import built-in modules
    from urllib import urlencode

    # Import third-party modules
    from urllib2 import quote as _quote
except ImportError:
    from urllib.parse import quote as _quote
    from urllib.parse import urlencode

# Import local modules
from transx.exceptions import TranslationError
from transx.internal.compat import ensure_unicode
from transx.internal.compat import text_type


def quote_plus(text):
    """Percent-encode a string for use in a URL query.

    Args:
        text: Text to encode

    Returns:
        str: Encoded text
    """
    if isinstance(text, text_type):
        text = text.encode("utf-8")
    return _quote(text, safe="")

LOGGER = logging.getLogger(__name__)

#: Environment variables understood by the profile layer.
PROFILE_ENV_VAR = "TRANSX_TRANSLATE_PROFILE"
ENDPOINT_ENV_VAR = "TRANSX_TRANSLATE_ENDPOINT"
API_KEY_ENV_VAR = "TRANSX_TRANSLATE_API_KEY"
MODEL_ENV_VAR = "TRANSX_TRANSLATE_MODEL"

#: Hosts that count as "this machine" for the offline loopback exemption.
LOOPBACK_HOSTS = frozenset(["localhost", "127.0.0.1", "::1", "[::1]", "0:0:0:0:0:0:0:1"])


def is_loopback_url(url):
    """Report whether ``url`` points at this machine.

    Offline mode exists so no string ever leaves the machine. A local service
    is already on the machine, so blocking it would make the offline path
    useless - that is the whole point of running a local bridge.

    Args:
        url: Absolute URL

    Returns:
        bool: True when the host is a loopback address
    """
    if not url:
        return False

    rest = ensure_unicode(url)
    separator = "://"
    if separator in rest:
        rest = rest.split(separator, 1)[1]
    # Drop credentials, host and anything after the host.
    for delimiter in ("/", "?", "#"):
        if delimiter in rest:
            rest = rest.split(delimiter, 1)[0]
    if "@" in rest:
        rest = rest.rsplit("@", 1)[1]

    # Strip an IPv6 bracket and a port number. Bracketed IPv6 keeps its
    # brackets here, because "::1" written bare cannot be told apart from a
    # host plus port.
    if rest.startswith("["):
        host = rest[1 : rest.index("]")] if "]" in rest else rest[1:]
    elif rest.count(":") > 1:
        # More than one colon means an unbracketed IPv6 address. "::1" is
        # ambiguous with "empty host, port 1", so try the whole thing first
        # and then drop the last colon group as if it were a port.
        host = rest
        if host.lower() in LOOPBACK_HOSTS:
            return True
        host = rest.rsplit(":", 1)[0]
    else:
        host = rest.split(":", 1)[0]

    return host.lower() in LOOPBACK_HOSTS


class TranslateProfile(object):
    """Everything that makes one translation backend different from another.

    Subclasses override the hooks that differ. The defaults describe a
    newline-joined GET endpoint with Google-shaped JSON, which is what the
    built-in Google profile builds on.
    """

    #: Name this profile is selected by.
    name = ""

    #: Default endpoint; an env var may override it.
    default_base_url = ""

    #: Environment variable that overrides ``base_url``.
    endpoint_env_var = ENDPOINT_ENV_VAR

    #: Identifier recorded in every translation memory key. Two profiles must
    #: never share one: a hit then silently mixes the two backends' output.
    engine_id = ""

    #: True when the backend accepts several strings per request.
    supports_batch = True

    #: Separator used to join a batch into one payload, if batching applies.
    batch_separator = "\n"

    #: HTTP method used for requests.
    method = "GET"

    #: Extra headers merged over the shared defaults. Instances get their own
    #: copy, so nothing can mutate another profile's headers.
    headers = None

    def __init__(self, base_url=None, api_key=None, model=None):
        """Initialize the profile.

        Args:
            base_url: Endpoint override; wins over the class default
            api_key: Optional credential, forwarded only when the profile
                sends it
            model: Backend model name, where the concept exists
        """
        self._base_url = base_url
        self.api_key = api_key
        self.model = model or getattr(self, "default_model", None)
        # Copied per instance: a profile is free to add headers or language
        # codes without touching the class every other instance reads from.
        self.headers = dict(self.headers or {})
        self.language_code_map = dict(self.language_code_map or {})

    # -- identity -----------------------------------------------------------

    @property
    def base_url(self):
        """Endpoint in use.

        Read from the environment on every access, so setting
        ``TRANSX_TRANSLATE_ENDPOINT`` after a translator was built still takes
        effect - which is how the override behaved before profiles existed.
        """
        if self._base_url:
            return self._base_url
        return os.environ.get(ENDPOINT_ENV_VAR) or self.default_base_url

    @base_url.setter
    def base_url(self, value):
        self._base_url = value

    def get_engine_id(self):
        """Return the identifier stored in translation memory keys.

        Returns:
            str: Engine identifier, unique per profile and configuration
        """
        return self.engine_id

    def map_language_code(self, code):
        """Convert a project language code to the backend's spelling.

        Args:
            code: Language code such as ``zh_CN``

        Returns:
            str: Code as the backend expects it
        """
        return self.language_code_map.get(code, code)

    #: Project language code to backend language code, as pairs so the class
    #: attribute stays immutable. Instances build a dict from it.
    language_code_map = ()

    # -- escaping -----------------------------------------------------------

    def escape(self, text):
        """Prepare one string for transport.

        Args:
            text: Source string

        Returns:
            str: Escaped string
        """
        return text

    def unescape(self, text):
        """Restore a string after transport.

        Args:
            text: Escaped string

        Returns:
            str: Restored string
        """
        return text

    # -- request ------------------------------------------------------------

    def join_batch(self, escaped_texts):
        """Combine escaped strings into one payload.

        Args:
            escaped_texts: Escaped strings, already run through ``escape``

        Returns:
            str: Payload to send
        """
        return self.batch_separator.join(escaped_texts)

    def build_request(self, payload, source_lang, target_lang, escaped_texts=None):
        """Describe the HTTP request for one batch.

        Args:
            payload: Joined payload, as returned by ``join_batch``
            source_lang: Source language code, backend spelling
            target_lang: Target language code, backend spelling
            escaped_texts: Individual escaped strings, for backends that send
                them as a list instead of a joined payload

        Returns:
            dict: Keys ``url``, ``data`` (may be None) and ``headers``
        """
        raise NotImplementedError

    def parse_response(self, response_data):
        """Extract the translated payload from a response body.

        Args:
            response_data: Decoded response body

        Returns:
            list: One translated string per input, or a single payload the
                caller still has to split
        """
        raise NotImplementedError

    def split_response(self, translated, expected_count):
        """Break a translated payload back into one string per input.

        Args:
            translated: Payload returned by ``parse_response``
            expected_count: Number of strings that were sent

        Returns:
            list: Translated strings, or ``None`` when the payload does not
                reproduce the input count and the caller must fall back to one
                request per string
        """
        if isinstance(translated, list):
            return translated if len(translated) == expected_count else None
        parts = ensure_unicode(translated).split(self.batch_separator)
        return parts if len(parts) == expected_count else None

    # -- budgeting ----------------------------------------------------------

    def measure(self, text):
        """Cost of ``text`` against ``max_batch_chars``.

        Args:
            text: Raw source string

        Returns:
            int: Number of characters the string costs on the wire
        """
        return len(quote_plus(self.escape(text))) + 1


class GoogleProfile(TranslateProfile):
    """The undocumented Google JSON endpoint already used by TransX.

    Kept as the default, and unchanged: the URL, the batch separator and the
    parsing all behave exactly as they did before profiles existed.
    """

    name = "google"
    default_base_url = "https://translate.googleapis.com/translate_a/single"
    engine_id = "google-gtx-v1"
    method = "GET"
    supports_batch = True
    batch_separator = "\n"

    language_code_map = (
        ("zh_CN", "zh-CN"),
        ("ja_JP", "ja"),
        ("ko_KR", "ko"),
        ("fr_FR", "fr"),
        ("es_ES", "es"),
    )

    #: Placeholders protecting characters that would otherwise be eaten by the
    #: endpoint or collide with the batch separator.
    _ESCAPES = (
        ("\n", "{{NEWLINE}}"),
        ("\r", "{{RETURN}}"),
        ("\t", "{{TAB}}"),
        ("\\", "{{BACKSLASH}}"),
        ('\\"', "{{QUOTE}}"),
        ("\b", "{{BACKSPACE}}"),
        ("\f", "{{FORMFEED}}"),
    )

    def escape(self, text):
        """Replace characters that must survive the round trip."""
        result = ensure_unicode(text)
        for char, placeholder in self._ESCAPES:
            result = result.replace(text_type(char), text_type(placeholder))
        return result

    def unescape(self, text):
        """Restore characters replaced by :meth:`escape`."""
        result = ensure_unicode(text)
        for char, placeholder in self._ESCAPES:
            result = result.replace(text_type(placeholder), text_type(char))
        return result

    def build_request(self, payload, source_lang, target_lang, escaped_texts=None):
        """Encode the payload as query parameters of a GET."""
        params = [
            ("client", "gtx"),
            ("sl", source_lang),
            ("tl", target_lang),
            ("dt", "t"),
            ("q", payload.encode("utf-8")),
        ]
        return {
            "url": self.base_url + "?" + urlencode(params),
            "data": None,
            "headers": {},
        }

    def parse_response(self, response_data):
        """Flatten the nested arrays the endpoint answers with."""
        try:
            data = json.loads(response_data)
        except ValueError as exc:
            raise TranslationError("Failed to parse translation response: %s" % exc)

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

        # Joined rather than returned as a list: the endpoint splits on
        # sentences, so the newlines it echoes back are what the caller splits
        # on to reproduce the input count.
        return "".join(parts)


class LibreTranslateProfile(TranslateProfile):
    """LibreTranslate, typically self-hosted.

    Speaks a documented JSON API and accepts a list of strings in one call, so
    no newline separator is needed and no sentence-splitting fallback applies.
    """

    name = "libretranslate"
    default_base_url = "http://localhost:5000/translate"
    engine_id = "libretranslate-v1"
    method = "POST"
    supports_batch = True

    language_code_map = (
        ("zh_CN", "zh"),
        ("zh_TW", "zh"),
        ("ja_JP", "ja"),
        ("ko_KR", "ko"),
        ("fr_FR", "fr"),
        ("es_ES", "es"),
        ("en_US", "en"),
        ("de_DE", "de"),
        ("it_IT", "it"),
        ("ru_RU", "ru"),
    )

    def build_request(self, payload, source_lang, target_lang, escaped_texts=None):
        """Send the strings as a JSON list, never newline-joined."""
        items = list(escaped_texts) if escaped_texts is not None else [payload]
        body = {
            "q": items,
            "source": source_lang,
            "target": target_lang,
            "format": "text",
        }
        # Only sent when the user set it: an empty api_key is rejected by some
        # deployments, so "unset" and "empty" must stay distinguishable.
        if self.api_key:
            body["api_key"] = self.api_key

        return {
            "url": self.base_url,
            "data": json.dumps(body).encode("utf-8"),
            "headers": {"Content-Type": "application/json"},
        }

    def parse_response(self, response_data):
        """Read the ``translatedText`` fields of the response object."""
        try:
            data = json.loads(response_data)
        except ValueError as exc:
            raise TranslationError("Failed to parse translation response: %s" % exc)

        if isinstance(data, dict):
            if "error" in data:
                raise TranslationError("Translation backend error: %s" % (data.get("error"),))
            translations = data.get("translatedText")
            # A single string is returned bare rather than in a list.
            if isinstance(translations, text_type):
                return [ensure_unicode(translations)]
            if not isinstance(translations, list):
                raise TranslationError("Could not find translation in response")
            return [ensure_unicode(item) for item in translations]

        if isinstance(data, list):
            # Older deployments answer with a bare list of strings.
            return [ensure_unicode(item) for item in data]

        raise TranslationError("Could not find translation in response")

    def split_response(self, translated, expected_count):
        """Require an exact count; the backend is list based, not text based."""
        if isinstance(translated, list):
            return translated if len(translated) == expected_count else None
        return None

    def measure(self, text):
        """Measure the raw string; a JSON body is not URL encoded."""
        return len(ensure_unicode(text)) + 1


class OllamaProfile(TranslateProfile):
    """A local Ollama model used as a translator.

    Ollama has no batch API and no JSON mode here, so the profile asks for one
    string per request and cleans up the prose a chat model tends to add. Its
    engine id carries the model name, because two models produce different
    translations and must not share memory entries.
    """

    name = "ollama"
    default_base_url = "http://localhost:11434/api/generate"
    engine_id = "ollama"
    default_model = "llama3.2"
    method = "POST"
    supports_batch = False

    language_code_map = (
        ("zh_CN", "Simplified Chinese"),
        ("zh_TW", "Traditional Chinese"),
        ("ja_JP", "Japanese"),
        ("ko_KR", "Korean"),
        ("fr_FR", "French"),
        ("es_ES", "Spanish"),
        ("en_US", "English"),
        ("de_DE", "German"),
        ("it_IT", "Italian"),
        ("ru_RU", "Russian"),
    )

    #: Instruction kept deliberately terse to keep the model from elaborating.
    INSTRUCTION = (
        "Translate the following text into {target}. "
        "Output only the translation. "
        "Do not explain, do not add notes, do not repeat the original."
    )

    #: Prefixes a chat model likes to put in front of its answer.
    _PREFIXES = (
        "translation:",
        "translated text:",
        "translated:",
        "here is the translation:",
        "here's the translation:",
        "output:",
        "result:",
    )

    def get_engine_id(self):
        """Include the model name so models never share memory entries."""
        model = self.model or self.default_model
        return "%s-%s" % (self.engine_id, model)

    def build_request(self, payload, source_lang, target_lang, escaped_texts=None):
        """Ask for a deterministic, unstreamed completion."""
        prompt = "%s\n\n%s" % (
            self.INSTRUCTION.format(target=self._language_name(target_lang)),
            payload,
        )
        body = {
            "model": self.model or self.default_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        }
        return {
            "url": self.base_url,
            "data": json.dumps(body).encode("utf-8"),
            "headers": {"Content-Type": "application/json"},
        }

    def _language_name(self, code):
        """Return a language name a model can understand."""
        return self.language_code_map.get(code, code)

    def parse_response(self, response_data):
        """Read the ``response`` field of an Ollama completion."""
        try:
            data = json.loads(response_data)
        except ValueError as exc:
            raise TranslationError("Failed to parse translation response: %s" % exc)

        if not isinstance(data, dict):
            raise TranslationError("Could not find translation in response")
        if data.get("error"):
            raise TranslationError("Translation backend error: %s" % (data.get("error"),))

        text = data.get("response")
        if text is None:
            raise TranslationError("Could not find translation in response")

        cleaned = self.clean_output(ensure_unicode(text))
        if not cleaned:
            # An empty answer is a refusal or a truncated completion, not an
            # empty translation: returning it would write a blank msgstr and
            # quietly lose the string.
            raise TranslationError("Translation backend returned an empty response")
        return [cleaned]

    def clean_output(self, text):
        """Strip the decoration a chat model wraps its answer in.

        Args:
            text: Raw model output

        Returns:
            str: The translation alone
        """
        result = ensure_unicode(text).strip()

        # A fenced block: keep only what is between the first and the last
        # fence, so prose the model appends after the closing fence is dropped
        # too - not just the fence lines themselves.
        if result.startswith("```"):
            lines = result.split("\n")
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            while lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            # Anything after a closing fence is commentary, not translation.
            kept = []
            for line in lines:
                if line.strip() == "```":
                    break
                kept.append(line)
            result = "\n".join(kept).strip()

        lowered = result.lower()
        for prefix in self._PREFIXES:
            if lowered.startswith(prefix):
                result = result[len(prefix) :].strip()
                lowered = result.lower()

        # A trailing note the model added after the translation.
        for marker in ("\n\n", "\n"):
            if marker in result:
                head, tail = result.split(marker, 1)
                if head.strip() and any(
                    tail.lower().lstrip("(").startswith(word)
                    for word in ("note", "here", "the above", "translation:", "let me")
                ):
                    result = head.strip()
                    break

        # Matching leading and trailing quotes add nothing but noise.
        if len(result) >= 2 and result[0] == result[-1] and result[0] in ("'", '"'):
            result = result[1:-1].strip()

        return result.strip()

    def split_response(self, translated, expected_count):
        """One request carries one string, so there is nothing to split."""
        if isinstance(translated, list) and len(translated) == expected_count:
            return translated
        return None

    def measure(self, text):
        """Measure the raw string; a JSON body is not URL encoded."""
        return len(ensure_unicode(text)) + 1


#: Profiles by selection name. Order matters only for error messages.
PROFILES = {
    GoogleProfile.name: GoogleProfile,
    LibreTranslateProfile.name: LibreTranslateProfile,
    OllamaProfile.name: OllamaProfile,
}

#: Sorted profile names, for error messages and ``--help`` text.
PROFILE_NAMES = sorted(PROFILES)

#: Endpoint path fragments that identify a profile when only a URL is given.
ENDPOINT_HINTS = (
    ("/api/generate", OllamaProfile.name),
    ("/translate_a/single", GoogleProfile.name),
    ("/translate", LibreTranslateProfile.name),
)


def infer_profile_name(endpoint):
    """Guess which profile an endpoint URL belongs to.

    Args:
        endpoint: Endpoint URL from the environment

    Returns:
        str: Profile name, or ``None`` when the URL matches nothing known
    """
    if not endpoint:
        return None

    lowered = ensure_unicode(endpoint).lower()
    for fragment, name in ENDPOINT_HINTS:
        if fragment in lowered:
            return name
    return None


def resolve_profile_name(explicit=None, endpoint=None):
    """Work out which profile to use.

    An explicit choice always wins, so a custom URL under a known profile is
    never silently reinterpreted. Otherwise the endpoint path is matched
    against :data:`ENDPOINT_HINTS`, and an unrecognised combination falls back
    to Google rather than failing - that is what any endpoint override did
    before profiles existed.

    Args:
        explicit: Profile name given by the caller or ``TRANSX_TRANSLATE_PROFILE``
        endpoint: Endpoint URL in use

    Returns:
        str: Profile name
    """
    if explicit:
        return explicit
    return infer_profile_name(endpoint) or GoogleProfile.name


def create_profile(name, base_url=None, api_key=None, model=None):
    """Instantiate a profile by name.

    Args:
        name: Profile name
        base_url: Endpoint override
        api_key: Optional credential
        model: Optional model name

    Returns:
        TranslateProfile: The profile instance

    Raises:
        TranslationError: If ``name`` is not a known profile
    """
    profile_class = PROFILES.get(name)
    if profile_class is None:
        raise TranslationError(
            "Unknown translation profile: {0}. Valid profiles are: {1}.".format(
                name, ", ".join(PROFILE_NAMES)
            )
        )
    return profile_class(base_url=base_url, api_key=api_key, model=model)
