"""Benchmark tests for TransX performance."""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import os

# Import local modules
from transx import TransX


def get_locale_dir():
    """Get the locale directory path."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "examples", "locales")


def test_transx_init(benchmark):
    """Benchmark TransX initialization performance."""
    locale_dir = get_locale_dir()

    def init_transx():
        transx = TransX(locales_root=locale_dir)
        return transx

    benchmark(init_transx)


def test_translation_lookup(benchmark):
    """Benchmark translation lookup performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")

    def lookup_translation():
        return transx.tr("Hello World")

    benchmark(lookup_translation)


def test_translation_with_params(benchmark):
    """Benchmark translation with parameters performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")

    def lookup_with_params():
        return transx.tr("Hello {name}", name="TransX")

    benchmark(lookup_with_params)


def test_translation_with_multiple_params(benchmark):
    """Benchmark translation with multiple parameters performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")

    def lookup_with_multiple_params():
        return transx.tr("Hello {name} at {time}", name="TransX", time="12:00")

    benchmark(lookup_with_multiple_params)


def test_translation_switch_locale(benchmark):
    """Benchmark locale switching performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    locales = ["zh_CN", "en_US"]
    current_locale_idx = 0

    def switch_locale():
        nonlocal current_locale_idx
        transx.switch_locale(locales[current_locale_idx])
        current_locale_idx = (current_locale_idx + 1) % len(locales)

    benchmark(switch_locale)


def test_translation_fallback(benchmark):
    """Benchmark translation fallback performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")

    def lookup_with_fallback():
        # Use a non-existent key to trigger fallback mechanism
        return transx.tr("NonexistentKey_ForBenchmark")

    benchmark(lookup_with_fallback)


def test_translation_batch(benchmark):
    """Benchmark batch translation performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")
    keys = ["Hello World", "Cancel", "OK", "File", "Edit"] * 20  # 100 translations

    def batch_translate():
        return [transx.tr(key) for key in keys]

    benchmark(batch_translate)


def test_translation_batch_with_params(benchmark):
    """Benchmark batch translation with parameters performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")
    templates = ["Hello {name}", "Welcome {user}", "Time: {time}"] * 10  # 30 translations
    params = [
        {"name": "TransX"},
        {"user": "Admin"},
        {"time": "12:00"}
    ] * 10

    def batch_translate_with_params():
        return [transx.tr(template, **param)
                for template, param in zip(templates, params)]

    benchmark(batch_translate_with_params)


def test_translation_long_text(benchmark):
    """Benchmark translation of long text performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")
    long_text = "This is a very long text that needs to be translated " * 10

    def translate_long_text():
        return transx.tr(long_text)

    benchmark(translate_long_text)


def test_translation_mixed_load(benchmark):
    """Benchmark mixed translation operations performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")
    operations = [
        ("simple", "Hello World"),
        ("params", ("Hello {name}", {"name": "TransX"})),
        ("fallback", "NonexistentKey"),
        ("long", "This is a long text " * 5)
    ]

    def mixed_operations():
        results = []
        for op_type, data in operations:
            if op_type == "params":
                template, params = data
                results.append(transx.tr(template, **params))
            else:
                results.append(transx.tr(data))
        return results

    benchmark(mixed_operations)


def test_po_file_loading(benchmark):
    """Benchmark .po file loading performance."""
    locale_dir = get_locale_dir()

    def load_po():
        # Create new instance to force loading translations
        transx = TransX(locales_root=locale_dir)
        transx.switch_locale("zh_CN")
        return transx

    benchmark(load_po)
