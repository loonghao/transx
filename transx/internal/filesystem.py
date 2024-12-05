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
import fnmatch
from transx.internal.compat import PY2
from transx.internal.compat import text_type

if PY2:
    FileNotFoundError = IOError


def read_file(file_path, encoding="utf-8", binary=False):
    """Read file content with proper encoding handling.

    Args:
        file_path: Path to the file
        encoding: File encoding (default: 'utf-8')
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


def write_file(file_path, content, encoding="utf-8"):
    """Write content to file with proper encoding handling.

    Args:
        file_path: Path to the file
        content: Content to write
        encoding: File encoding (default: 'utf-8')
    """
    # Create directory if it doesn't exist
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError:
            if not os.path.isdir(directory):
                raise

    # In Python 2, ensure content is unicode before writing
    if not isinstance(content, text_type):
        content = content.decode("utf-8")

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


def get_gitignore_patterns(root_dir):
    """Get patterns from .gitignore file.

    Args:
        root_dir (str): Project root directory

    Returns:
        set: Set of gitignore patterns
    """
    patterns = set()
    gitignore_path = os.path.join(root_dir, ".gitignore")

    if os.path.isfile(gitignore_path):
        with open(gitignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Normalize path separators
                    line = line.replace("\\", "/")
                    patterns.add(line)

    return patterns


def is_ignored(path, root_dir, ignore_patterns):
    """Check if a path should be ignored based on gitignore patterns.

    Args:
        path (str): Path to check
        root_dir (str): Project root directory
        ignore_patterns (set): Set of gitignore patterns

    Returns:
        bool: True if path should be ignored, False otherwise
    """
    # Convert absolute path to relative path from root_dir
    rel_path = os.path.relpath(path, root_dir)
    # Normalize path separators
    rel_path = rel_path.replace(os.path.sep, "/")

    # Check each pattern
    for pattern in ignore_patterns:
        # Handle directory-specific patterns
        if pattern.endswith("/"):
            pattern = pattern[:-1]
            # Check if any part of the path matches the pattern
            path_parts = rel_path.split("/")
            for i in range(len(path_parts)):
                subpath = path_parts[i]
                if fnmatch.fnmatch(subpath, pattern):
                    return True
        # Handle file patterns
        else:
            # Check if the file matches the pattern
            if fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                return True
            # Check if any parent directory matches the pattern
            path_parts = rel_path.split("/")
            for i in range(len(path_parts)):
                subpath = path_parts[i]
                if fnmatch.fnmatch(subpath, pattern):
                    return True

    return False


def should_ignore(path, root_dir=None):
    """Check if a path should be ignored based on .gitignore rules.

    Args:
        path (str): Path to check
        root_dir (str, optional): Project root directory. If None, use path's directory

    Returns:
        bool: True if path should be ignored, False otherwise
    """
    if root_dir is None:
        if os.path.isfile(path):
            root_dir = os.path.dirname(path)
        else:
            root_dir = path

    # Find the nearest .gitignore by walking up the directory tree
    current_dir = root_dir
    while current_dir:
        gitignore_path = os.path.join(current_dir, ".gitignore")
        if os.path.isfile(gitignore_path):
            ignore_patterns = get_gitignore_patterns(current_dir)
            return is_ignored(path, current_dir, ignore_patterns)
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir

    return False


def walk_with_gitignore(root_dir, file_patterns=None):
    """Walk directory tree respecting .gitignore.

    Args:
        root_dir (str): Root directory to start walking from
        file_patterns (list, optional): List of file patterns to match (e.g. ['*.py'])

    Returns:
        list: List of file paths that match patterns and are not ignored
    """
    matched_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip .git directory
        if ".git" in dirnames:
            dirnames.remove(".git")

        # Remove ignored directories
        i = len(dirnames) - 1
        while i >= 0:
            dirpath_full = os.path.join(dirpath, dirnames[i])
            if should_ignore(dirpath_full):
                del dirnames[i]
            i -= 1

        # Process files
        for filename in filenames:
            # Skip .gitignore file itself
            if filename == ".gitignore":
                continue

            filepath = os.path.join(dirpath, filename)

            # Skip ignored files
            if should_ignore(filepath):
                continue

            # If patterns specified, only include matching files
            if file_patterns:
                for pattern in file_patterns:
                    if fnmatch.fnmatch(filename, pattern):
                        matched_files.append(filepath)
                        break
            else:
                matched_files.append(filepath)

    return matched_files
