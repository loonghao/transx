"""TransX - A flexible translation framework."""

import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set specific loggers to DEBUG level
logging.getLogger("transx.api.translate").setLevel(logging.DEBUG)
logging.getLogger("transx.api.po").setLevel(logging.DEBUG)

# Import local modules
from transx.api import POFile, PotExtractor, compile_po_file
from transx.api.translation_catalog import TranslationCatalog
from transx.core import TransX
from transx.exceptions import (
    CatalogNotFoundError,
    InvalidFormatError,
    LocaleNotFoundError,
    TranslationError,
    TransXError,
)

__all__ = [
    "CatalogNotFoundError",
    "InvalidFormatError",
    "LocaleNotFoundError",
    "POFile",
    "PotExtractor",
    "TransX",
    "TransXError",
    "TranslationCatalog",
    "TranslationError",
    "compile_po_file",
]
