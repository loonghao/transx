#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Persistent translation memory.

A translation memory (TM) remembers what an engine already translated so the
same string is never sent to the network twice. That is what actually removes
the 429s: the in-process caches in :mod:`transx.core` die with the process, so
every CI run and every local run re-translated the whole catalog from scratch.
A TM that survives the process turns repeat runs into zero-request runs.

The file is plain JSON, versioned, sorted and written atomically so it can be
committed to a repository and reviewed in a diff without churn.
"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# Import built-in modules
import contextlib
import errno
import hashlib
import io
import json
import logging
import os
import tempfile

# Import local modules
from transx.internal.compat import ensure_unicode
from transx.internal.compat import text_type


LOGGER = logging.getLogger(__name__)

#: Current on-disk format. Unknown versions are treated as corrupt.
TM_VERSION = 1

#: Directory and file name used inside a locale root.
TM_DIR_NAME = ".transx"
TM_FILE_NAME = "tm.json"

#: Environment variables recognised by :func:`resolve_tm_path`.
TM_PATH_ENV_VAR = "TRANSX_TM_PATH"
OFFLINE_ENV_VAR = "TRANSX_OFFLINE"


def _truthy(value):
    """Return True when an environment-style value means "on".

    Args:
        value: Raw value, usually from ``os.environ``

    Returns:
        bool: True for 1/true/yes/on, case insensitive
    """
    if value is None:
        return False
    return ensure_unicode(value).strip().lower() in ("1", "true", "yes", "on")


def offline_enabled(override=None):
    """Report whether network access is disabled.

    Args:
        override: Explicit flag; wins over the environment when not None

    Returns:
        bool: True when no request may be sent
    """
    if override is not None:
        return bool(override)
    return _truthy(os.environ.get(OFFLINE_ENV_VAR))


def make_key(source_text, source_lang, target_lang, engine_id):
    """Build the TM lookup key for one string.

    The engine is part of the key: two engines produce different translations,
    and reusing one engine's output under another's identity would silently
    mix quality levels and dialects.

    Args:
        source_text (str): Text that was translated
        source_lang (str): Source language code, or ``auto``
        target_lang (str): Target language code
        engine_id (str): Identifier of the engine that produced the text

    Returns:
        str: Hex digest identifying this exact translation request
    """
    parts = [
        ensure_unicode(source_text),
        ensure_unicode(source_lang or "auto"),
        ensure_unicode(target_lang or ""),
        ensure_unicode(engine_id or ""),
    ]
    # A delimiter that cannot occur inside a single part keeps the hashed
    # input unambiguous, so no combination of fields can collide with another.
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def resolve_tm_path(locale_root=None, explicit_path=None):
    """Work out where the TM file should live.

    Precedence is explicit path, then ``TRANSX_TM_PATH``, then
    ``<locale_root>/.transx/tm.json``, then the user level
    ``~/.transx/tm.json``. The first two are honoured verbatim; the fallbacks
    keep working when no repository root is available, for example under a
    bare ``transx translate`` invoked from an arbitrary directory.

    Args:
        locale_root: Directory holding the ``<locale>/LC_MESSAGES`` tree
        explicit_path: Path forced by the caller

    Returns:
        str: Path to the TM file
    """
    if explicit_path:
        return explicit_path

    from_env = os.environ.get(TM_PATH_ENV_VAR)
    if from_env:
        return from_env

    if locale_root:
        return os.path.join(locale_root, TM_DIR_NAME, TM_FILE_NAME)

    return os.path.join(os.path.expanduser("~"), ".transx", TM_FILE_NAME)


def _ensure_parent_dir(path):
    """Create the directory holding ``path`` if it is missing.

    Args:
        path: File whose parent directory should exist
    """
    parent = os.path.dirname(path)
    if not parent or os.path.isdir(parent):
        return
    try:
        os.makedirs(parent)
    except OSError as exc:
        # Another process may have created it between the check and the call.
        if exc.errno != errno.EEXIST:
            raise


def _atomic_write(path, text):
    """Write text to ``path`` without ever leaving a half written file.

    The content is written to a temporary file in the same directory and then
    renamed into place. ``os.replace`` does not exist on Python 2.7, and on
    Windows ``os.rename`` refuses to overwrite, so the target is removed
    first when it is already there.

    Args:
        path: Destination file
        text (str): Content to write
    """
    _ensure_parent_dir(path)
    directory = os.path.dirname(path) or "."

    handle, temp_path = tempfile.mkstemp(prefix=".tm-", suffix=".tmp", dir=directory)
    try:
        # mkstemp returns a low level handle, so close it before reopening
        # with the encoding-aware wrapper.
        os.close(handle)
        with io.open(temp_path, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())

        if os.path.exists(path):
            os.remove(path)
        os.rename(temp_path, path)
    except Exception:
        if os.path.exists(temp_path):
            with contextlib.suppress(OSError):
                os.remove(temp_path)
        raise


