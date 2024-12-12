# -*- coding: utf-8 -*-
"""Performance benchmarks for transx."""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import os

# Import local modules
from transx import TransX


def test_transx_init(benchmark):
    """Benchmark TransX initialization performance."""
    locale_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "examples", "locales")
    def init_transx():
        transx = TransX(locales_root=locale_dir)
        return transx

    benchmark(init_transx)


def test_translation_lookup(benchmark):
    """Benchmark translation lookup performance."""
    locale_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "examples", "locales")
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")

    def lookup_translation():
        return transx.tr("Hello World")

    benchmark(lookup_translation)
