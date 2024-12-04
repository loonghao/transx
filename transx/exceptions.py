"""Custom exceptions for TransX."""
# Import future modules
from __future__ import unicode_literals


class TransXError(Exception):
    """Base exception for TransX."""

    def __init__(self, message, *args):
        """Initialize the exception.

        Args:
            message: Error message
            *args: Additional arguments
        """
        super(TransXError, self).__init__(message, *args)
        self.message = message


class CatalogNotFoundError(TransXError):
    """Raised when a translation catalog is not found."""

    def __init__(self, catalog_path, *args):
        """Initialize the exception.

        Args:
            catalog_path: Path to the missing catalog
            *args: Additional arguments
        """
        message = "Translation catalog not found: %s" % catalog_path
        super(CatalogNotFoundError, self).__init__(message, *args)
        self.catalog_path = catalog_path


class LocaleNotFoundError(TransXError):
    """Raised when a locale directory is not found."""

    def __init__(self, locale, *args):
        """Initialize the exception.

        Args:
            locale: Locale code that was not found
            *args: Additional arguments
        """
        message = "Locale not found: %s" % locale
        super(LocaleNotFoundError, self).__init__(message, *args)
        self.locale = locale


class InvalidFormatError(TransXError):
    """Raised when a file format is invalid."""

    def __init__(self, file_path, reason=None, *args):
        """Initialize the exception.

        Args:
            file_path: Path to the invalid file
            reason: Optional reason for the invalid format
            *args: Additional arguments
        """
        message = "Invalid file format: %s" % file_path
        if reason:
            message += " (%s)" % reason
        super(InvalidFormatError, self).__init__(message, *args)
        self.file_path = file_path
        self.reason = reason


class TranslationError(TransXError):
    """Raised when a translation operation fails."""

    def __init__(self, message, source_text=None, source_lang=None, target_lang=None, *args):
        """Initialize the exception.

        Args:
            message: Error message
            source_text: Optional source text that failed to translate
            source_lang: Optional source language code
            target_lang: Optional target language code
            *args: Additional arguments
        """
        super(TranslationError, self).__init__(message, *args)
        self.source_text = source_text
        self.source_lang = source_lang
        self.target_lang = target_lang


class ParserError(TransXError):
    """Raised when parsing a translation file fails."""

    def __init__(self, file_path, line_number=None, reason=None, *args):
        """Initialize the exception.

        Args:
            file_path: Path to the file that failed to parse
            line_number: Optional line number where the error occurred
            reason: Optional reason for the parsing error
            *args: Additional arguments
        """
        message = "Failed to parse file: %s" % file_path
        if line_number is not None:
            message += " at line %d" % line_number
        if reason:
            message += " (%s)" % reason
        super(ParserError, self).__init__(message, *args)
        self.file_path = file_path
        self.line_number = line_number
        self.reason = reason


class ValidationError(TransXError):
    """Raised when validating a translation file fails."""

    def __init__(self, file_path, errors, *args):
        """Initialize the exception.

        Args:
            file_path: Path to the file that failed validation
            errors: List of validation errors
            *args: Additional arguments
        """
        message = "Validation failed for file: %s\n%s" % (
            file_path,
            "\n".join("- " + str(error) for error in errors)
        )
        super(ValidationError, self).__init__(message, *args)
        self.file_path = file_path
        self.errors = errors
