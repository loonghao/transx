"""Application-level utilities for TransX."""
# Import future modules
from __future__ import absolute_import
from __future__ import unicode_literals

# Import built-in modules
from collections import OrderedDict

# Import local modules
from transx.context import get_manager
from transx.internal.compat import binary_type
from transx.internal.compat import text_type


_instances = OrderedDict()  # Cache of TransX instances

def get_transx_instance(app_name, default_locale=None, strict_mode=None, auto_compile=True):
    """Get a TransX instance for the given application.

    This function will:
    1. Get the locale root from environment variable TRANSX_{APP_NAME}_LOCALES_ROOT
    2. Create or return a cached TransX instance with the given configuration
    3. Load persisted settings if available

    Args:
        app_name: Name of the application
        default_locale: Default locale to use. If None, uses system locale
        strict_mode: If True, raise exceptions for missing translations
        auto_compile: If True, automatically compile PO files to MO files

    Returns:
        TransX: A configured TransX instance

    Raises:
        KeyError: If TRANSX_{APP_NAME}_LOCALES_ROOT environment variable is not set
    """
    if not isinstance(app_name, (text_type, binary_type)):
        raise TypeError("app_name must be a string")

    return get_manager().get_instance(
        app_name,
        default_locale=default_locale,
        strict_mode=strict_mode,
        auto_compile=auto_compile
    )
