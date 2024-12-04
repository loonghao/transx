"""File system utilities for TransX.

This module provides file system utilities with proper encoding handling
and Python 2/3 compatibility.
"""
# fmt: off
# isort: skip_file
# ruff: noqa: I001
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# Import built-in modules
# fmt: on
import codecs
import os

# Import local modules
from transx.constants import DEFAULT_ENCODING


def read_file(file_path, encoding=DEFAULT_ENCODING, binary=False):
    """Read file content with proper encoding handling.

    Args:
        file_path: Path to the file
        encoding: File encoding (default: utf-8)
        binary: If True, read file in binary mode (default: False)

    Returns:
        str or bytes: File content
    """
    if binary:
        with open(file_path, "rb") as f:
            return f.read()
    else:
        with codecs.open(file_path, "r", encoding=encoding) as f:
            return f.read()


def write_file(file_path, content, encoding=DEFAULT_ENCODING):
    """Write content to file with proper encoding handling.

    Args:
        file_path: Path to the file
        content: Content to write
        encoding: File encoding (default: utf-8)
    """
    # Create directory if it doesn't exist
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    with codecs.open(file_path, "w", encoding=encoding) as f:
        f.write(content)


def write_binary_file(file_path, content):
    """Write binary content to file.

    Args:
        file_path: Path to the file
        content: Binary content to write
    """
    # Create directory if it doesn't exist
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    with open(file_path, "wb") as f:
        f.write(content)


def normalize_path(path):
    """Normalize a file path for writing to PO/POT file.

    Args:
        path: The file path to normalize

    Returns:
        str: The normalized path
    """
    if not path:
        return path

    # Convert to absolute path if not already
    if not os.path.isabs(path):
        path = os.path.abspath(path)

    # Convert backslashes to forward slashes
    path = path.replace("\\", "/")

    # Try to make path relative to current directory
    try:
        rel_path = os.path.relpath(path)
        if not rel_path.startswith(".."):
            return rel_path.replace("\\", "/")
    except ValueError:
        pass

    return path


def ensure_dir(path):
    """Ensure directory exists, create it if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
