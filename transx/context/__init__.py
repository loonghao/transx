"""Internal context management for TransX."""
# Import future modules
from __future__ import absolute_import
from __future__ import unicode_literals

# Import local modules
from transx.context.manager import TransXContextManager


_global_manager = None

def get_manager():
    """Get the global TransX context manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = TransXContextManager()
    return _global_manager

def get_transx(app_name, **kwargs):
    """Get a TransX instance for the given application.

    Args:
        app_name: Application name
        **kwargs: Additional arguments for TransX constructor

    Returns:
        TransX: Instance for the given app
    """
    return get_manager().get_instance(app_name, **kwargs)

__all__ = ["TransXContextManager", "get_manager", "get_transx"]
