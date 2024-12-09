"""Tests for the TransX context manager."""
# Import future modules
from __future__ import absolute_import
from __future__ import unicode_literals

# Import built-in modules
from collections import OrderedDict

# Import third-party modules
import pytest

# Import local modules
from transx.constants import DEFAULT_LOCALE
from transx.context.manager import TransXContextManager
from transx.core import TransX


@pytest.fixture
def manager():
    """Fixture providing a clean TransXContextManager instance."""
    return TransXContextManager()

def test_manager_initialization(manager):
    """Test manager initialization."""
    assert isinstance(manager._instances, OrderedDict)
    assert isinstance(manager._config, dict)
    assert len(manager._instances) == 0
    assert len(manager._config) == 0

def test_get_instance(manager):
    """Test getting TransX instances."""
    # Get first instance
    instance1 = manager.get_instance("test_app")
    assert isinstance(instance1, TransX)
    assert instance1.app_name == "test_app"

    # Get same instance again
    instance2 = manager.get_instance("test_app")
    assert instance1 is instance2

    # Get different instance
    instance3 = manager.get_instance("other_app")
    assert instance3 is not instance1
    assert instance3.app_name == "other_app"

def test_get_instance_with_kwargs(manager):
    """Test getting instances with additional arguments."""
    instance = manager.get_instance(
        "test_app",
        default_locale="ja_JP",
    )
    assert instance.app_name == "test_app"
    assert instance.context.default_locale == "ja_JP"  # Use property instead

def test_get_config(manager):
    """Test configuration management."""
    # Get default config
    config1 = manager.get_config("test_app")
    assert isinstance(config1, dict)
    assert config1["locale"] == DEFAULT_LOCALE

    # Modify config
    config1["locale"] = "ja_JP"

    # Get same config again
    config2 = manager.get_config("test_app")
    assert config2["locale"] == "ja_JP"

    # Get different app config
    config3 = manager.get_config("other_app")
    assert config3["locale"] == DEFAULT_LOCALE

def test_manager_instance_tracking(manager):
    """Test that manager properly tracks instances."""
    instance1 = manager.get_instance("app1")
    instance2 = manager.get_instance("app2")

    assert len(manager._instances) == 2
    assert manager._instances["app1"] is instance1
    assert manager._instances["app2"] is instance2

def test_manager_config_isolation(manager):
    """Test that configurations are properly isolated."""
    config1 = manager.get_config("app1")
    config2 = manager.get_config("app2")

    config1["locale"] = "ja_JP"
    config2["locale"] = "fr_FR"

    assert manager.get_config("app1")["locale"] == "ja_JP"
    assert manager.get_config("app2")["locale"] == "fr_FR"

def test_manager_instance_reuse(manager):
    """Test instance reuse behavior."""
    instance1 = manager.get_instance("test_app", default_locale="ja_JP")
    instance2 = manager.get_instance("test_app", default_locale="en_US")

    # Should reuse existing instance and ignore new kwargs
    assert instance1 is instance2
    assert instance1.context.default_locale == "en_US"  # Use property instead
    instance3 = manager.get_instance("test_app")
    assert instance3.context.default_locale == "en_US"
