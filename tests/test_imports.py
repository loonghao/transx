# -*- coding: utf-8 -*-
"""Import Test."""

# Import future modules
from __future__ import absolute_import, division, print_function

# Import built-in modules
import importlib
import pkgutil

# Import local modules
import transx


def test_imports():
    """Test import modules."""
    prefix = "{}.".format(transx.__name__)
    iter_packages = pkgutil.walk_packages(
        transx.__path__,
        prefix,
    )
    for _, name, _ in iter_packages:
        module_name = name if name.startswith(prefix) else prefix + name
        importlib.import_module(module_name)
