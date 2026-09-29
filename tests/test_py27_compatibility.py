#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Static guard for the declared Python 2.7 support.

The project declares ``python = ">=2.7,<4.0"`` but CI only runs 3.7-3.12, so
a Python 3 only construct is invisible until someone actually runs 2.7. This
module parses every source file and rejects the constructs that would break
there. It is not a substitute for running 2.7, just a cheap regression guard
that runs on the versions CI does cover.
"""

# Import future modules
from __future__ import unicode_literals

# Import built-in modules
import ast
import io
import os
import re

# Import third-party modules
import pytest

PACKAGE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "transx")

# Constructs that are syntactically valid on Python 3 but not on Python 2.7.
SOURCE_PATTERNS = [
    (re.compile(r"""(?:^|[^\w'"])[fF]["']"""), "f-string"),
    (re.compile(r"\bnonlocal\b"), "nonlocal"),
    (re.compile(r"\byield\s+from\b"), "yield from"),
    (re.compile(r"\basync\s+def\b"), "async def"),
    (re.compile(r"\bawait\b"), "await"),
    (re.compile(r":="), "walrus operator"),
    (re.compile(r"\bdef\s+\w+\s*\([^)]*\b\w+\s*:\s*\w+"), "annotated parameter"),
    (re.compile(r"\bdef\s+\w+\s*\([^)]*\)\s*->"), "annotated return"),
]

# APIs that do not exist on Python 2.7.
FORBIDDEN_APIS = [
    (re.compile(r"\bos\.replace\s*\("), "os.replace (use os.rename)"),
    (re.compile(r"\bos\.makedirs\s*\([^)]*exist_ok"), "os.makedirs(exist_ok=)"),
    (re.compile(r"\bsubprocess\.run\s*\("), "subprocess.run"),
    (re.compile(r"\bimport\s+pathlib\b"), "pathlib"),
    (re.compile(r"\bfrom\s+pathlib\b"), "pathlib"),
    (re.compile(r"\bimport\s+dataclasses\b"), "dataclasses"),
    (re.compile(r"\bfrom\s+dataclasses\b"), "dataclasses"),
    (re.compile(r"\bimport\s+typing\b"), "typing"),
    (re.compile(r"\bfrom\s+typing\b"), "typing"),
]


def _source_files():
    """Yield every Python file shipped in the package.

    Yields:
        str: Absolute path to a source file
    """
    for root, dirs, files in os.walk(PACKAGE_ROOT):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in sorted(files):
            if name.endswith(".py"):
                yield os.path.join(root, name)


def _strip_string_prefixes(line):
    """Blank out string literals so escapes like ``"\\f"`` are not misread.

    Args:
        line: A line of source

    Returns:
        str: The line with string literal contents removed
    """
    return re.sub(r"""["'].*?["']""", '""', line)


def test_all_sources_parse():
    """Every shipped module must at least parse."""
    for path in _source_files():
        with io.open(path, encoding="utf-8") as handle:
            source = handle.read()
        try:
            ast.parse(source, filename=path)
        except SyntaxError as exc:
            pytest.fail("%s does not parse: %s" % (path, exc))


def test_no_python3_only_syntax():
    """Reject syntax Python 2.7 cannot parse."""
    offenders = []

    for path in _source_files():
        with io.open(path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()

        for number, line in enumerate(lines, 1):
            code = line.split("#")[0]
            # Drop string literals so an escaped \f is not read as an f-string.
            code = _strip_string_prefixes(code)
            for pattern, label in SOURCE_PATTERNS:
                if pattern.search(code):
                    offenders.append("%s:%d uses %s: %s" % (path, number, label, line.strip()))

    assert offenders == [], "\n".join(offenders)


def test_no_python3_only_apis():
    """Reject stdlib APIs that do not exist on Python 2.7."""
    offenders = []

    for path in _source_files():
        with io.open(path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()

        for number, line in enumerate(lines, 1):
            code = line.split("#")[0]
            for pattern, label in FORBIDDEN_APIS:
                if pattern.search(code):
                    offenders.append("%s:%d uses %s: %s" % (path, number, label, line.strip()))

    assert offenders == [], "\n".join(offenders)


#: Modules introduced with the translation memory. Pre-existing modules are
#: out of scope here; this guard exists to stop new code from regressing.
NEW_MODULES = [
    os.path.join("internal", "translation_memory.py"),
]


def test_new_modules_declare_future_imports():
    """New modules must opt into the Python 3 semantics available on 2.7."""
    missing = []

    for relative in NEW_MODULES:
        path = os.path.join(PACKAGE_ROOT, relative)
        assert os.path.isfile(path), "expected module is missing: %s" % path

        with io.open(path, encoding="utf-8") as handle:
            source = handle.read()

        if "unicode_literals" in source or "absolute_import" in source:
            continue
        missing.append(path)

    assert missing == [], "modules missing __future__ imports: %s" % missing
