"""Internal context manager for TransX instances."""
# Import future modules
from __future__ import absolute_import
from __future__ import unicode_literals

# Import built-in modules
from collections import OrderedDict
import logging
import os

# Import local modules
from transx.api.locale import normalize_language_code
from transx.constants import DEFAULT_LOCALE
from transx.core import TransX


class TransXContextManager(object):
    """Internal context manager for TransX instances.

    This class manages TransX instances and their configurations.
    It is not intended to be used directly by end users.
    """
    def __init__(self):
        """Initialize the context manager."""
        self.logger = logging.getLogger(__name__)
        self._instances = OrderedDict()
        self._config = {}

    def get_instance(self, app_name, **kwargs):
        """Get or create a TransX instance.

        Args:
            app_name: Application name
            **kwargs: Additional arguments for TransX constructor

        Returns:
            TransX: Instance for the given app
        """
        if app_name in self._instances:
            instance = self._instances[app_name]
            default_locale = kwargs.get("default_locale")
            if default_locale:
                default_locale = normalize_language_code(default_locale)
                # Only log if the requested locale is different
                if default_locale != instance._context.default_locale:
                    self.logger.debug("Ignoring default_locale=%s for existing instance with locale %s",
                               default_locale, instance._context.default_locale)
                instance._context.default_locale =  default_locale
            return instance

        # Get locales root from environment with None as default
        env_var = "TRANSX_{}_LOCALES_ROOT".format(app_name.upper())
        locales_root = os.getenv(env_var)

        # Create new instance with locales root and app name
        instance = TransX(locales_root=locales_root, app_name=app_name, **kwargs)
        self._instances[app_name] = instance

        return instance

    def get_config(self, app_name):
        """Get configuration for an app.

        Args:
            app_name: Application name

        Returns:
            dict: App configuration
        """
        if app_name not in self._config:
            self._config[app_name] = {
                "locale": DEFAULT_LOCALE
            }
        return self._config[app_name]
