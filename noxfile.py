# -*- coding: utf-8 -*-
"""Nox file for running test and development tasks."""

# Import built-in modules
import os
import sys

# Import third-party modules
import nox


ROOT = os.path.dirname(__file__)

# Ensure maya_umbrella is importable.
if ROOT not in sys.path:
    sys.path.append(ROOT)

# Import third-party modules
from nox_actions import codetest
from nox_actions import lint


nox.session(lint.lint, name="lint")
nox.session(lint.lint_fix, name="lint-fix")
nox.session(codetest.pytest, name="pytest")
nox.session(codetest.benchmark, name="benchmark")
