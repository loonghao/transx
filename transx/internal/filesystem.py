#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""File system utilities for TransX.

This module provides file system utilities with proper encoding handling
and Python 2/3 compatibility.
"""
# fmt: off
# isort: skip_file
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
from transx.internal.compat import string_types
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

    # Accept os.PathLike objects (pathlib.Path and friends) the same way the
    # os.path functions below do; os.fspath() is not available on Python 2.
    if not isinstance(path, string_types):
        path = text_type(path)

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


def _load_gitignore_patterns(root_dir):
    """Read one .gitignore file, keeping the patterns in file order.

    Order is part of the semantics: gitignore rules are "last match wins",
    which is what lets ``!pattern`` re-include a path an earlier rule ignored.

    Args:
        root_dir (str): Directory that may hold a .gitignore file

    Returns:
        tuple: Ordered patterns, or an empty tuple when there is no .gitignore
    """
    gitignore_path = os.path.join(root_dir, ".gitignore")
    if not os.path.isfile(gitignore_path):
        return ()

    patterns = []
    with open(gitignore_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Normalize path separators
                patterns.append(line.replace("\\", "/"))

    return tuple(patterns)


def get_gitignore_patterns(root_dir):
    """Get patterns from .gitignore file.

    Args:
        root_dir (str): Project root directory

    Returns:
        set: Set of gitignore patterns
    """
    return set(_load_gitignore_patterns(root_dir))


def is_ignored(path, root_dir, ignore_patterns):
    """Check if a path should be ignored based on gitignore patterns.

    Args:
        path (str): Path to check
        root_dir (str): Project root directory
        ignore_patterns (set): Set of gitignore patterns

    Returns:
        bool: True if path should be ignored, False otherwise
    """
    parent = os.path.dirname(path) or root_dir
    return _match_ignore_specs(
        (_build_ignore_spec(_relative_parts(parent, root_dir), ignore_patterns),),
        (os.path.basename(path),))


def _relative_parts(path, start):
    """Path components of ``path`` relative to ``start``, outermost first.

    Args:
        path (str): Path to express relatively
        start (str): Directory the components are relative to

    Returns:
        tuple: Path components, or an empty tuple when ``path`` is ``start``
    """
    rel_path = os.path.relpath(path, start).replace(os.path.sep, "/")
    return () if rel_path == "." else tuple(rel_path.split("/"))


def _build_ignore_spec(parts, patterns):
    """Prepare one level of the .gitignore stack for matching.

    The components of the checked directory are resolved once per directory
    instead of once per entry, and the ``!`` flag is resolved once per
    .gitignore instead of once per pattern per entry.

    Args:
        parts (tuple): Components of the checked directory relative to the
            directory holding the .gitignore
        patterns (iterable): Ordered patterns of that .gitignore

    Returns:
        tuple: ``(parts, patterns, has_negation)``
    """
    patterns = tuple(patterns)
    return (parts, patterns, any(pattern.startswith("!") for pattern in patterns))


def _match_ignore_specs(specs, extra=()):
    """Evaluate an ordered .gitignore stack against one path.

    Args:
        specs (tuple): Levels prepared by ``_build_ignore_spec``, outermost first
        extra (tuple): Components below the directory the stack was built for --
            ``(filename,)`` for a file, ``()`` for a subdirectory (whose own name
            is already part of the stack resolved for it)

    Returns:
        bool: True if the path should be ignored, False otherwise
    """
    ignored = False
    # A ``!`` rule can re-include a path at any level, so every level has to be
    # evaluated when one is present. Without one the first match decides.
    early_exit = not any(has_negation for _, _, has_negation in specs)

    for parts, patterns, _has_negation in specs:
        path_parts = parts + extra
        if not path_parts:
            # A directory's own .gitignore cannot exclude the directory itself.
            continue
        basename = path_parts[-1]

        for pattern in patterns:
            negated = pattern.startswith("!")
            if negated:
                pattern = pattern[1:]
            # A trailing "/" only marks the rule as directory-oriented; the
            # match itself still runs against a single path component.
            if pattern.endswith("/"):
                pattern = pattern[:-1]
            if not pattern:
                continue

            # Check the entry itself, then every directory component above it.
            if fnmatch.fnmatch(basename, pattern):
                ignored = not negated
            else:
                for subpath in path_parts:
                    if fnmatch.fnmatch(subpath, pattern):
                        ignored = not negated
                        break

            if ignored and early_exit:
                return True

    return ignored


def _ancestor_ignore_specs(walk_root):
    """.gitignore stack that applies above the walk root, outermost first.

    transx is often pointed at a subdirectory of a repository, so the rules
    above the walk root still have to be honoured.

    Args:
        walk_root (str): Directory the walk starts from

    Returns:
        tuple: Levels prepared by ``_build_ignore_spec``
    """
    specs = []
    current_dir = os.path.dirname(walk_root)
    while current_dir:
        patterns = _load_gitignore_patterns(current_dir)
        if patterns:
            specs.append(_build_ignore_spec(_relative_parts(walk_root, current_dir), patterns))
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir

    specs.reverse()
    return tuple(specs)


def _resolve_ignore_specs(dirpath, walk_root, cache):
    """Ordered .gitignore stack that applies to ``dirpath``.

    Git layers .gitignore files from the top of the tree down to the directory
    being checked: a nested file *adds* to the rules inherited from its
    ancestors and can only weaken them with ``!``. Resolving only the nearest
    file (or only the walk root's file) gets both directions wrong -- the first
    drops the ancestor rules, the second drops the nested ones.

    Args:
        dirpath (str): Directory to resolve the rules for
        walk_root (str): Directory the current walk started from
        cache (dict): Mutable cache shared by one directory walk

    Returns:
        tuple: Levels prepared by ``_build_ignore_spec``, outermost first
    """
    try:
        return cache[dirpath]
    except KeyError:
        pass

    parent_dir = os.path.dirname(dirpath)
    if dirpath == walk_root or parent_dir == dirpath:
        inherited = _ancestor_ignore_specs(dirpath) if dirpath == walk_root else ()
    else:
        # os.walk is top-down, so the parent's stack is always ready first: each
        # directory only shifts its parent's components down one level and reads
        # its own .gitignore.
        inherited = tuple(
            (parts + (os.path.basename(dirpath),), patterns, has_negation)
            for parts, patterns, has_negation
            in _resolve_ignore_specs(parent_dir, walk_root, cache))

    own_patterns = _load_gitignore_patterns(dirpath)
    specs = inherited + (_build_ignore_spec((), own_patterns),) if own_patterns else inherited

    cache[dirpath] = specs
    return specs


def should_ignore(path, root_dir=None):
    """Check if a path should be ignored based on .gitignore rules.

    Args:
        path (str): Path to check
        root_dir (str, optional): Project root directory. If None, use path's directory

    Returns:
        bool: True if path should be ignored, False otherwise
    """
    if root_dir is None:
        root_dir = os.path.dirname(path) or path

    root_dir = os.path.abspath(root_dir)
    specs = _resolve_ignore_specs(root_dir, root_dir, {})
    if not specs:
        return False

    return _match_ignore_specs(specs, (os.path.basename(path),))


def _should_ignore_cached(dirpath, walk_root, cache, extra=()):
    """``should_ignore`` for one entry of ``dirpath``, with a per-walk cache.

    Args:
        dirpath (str): Directory whose .gitignore stack applies
        walk_root (str): Directory the current walk started from
        cache (dict): Mutable cache shared by one directory walk
        extra (tuple): ``(filename,)`` for a file, ``()`` for a subdirectory

    Returns:
        bool: True if the entry should be ignored, False otherwise
    """
    specs = _resolve_ignore_specs(dirpath, walk_root, cache)
    if not specs:
        return False

    return _match_ignore_specs(specs, extra)


def walk_with_gitignore(root_dir, file_patterns=None):
    """Walk directory tree respecting .gitignore.

    Args:
        root_dir (str): Root directory to start walking from
        file_patterns (list, optional): List of file patterns to match (e.g. ['*.py'])

    Returns:
        list: List of file paths that match patterns and are not ignored
    """
    matched_files = []
    root_dir = os.path.abspath(root_dir)
    # Resolving the applicable .gitignore used to repeat the upwards directory
    # walk and re-read the file for every single entry. Now each directory
    # inherits its parent's already-resolved stack, so a walk reads every
    # .gitignore at most once while still layering nested files on top of the
    # ancestor rules the way git does.
    ignore_cache = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames.sort()
        filenames.sort()

        # Skip .git directory
        if ".git" in dirnames:
            dirnames.remove(".git")

        # Remove ignored directories
        i = len(dirnames) - 1
        while i >= 0:
            dirpath_full = os.path.join(dirpath, dirnames[i])
            if _should_ignore_cached(dirpath_full, root_dir, ignore_cache):
                del dirnames[i]
            i -= 1

        # Process files
        for filename in filenames:
            # Skip .gitignore file itself
            if filename == ".gitignore":
                continue

            # Skip ignored files
            if _should_ignore_cached(dirpath, root_dir, ignore_cache, (filename,)):
                continue

            filepath = os.path.join(dirpath, filename)

            # If patterns specified, only include matching files
            if file_patterns:
                for pattern in file_patterns:
                    if fnmatch.fnmatch(filename, pattern):
                        matched_files.append(filepath)
                        break
            else:
                matched_files.append(filepath)

    return matched_files



def get_config_file_path(app_name=None, filename="config.json"):
    """Get configuration file path with proper directory creation handling.

    Args:
        app_name: Optional application name for app-specific config
        filename: Configuration file name (default: config.json)

    Returns:
        str: Path to configuration file
    """
    paths = [
        os.path.expanduser(os.path.join("~", ".transx", app_name if app_name else "", filename)),
        os.path.join(os.getcwd(), ".transx_{}_config.json".format(app_name if app_name else "")),
    ]

    # 在 Windows 上添加 APPDATA 路径
    if os.name == "nt" and "APPDATA" in os.environ:
        paths.insert(0, os.path.join(os.environ["APPDATA"], "TransX",
                                   app_name if app_name else "", filename))

    for path in paths:
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                return path
            except (IOError, OSError):
                continue
        elif os.access(directory, os.W_OK):
            return path

    return paths[0]
