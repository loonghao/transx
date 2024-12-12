"""Benchmark tests for TransX performance."""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import os
import random
import string

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
    templates = [
        "Hello {name}",
        "Welcome back, {user}!",
        "Last login: {time}",
        "{count} messages",
        "Version {version}"
    ] * 20  # 100 translations
    params = [
        {"name": "TransX"},
        {"user": "Admin"},
        {"time": "2023-12-12"},
        {"count": "5"},
        {"version": "1.0.0"}
    ] * 20

    def batch_translate_with_params():
        return [transx.tr(template, **param) for template, param in zip(templates, params)]

    benchmark(batch_translate_with_params)


def test_translation_long_text(benchmark):
    """Benchmark translation of long text performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")
    long_text = " ".join(["Hello World"] * 100)  # Create a long text string

    def translate_long_text():
        return transx.tr(long_text)

    benchmark(translate_long_text)


def test_translation_mixed_load(benchmark):
    """Benchmark mixed translation operations performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    operations = [
        ("simple", "Hello World"),
        ("params", ("Hello {name}", {"name": "TransX"})),
        ("switch", "zh_CN"),
        ("fallback", "NonexistentKey"),
        ("long", " ".join(["Hello"] * 10))
    ] * 20  # 100 mixed operations

    def mixed_operations():
        results = []
        for op_type, data in operations:
            if op_type == "simple":
                results.append(transx.tr(data))
            elif op_type == "params":
                template, params = data
                results.append(transx.tr(template, **params))
            elif op_type == "switch":
                transx.switch_locale(data)
            elif op_type == "fallback" or op_type == "long":
                results.append(transx.tr(data))
        return results

    benchmark(mixed_operations)


def test_po_file_loading(benchmark):
    """Benchmark .po file loading performance."""
    locale_dir = get_locale_dir()

    def load_po_files():
        transx = TransX(locales_root=locale_dir)
        transx.switch_locale("zh_CN")
        return transx

    benchmark(load_po_files)


def test_translation_cache_performance(benchmark):
    """Benchmark translation cache performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")

    # First access to populate cache
    key = "Hello World"
    transx.tr(key)

    def cached_lookup():
        return transx.tr(key)

    benchmark(cached_lookup)


def test_translation_with_nested_params(benchmark):
    """Benchmark translation with nested parameters performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")

    def nested_params_lookup():
        return transx.tr(
            "User {user} has {count} {type} in {location}",
            user={"name": "Admin", "id": 123},
            count=5,
            type="files",
            location={"folder": "Documents", "path": "/home/docs"}
        )

    benchmark(nested_params_lookup)


def test_translation_with_large_params(benchmark):
    """Benchmark translation with large number of parameters performance."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")

    # Create a template with 50 parameters
    params = {f"param{i}": f"value{i}" for i in range(50)}
    template = "Template with many params: " + " ".join(["{" + f"param{i}" + "}" for i in range(50)])

    def large_params_lookup():
        return transx.tr(template, **params)

    benchmark(large_params_lookup)


def test_translation_concurrent_locale_switch(benchmark):
    """Benchmark performance under frequent locale switches."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    locales = ["zh_CN", "en_US", "ja_JP", "ko_KR"]  # Add more locales if available
    keys = ["Hello", "World", "TransX", "Test"]

    def concurrent_operations():
        results = []
        for _ in range(25):  # 25 switches * 4 translations = 100 operations
            locale = random.choice(locales)
            transx.switch_locale(locale)
            results.extend([transx.tr(key) for key in keys])
        return results

    benchmark(concurrent_operations)


def test_translation_memory_usage(benchmark):
    """Benchmark memory usage with large number of translations."""
    locale_dir = get_locale_dir()
    transx = TransX(locales_root=locale_dir)
    transx.switch_locale("zh_CN")

    # Generate 1000 unique keys
    keys = ["".join(random.choices(string.ascii_letters, k=10)) for _ in range(1000)]

    def memory_test():
        results = []
        for key in keys:
            results.append(transx.tr(key))
        return results

    benchmark(memory_test)