class TranslationMemory(object):
    """Persistent, JSON backed cache of already translated strings."""

    #: Environment variable that overrides the resolved path.
    PATH_ENV_VAR = "TRANSX_TM_PATH"

    """A persistent, JSON backed cache of already translated strings.

    Misses are reported, never raised: a broken or unreadable memory must
    degrade to "no entries" and let the caller fall back to the network or to
    the source text, rather than break a localisation run.
    """

    def __init__(self, path=None, engine_id="", enabled=True, locale_root=None):
        """Initialize the translation memory.

        Args:
            path: Explicit file path; overrides the resolved location
            engine_id (str): Identifier of the engine whose entries this is
            enabled (bool): When False the memory neither reads nor writes
            locale_root: Directory used to resolve a default path
        """
        self.enabled = enabled
        self.engine_id = engine_id or ""
        self.path = resolve_tm_path(locale_root=locale_root, explicit_path=path)
        self.logger = logging.getLogger(__name__)

        self._entries = {}
        self._loaded = False
        self._dirty = False

        #: Number of lookups served from the memory so far.
        self.hits = 0
        #: Number of lookups the memory could not serve.
        self.misses = 0
        #: True when the file on disk was unusable and had to be ignored.
        self.recovered_from_error = False

    # -- lifecycle ---------------------------------------------------------

    def load(self):
        """Read the memory from disk.

        A missing file yields an empty memory. A file that cannot be parsed,
        or that holds an unknown version, is backed up next to itself and
        treated as empty so a localisation run never dies on bad cache state.

        Returns:
            TranslationMemory: self, for chaining
        """
        self._loaded = True

        if not self.enabled or not self.path or not os.path.isfile(self.path):
            return self

        try:
            with io.open(self.path, "r", encoding="utf-8") as stream:
                data = json.load(stream)
        except (ValueError, IOError, OSError) as exc:
            self._quarantine(exc)
            return self

        if not isinstance(data, dict):
            self._quarantine(ValueError("translation memory root is not an object"))
            return self

        version = data.get("version")
        if version != TM_VERSION:
            self._quarantine(ValueError("unsupported translation memory version: %r" % (version,)))
            return self

        entries = data.get("entries")
        if not isinstance(entries, dict):
            self._quarantine(ValueError("translation memory entries are not an object"))
            return self

        # Only keep entries shaped the way we write them; a hand edited or
        # partially written file must not be able to crash a later lookup.
        for key, value in entries.items():
            if isinstance(value, dict) and isinstance(value.get("msgstr"), text_type):
                self._entries[key] = value

        return self

    def _quarantine(self, error):
        """Back up an unusable TM file and continue with an empty memory.

        Args:
            error: The reason the file was rejected
        """
        self._entries = {}
        self.recovered_from_error = True
        self.logger.warning(
            "Ignoring unusable translation memory %s (%s)",
            self.path,
            error,
        )

        backup = self.path + ".corrupt"
        try:
            if os.path.exists(self.path):
                if os.path.exists(backup):
                    os.remove(backup)
                os.rename(self.path, backup)
        except OSError as exc:
            self.logger.debug("Could not back up translation memory: %s", exc)

    def save(self):
        """Write the memory back to disk if it changed.

        Returns:
            bool: True when the file was written
        """
        if not self.enabled or not self.path or not self._dirty:
            return False

        payload = {
            "version": TM_VERSION,
            "entries": self._entries,
        }
        # sort_keys keeps the committed file stable, so the same translations
        # always produce byte-identical output and never churn the diff.
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)

        try:
            _atomic_write(self.path, text)
        except (IOError, OSError) as exc:
            self.logger.warning("Could not save translation memory %s: %s", self.path, exc)
            return False

        self._dirty = False
        return True

    def __enter__(self):
        """Load on entry.

        Returns:
            TranslationMemory: self
        """
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Persist on exit."""
        self.save()
        return False

    # -- lookups -----------------------------------------------------------

    def get(self, source_text, source_lang, target_lang):
        """Look up one translation.

        Args:
            source_text (str): Text to translate
            source_lang (str): Source language code, or ``auto``
            target_lang (str): Target language code

        Returns:
            str: The remembered translation, or None on a miss
        """
        if not self.enabled:
            return None

        if not self._loaded:
            self.load()

        key = make_key(source_text, source_lang, target_lang, self.engine_id)
        entry = self._entries.get(key)
        if entry is None:
            self.misses += 1
            return None

        self.hits += 1
        return entry.get("msgstr")

    def put(self, source_text, source_lang, target_lang, translated_text):
        """Remember one translation.

        Empty translations are not stored, so a failed translation never
        poisons the memory with a value that would suppress a later retry.

        Args:
            source_text (str): Text that was translated
            source_lang (str): Source language code, or ``auto``
            target_lang (str): Target language code
            translated_text (str): Result to remember

        Returns:
            bool: True when the memory changed
        """
        if not self.enabled or not translated_text or not translated_text.strip():
            return False

        if not self._loaded:
            self.load()

        key = make_key(source_text, source_lang, target_lang, self.engine_id)
        existing = self._entries.get(key)
        if existing is not None and existing.get("msgstr") == translated_text:
            return False

        self._entries[key] = {
            "msgstr": ensure_unicode(translated_text),
            # Kept for human review; the key alone cannot be read back.
            "src": ensure_unicode(source_text),
            "src_lang": ensure_unicode(source_lang or "auto"),
            "tgt_lang": ensure_unicode(target_lang or ""),
            "engine": self.engine_id,
        }
        self._dirty = True
        return True

    def get_all(self, items, source_lang, target_lang):
        """Look up several translations at once.

        Args:
            items: Sequence of source strings
            source_lang (str): Source language code, or ``auto``
            target_lang (str): Target language code

        Returns:
            list: Translation or None per input, in the original order
        """
        return [self.get(text, source_lang, target_lang) for text in items]

    def put_all(self, items, source_lang, target_lang, translations):
        """Remember several translations at once.

        Args:
            items: Sequence of source strings
            source_lang (str): Source language code, or ``auto``
            target_lang (str): Target language code
            translations: Sequence of results, aligned with ``items``
        """
        for text, translated in zip(items, translations):
            self.put(text, source_lang, target_lang, translated)

    # -- introspection ----------------------------------------------------

    def __len__(self):
        """Return the number of remembered entries.

        Returns:
            int: Entry count
        """
        return len(self._entries)

    def clear(self):
        """Forget every entry and mark the memory dirty."""
        self._entries = {}
        self._dirty = True
