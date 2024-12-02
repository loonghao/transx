"""Custom exceptions for TransX."""


class TransXError(Exception):
    """Base exception for all TransX errors."""


class LocaleNotFoundError(TransXError):
    """Raised when a requested locale is not found."""


class CatalogNotFoundError(TransXError):
    """Raised when a translation catalog is not found."""


class InvalidFormatError(TransXError):
    """Raised when a translation file has an invalid format."""
