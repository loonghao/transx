#!/usr/bin/env python
"""Core translation functionality."""

# Import built-in modules
import logging
import os
import sys

# Import local modules
from transx.api.mo import MOFile
from transx.constants import (
    DEFAULT_CHARSET,
    DEFAULT_LOCALE,
    DEFAULT_LOCALES_DIR,
    DEFAULT_MESSAGES_DOMAIN,
    MO_FILE_EXTENSION,
    PO_FILE_EXTENSION
)
from transx.exceptions import CatalogNotFoundError, LocaleNotFoundError
from transx.api.translation_catalog import TranslationCatalog
from transx.compat import ensure_unicode

class TransX:
    """Main translation class for handling translations."""

    def __init__(self, locales_root=None, default_locale=DEFAULT_LOCALE, strict_mode=False):
        """Initialize translator.

        Args:
            locales_root: Root directory for translation files. Defaults to './locales'
            default_locale: Default locale to use. Defaults to 'en'
            strict_mode: If True, raise exceptions for missing translations. Defaults to False
        """
        self.logger = logging.getLogger(__name__)
        self.locales_root = os.path.abspath(locales_root or DEFAULT_LOCALES_DIR)
        self.default_locale = default_locale
        self.strict_mode = strict_mode
        self._current_locale = default_locale
        self._translations = {}  # {locale: gettext.GNUTranslations}
        self._catalogs = {}  # {locale: TranslationCatalog}

        # Create locales directory if it doesn't exist
        if not os.path.exists(self.locales_root):
            os.makedirs(self.locales_root)

        # Log initialization details
        self.logger.debug("Initialized TransX with locales_root: {}, default_locale: {}, strict_mode: {}".format(
            self.locales_root, self.default_locale, self.strict_mode))

    def load_catalog(self, locale):
        """Load translation catalog for the specified locale.

        Args:
            locale: Locale to load catalog for

        Returns:
            bool: True if catalog was loaded successfully, False otherwise

        Raises:
            LocaleNotFoundError: If locale directory not found (only in strict mode)
            ValueError: If locale is None
        """
        if locale in self._translations or locale in self._catalogs:
            return True

        locale_dir = os.path.join(self.locales_root, locale, "LC_MESSAGES")

        if not os.path.exists(locale_dir):
            msg = "Locale directory not found: {}".format(locale_dir)
            if self.strict_mode:
                raise LocaleNotFoundError(msg)
            self.logger.debug(msg)
            return False

        mo_file = os.path.join(locale_dir, DEFAULT_MESSAGES_DOMAIN + MO_FILE_EXTENSION)
        po_file = os.path.join(locale_dir, DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)

        # Try loading MO file first
        if os.path.exists(mo_file):
            try:
                with open(mo_file, "rb") as fp:
                    self._translations[locale] = MOFile(fp)
                return True
            except Exception as e:
                msg = "Failed to load MO file {}: {}".format(mo_file, str(e))
                if self.strict_mode:
                    raise CatalogNotFoundError(msg)
                self.logger.debug(msg)

        # Fall back to PO file if MO file not found or failed to load
        if os.path.exists(po_file):
            try:
                catalog = TranslationCatalog(locale=locale)
                catalog.load(po_file)
                self._catalogs[locale] = catalog
                return True
            except Exception as e:
                msg = "Failed to load PO file {}: {}".format(po_file, str(e))
                if self.strict_mode:
                    raise CatalogNotFoundError(msg)
                self.logger.debug(msg)

        if self.strict_mode:
            raise CatalogNotFoundError("No translation catalog found for locale: {}".format(locale))
        self.logger.debug("No translation catalog found for locale: {}".format(locale))
        return False

    def _parse_po_file(self, fileobj, catalog):
        """Parse a PO file and add messages to the catalog."""
        current_msgid = None
        current_msgstr = []
        current_context = None

        for line in fileobj:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith('msgctxt "'):
                current_context = line[9:-1]
            elif line.startswith('msgid "'):
                if current_msgid is not None:
                    catalog.add_message(current_msgid, "".join(current_msgstr), current_context)
                current_msgid = line[7:-1]
                current_msgstr = []
                current_context = None
            elif line.startswith('msgstr "'):
                current_msgstr = [line[8:-1]]
            elif line.startswith('"') and current_msgstr is not None:
                current_msgstr.append(line[1:-1])

        if current_msgid is not None:
            catalog.add_message(current_msgid, "".join(current_msgstr), current_context)

    def add_translation(self, msgid, msgstr, context=None):
        """Add a translation entry.

        Args:
            msgid: The message ID
            msgstr: The translated string
            context: Optional context for the translation
        """
        if context:
            msgid = context + "\x04" + msgid
        if self._current_locale not in self._catalogs:
            self._catalogs[self._current_locale] = TranslationCatalog(locale=self._current_locale)
        self._catalogs[self._current_locale].add_translation(msgid, msgstr)

    @property
    def current_locale(self):
        """Get current locale."""
        return self._current_locale

    @current_locale.setter
    def current_locale(self, locale):
        """Set current locale and load translations.

        Args:
            locale: Locale code (e.g. 'en_US', 'zh_CN')

        Raises:
            LocaleNotFoundError: If the locale directory doesn't exist
            ValueError: If locale is None
        """
        if not locale:
            raise ValueError("Locale cannot be None")

        if locale != self._current_locale:
            locale_dir = os.path.join(self.locales_root, locale, "LC_MESSAGES")
            if not os.path.exists(locale_dir) and self.strict_mode:
                    raise LocaleNotFoundError(f"Locale directory not found: {locale_dir}")

            self._current_locale = locale
            if locale not in self._translations:
                self.load_catalog(locale)

    def translate(self, msgid, catalog=None, **kwargs):
        """Translate a message."""
        if catalog is None:
            raise CatalogNotFoundError("No catalog provided")

        if msgid not in catalog:
            return msgid

        msgstr = catalog[msgid]

        try:
            return msgstr.format(**kwargs) if kwargs else msgstr
        except KeyError as e:
            raise KeyError("Missing parameter in translation: {}".format(e))
        except Exception:
            return msgstr

    def tr(self, text: str, **kwargs) -> str:
        """Translate a string.

        Args:
            text: The string to translate
            **kwargs: Format arguments

        Returns:
            The translated string
        """
        # Ensure text is unicode
        text = ensure_unicode(text)

        if not self._translations:
            return text

        trans = self._translations.get(self._current_locale)
        if not trans:
            return text

        translated = trans.gettext(text)
        
        # If we have format parameters, ensure they are consistent
        if kwargs:
            try:
                # First check if the original text can be formatted with the provided kwargs
                text.format(**kwargs)
                
                # If translation has different parameter names, replace them with original ones
                import re
                format_params = re.findall(r'\{(\w+)\}', text)
                for param in format_params:
                    if param in kwargs:
                        translated = re.sub(r'\{[^}]+\}', '{' + param + '}', translated, count=1)
                
                translated = translated.format(**kwargs)
            except KeyError as e:
                msg = "Missing format parameter in translation: {}".format(str(e))
                raise KeyError(msg)
            except Exception as e:
                msg = "Error formatting translation: {}".format(str(e))
                raise ValueError(msg)

        return translated
