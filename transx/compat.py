#!/usr/bin/env python
"""Python 2/3 compatibility module."""
from __future__ import unicode_literals

import abc
import gzip
import sys
import tokenize
from io import BytesIO

try:
    from urllib import urlencode # noqa
    from urllib2 import Request, urlopen, HTTPError, URLError # noqa
    from StringIO import StringIO as BytesIO # noqa
except ImportError:
    from urllib.parse import urlencode  # noqa
    from urllib.request import Request, urlopen # noqa
    from urllib.error import HTTPError, URLError # noqa
    from io import BytesIO

from transx.constants import DEFAULT_CHARSET

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2

if PY2:
    text_type = unicode
    binary_type = str
    ABC = abc.ABCMeta(str("ABC"), (object,), {"__slots__": ()})
    string_types = (str, unicode)
    abstractmethod = abc.abstractmethod
    
    def tokenize_source(content):
        """Tokenize source code content."""
        return list(tokenize.generate_tokens(BytesIO(content.encode("utf-8")).readline))
else:
    text_type = str
    binary_type = bytes
    ABC = abc.ABCMeta("ABC", (object,), {"__slots__": ()})
    string_types = (str,)
    abstractmethod = abc.abstractmethod
    
    def tokenize_source(content):
        """Tokenize source code content."""
        return list(tokenize.tokenize(BytesIO(content.encode("utf-8")).readline))


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
    return isinstance(text, string_types)


def safe_eval_string(token_string):
    """Safely evaluate a string token.
    
    Args:
        token_string: String token to evaluate
        
    Returns:
        Evaluated string or None if evaluation fails
    """
    try:
        import ast
        result = ast.literal_eval(token_string)
        if isinstance(result, string_types):
            return ensure_unicode(result)
    except (ValueError, SyntaxError):
        pass
    return None


def decompress_gzip(data):
    """Decompress gzip data.
    
    Args:
        data: Compressed data
        
    Returns:
        Decompressed data
    """
    gzip_data = BytesIO(data)
    with gzip.GzipFile(fileobj=gzip_data, mode="rb") as f:
        return f.read()
