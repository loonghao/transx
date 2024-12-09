"""Test cases for custom exceptions."""
# Import future modules
from __future__ import unicode_literals

# Import built-in modules
import unittest

# Import local modules
from transx.exceptions import CatalogNotFoundError
from transx.exceptions import InvalidFormatError
from transx.exceptions import LocaleNotFoundError
from transx.exceptions import ParserError
from transx.exceptions import TransXError
from transx.exceptions import TranslationError
from transx.exceptions import ValidationError


class TestExceptions(unittest.TestCase):
    """Test cases for TransX exceptions."""

    def test_transx_error(self):
        """Test TransXError exception."""
        error = TransXError("Test error")
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.message, "Test error")

    def test_catalog_not_found_error(self):
        """Test CatalogNotFoundError exception."""
        error = CatalogNotFoundError("/path/to/catalog")
        self.assertEqual(error.catalog_path, "/path/to/catalog")
        self.assertIn("/path/to/catalog", str(error))

    def test_locale_not_found_error(self):
        """Test LocaleNotFoundError exception."""
        error = LocaleNotFoundError("en_US")
        self.assertEqual(error.locale, "en_US")
        self.assertIn("en_US", str(error))

    def test_invalid_format_error(self):
        """Test InvalidFormatError exception."""
        error = InvalidFormatError("po", "/path/to/file.txt")
        self.assertEqual(error.format, "po")
        self.assertEqual(error.file_path, "/path/to/file.txt")
        self.assertIn("po", str(error))
        self.assertIn("/path/to/file.txt", str(error))

    def test_translation_error(self):
        """Test TranslationError exception."""
        error = TranslationError(
            "Translation failed",
            source_text="Hello",
            source_lang="en",
            target_lang="fr"
        )
        self.assertEqual(error.source_text, "Hello")
        self.assertEqual(error.source_lang, "en")
        self.assertEqual(error.target_lang, "fr")
        self.assertIn("Translation failed", str(error))

    def test_parser_error(self):
        """Test ParserError exception."""
        # Test with minimal arguments
        error1 = ParserError("/path/to/file.po")
        self.assertEqual(error1.file_path, "/path/to/file.po")
        self.assertIsNone(error1.line_number)
        self.assertIsNone(error1.reason)

        # Test with all arguments
        error2 = ParserError(
            "/path/to/file.po",
            line_number=42,
            reason="Invalid syntax"
        )
        self.assertEqual(error2.file_path, "/path/to/file.po")
        self.assertEqual(error2.line_number, 42)
        self.assertEqual(error2.reason, "Invalid syntax")
        self.assertIn("line 42", str(error2))
        self.assertIn("Invalid syntax", str(error2))

    def test_validation_error(self):
        """Test ValidationError exception."""
        errors = ["Error 1", "Error 2"]
        error = ValidationError("/path/to/file.po", errors)
        self.assertEqual(error.file_path, "/path/to/file.po")
        self.assertEqual(error.errors, errors)
        self.assertIn("Error 1", str(error))
        self.assertIn("Error 2", str(error))


if __name__ == "__main__":
    unittest.main()
