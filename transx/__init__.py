"""TransX - A flexible translation system for Python applications."""
# Import future modules
from __future__ import absolute_import
from __future__ import unicode_literals

from .__version__ import __version__
from .app import get_transx_instance
from .core import TransX


__all__ = [
    "TransX",
    "__version__",
    "get_transx_instance",
]
