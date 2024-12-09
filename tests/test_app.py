"""Tests for the application-level API."""
# Import future modules
from __future__ import absolute_import
from __future__ import unicode_literals

# Import built-in modules
from collections import OrderedDict
import sys

# Import third-party modules
import pytest

# Import local modules
from transx import get_transx_instance
from transx.core import TransX


def test_get_transx_instance_basic():
    """Test basic instance creation."""
    instance = get_transx_instance("test_app")
    assert isinstance(instance, TransX)
    assert instance.app_name == "test_app"

def test_get_transx_instance_caching():
    """Test that instances are cached properly."""
    instance1 = get_transx_instance("test_app")
    instance2 = get_transx_instance("test_app")
    instance3 = get_transx_instance("other_app")

    # Same app should return same instance
    assert instance1 is instance2
    # Different apps should return different instances
    assert instance1 is not instance3

def test_get_transx_instance_with_kwargs():
    """Test instance creation with additional arguments."""
    instance = get_transx_instance(
        "test_app",
        default_locale="ja_JP",
        strict_mode=True
    )
    assert instance.app_name == "test_app"
    assert instance._context._default_locale == "ja_JP"

def test_get_transx_instance_invalid_app_name():
    """Test error handling for invalid app names."""
    with pytest.raises(TypeError):
        get_transx_instance(123)  # Non-string app name

    with pytest.raises(TypeError):
        get_transx_instance(None)  # None app name

def test_instance_locale_switching():
    """Test locale switching functionality."""
    instance = get_transx_instance("test_app")

    # Test switching to valid locale
    assert instance.switch_locale("ja_JP") is True

    # Test switching to same locale (should succeed)
    assert instance.switch_locale("ja_JP") is True

    # Test switching to invalid locale
    with pytest.raises(ValueError):
        instance.switch_locale("")

    with pytest.raises(ValueError):
        instance.switch_locale(None)

@pytest.mark.skipif(
    "PyQt5.QtCore" not in sys.modules,
    reason="PyQt5 is not installed"
)
def test_qt_integration():
    """Test Qt integration functionality."""
    # Import third-party modules
    from PyQt5.QtCore import QCoreApplication
    from PyQt5.QtCore import QTranslator

    app = QCoreApplication([])
    instance = get_transx_instance("test_app")
    translator = QTranslator()

    # Test registering Qt translator
    result = instance.register_qt_translator(app, translator, "dummy/path")
    assert isinstance(result, bool)  # Should return boolean

    app.quit()

def test_multiple_instances():
    """Test handling of multiple instances."""
    instances = OrderedDict()
    app_names = ["app1", "app2", "app3"]

    # Create multiple instances
    for name in app_names:
        instances[name] = get_transx_instance(name)

    # Verify each instance is unique
    for name1 in app_names:
        for name2 in app_names:
            if name1 != name2:
                assert instances[name1] is not instances[name2]
            else:
                assert instances[name1] is instances[name2]

def test_instance_persistence():
    """Test that instance settings persist."""
    instance1 = get_transx_instance("test_app")
    instance1.switch_locale("ja_JP")

    # Get same instance again
    instance2 = get_transx_instance("test_app")
    assert instance2._context.current_locale == "ja_JP"

    # Settings should persist even with new instance
    instance3 = get_transx_instance("test_app", default_locale="en_US")
    assert instance3._context._default_locale == "en_US"  # Previous setting should win

@pytest.fixture
def cleanup_instances():
    """Fixture to clean up instances after tests."""
    yield
    from transx.context import get_manager
    manager = get_manager()
    manager._instances.clear()
    manager._config.clear()

@pytest.mark.usefixtures("cleanup_instances")
def test_instance_cleanup():
    """Test that instances can be properly cleaned up."""
    instance = get_transx_instance("test_app")
    assert isinstance(instance, TransX)

    # Clean up should work
    # Import local modules
    from transx.context import get_manager
    manager = get_manager()
    manager._instances.clear()

    # Should create new instance after cleanup
    new_instance = get_transx_instance("test_app")
    assert new_instance is not instance
