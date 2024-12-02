#!/usr/bin/env python
"""Python 2/3 compatibility module."""
from __future__ import unicode_literals

import sys

from transx.constants import DEFAULT_CHARSET

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2

if PY2:
    text_type = unicode
    binary_type = str
else:
    text_type = str
    binary_type = bytes


def ensure_unicode(text):
    """Ensure text is unicode.
    
    Args:
        text: Text to convert
        
    Returns:
        Unicode string
    """
    if isinstance(text, binary_type):
        return text.decode(DEFAULT_CHARSET)
    return text


def ensure_binary(text):
    """Ensure text is binary.
    
    Args:
        text: Text to convert
        
    Returns:
        Binary string
    """
    if isinstance(text, text_type):
        return text.encode(DEFAULT_CHARSET)
    return text


def is_string(text):
    """Check if text is a string (unicode or bytes).
    
    Args:
        text: Text to check
        
    Returns:
        bool: True if text is a string
    """
    return isinstance(text, (text_type, binary_type))
