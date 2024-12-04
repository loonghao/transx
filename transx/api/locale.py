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


def normalize_language_code(lang_code):
    """Normalize language code to standard format.

    Args:
        lang_code (str): Language code in various formats
            Examples: 'zh-CN', 'zh_CN', 'zh-Hans', 'zh', 'Chinese'

    Returns:
        str: Normalized language code in format like 'zh_CN'
    """
    if not lang_code:
        return None

    # Convert to lowercase and replace hyphens
    lang_code = lang_code.lower().replace("-", "_")

    # Check if it's in LANGUAGE_CODES
    for code, (_, aliases) in LANGUAGE_CODES.items():
        if lang_code in [a.lower() for a in aliases]:
            return code

    # Check common language mappings
    if lang_code in LANGUAGE_MAP:
        return LANGUAGE_MAP[lang_code]

    # Handle codes like 'zh', 'ja', 'ko'
    if len(lang_code) == 2 and lang_code in DEFAULT_COUNTRY_MAP:
        return "{0}_{1}".format(lang_code, DEFAULT_COUNTRY_MAP[lang_code])

    # If already in correct format (e.g. zh_CN), return as is
    if len(lang_code.split("_")) == 2:
        return lang_code

    return None


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
