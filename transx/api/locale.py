#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Locale utilities for TransX."""

# Import future modules
from __future__ import unicode_literals

# Import built-in modules
import locale
import sys

# Import local modules
from transx.constants import DEFAULT_COUNTRY_MAP
from transx.constants import LANGUAGE_CODES
from transx.constants import LANGUAGE_MAP


#: Lowercased alias -> canonical code, built once instead of rebuilding the
#: ``[code] + aliases`` list on every call.
_LOWER_ALIASES = {}
for _code, (_name, _aliases) in LANGUAGE_CODES.items():
    for _alias in [_code] + list(_aliases):
        _LOWER_ALIASES.setdefault(_alias.lower(), _code)
_LOWER_CODES = {code.lower(): code for code in LANGUAGE_CODES}


def _normalize_language_code_uncached(lang_code):
    """Normalize a language code without consulting the cache."""
    # Replace hyphens with underscores
    normalized = lang_code.replace("-", "_")

    # First try exact match in LANGUAGE_CODES
    if normalized in LANGUAGE_CODES:
        return normalized

    # Then try exact match in aliases
    for code, (_, aliases) in LANGUAGE_CODES.items():
        if normalized in aliases:
            return code

    # Try case-insensitive match
    normalized_lower = normalized.lower()
    code = _LOWER_CODES.get(normalized_lower) or _LOWER_ALIASES.get(normalized_lower)
    if code:
        return code

    # Check common language mappings
    if normalized_lower in LANGUAGE_MAP:
        return LANGUAGE_MAP[normalized_lower]

    # Handle simple language codes (e.g., 'en' -> 'en_US')
    if "_" not in normalized_lower and normalized_lower in DEFAULT_COUNTRY_MAP:
            return "{0}_{1}".format(normalized_lower, DEFAULT_COUNTRY_MAP[normalized_lower])

    return None


#: Memoized results, keyed by the raw input. Locale codes are a small closed
#: set, but normalization walks every entry of ``LANGUAGE_CODES`` and is on the
#: path of ``switch_locale`` and of every ``Context`` locale assignment.
_NORMALIZED_CACHE = {}


def normalize_language_code(lang_code):
    """Normalize a language code to a standard format.

    Args:
        lang_code: Language code to normalize (e.g., 'en', 'zh-CN', 'zh_cn')

    Returns:
        str: Normalized language code (e.g., 'en_US', 'zh_CN', 'ja_JP')
            or None if the code is not recognized
    """
    if not lang_code:
        return None

    try:
        cached = _NORMALIZED_CACHE.get(lang_code)
    except TypeError:  # unhashable input
        return _normalize_language_code_uncached(lang_code)

    if cached is None:
        cached = _normalize_language_code_uncached(lang_code)
        _NORMALIZED_CACHE[lang_code] = cached
    return cached


def get_system_locale():
    """Get system locale and normalize it.

    Returns:
        str: Normalized system locale (e.g. 'zh_CN', 'en_US')
    """
    try:
        if sys.platform == "win32":
            # Import built-in modules
            import ctypes
            windll = ctypes.windll.kernel32
            # Get system default locale identifier
            lcid = windll.GetUserDefaultUILanguage()
            # Convert LCID to locale name
            buf_size = 85
            buf = ctypes.create_unicode_buffer(buf_size)
            windll.LCIDToLocaleName(lcid, buf, buf_size, 0)
            sys_locale = buf.value
        else:
            # For Unix-like systems
            sys_locale = locale.getdefaultlocale()[0]

        if not sys_locale:
            return None

        # Some systems return locale with encoding (e.g. 'zh_CN.UTF-8')
        sys_locale = sys_locale.split(".")[0]

        return normalize_language_code(sys_locale)

    except Exception:
        return None
