"""TransX - A flexible translation framework."""

# fmt: off
# isort: skip_file
# ruff: noqa: I001, RUF022
from transx.internal.logging import setup_logging

# Configure basic logging with default settings
setup_logging("transx")

from transx.api import POFile
from transx.api import PotExtractor
from transx.api import compile_po_file
from transx.api.translation_catalog import TranslationCatalog
from transx.core import TransX
from transx.exceptions import CatalogNotFoundError
from transx.exceptions import InvalidFormatError
from transx.exceptions import LocaleNotFoundError
from transx.exceptions import TransXError
from transx.exceptions import TranslationError

# fmt: on

__all__ = [
    "CatalogNotFoundError",
    "compile_po_file",
    "InvalidFormatError",
    "LocaleNotFoundError",
    "POFile",
    "PotExtractor",
    "TransX",
    "TransXError",
    "TranslationCatalog",
    "TranslationError",
]
