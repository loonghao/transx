#!/usr/bin/env python
"""Core translation functionality."""

# Import built-in modules
import os
import gettext
import logging
import sys

# Import local modules
from transx.constants import (
    DEFAULT_LOCALES_DIR,
    DEFAULT_LOCALE,
    DEFAULT_MESSAGES_DOMAIN,
    DEFAULT_CHARSET,
    PO_FILE_EXTENSION,
    MO_FILE_EXTENSION
)
from transx.translation_catalog import TranslationCatalog
from transx.exceptions import LocaleNotFoundError, CatalogNotFoundError

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode  # noqa: F821
    binary_type = str
else:
    text_type = str
    binary_type = bytes


class MOFile(gettext.GNUTranslations):
    """Custom MO file handler with proper encoding support."""
    
    def _parse(self, fp):
        """Parse MO file with UTF-8 encoding."""
        self._charset = DEFAULT_CHARSET
        self._output_charset = DEFAULT_CHARSET
        super(MOFile, self)._parse(fp)


class TransX:
    """Main translation class for handling translations."""
    
    def __init__(self, locales_root=None, default_locale=DEFAULT_LOCALE, strict_mode=False):
        """Initialize translator.
        
        Args:
            locales_root: Root directory for translation files. Defaults to './locales'
            default_locale: Default locale to use. Defaults to 'en_US'
            strict_mode: If True, raise exceptions when translations or files are missing.
                        If False, return original text and log warnings. Defaults to False.
        """
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
        logging.debug("Initialized TransX with locales_root: {}, default_locale: {}, strict_mode: {}".format(
            self.locales_root, self.default_locale, self.strict_mode))

    def load_catalog(self, locale):
        """Load translation catalog for the specified locale.
        
        Args:
            locale: Locale to load catalog for
            
        Returns:
            bool: True if catalog was loaded successfully, False otherwise
            
        Raises:
            LocaleNotFoundError: If locale directory not found (only in strict mode)
            CatalogNotFoundError: If catalog file not found (only in strict mode)
        """
        if locale in self._translations or locale in self._catalogs:
            return True
            
        locale_dir = os.path.join(self.locales_root, locale, "LC_MESSAGES")
        
        if not os.path.exists(locale_dir):
            msg = "Locale directory not found: {}".format(locale_dir)
            if self.strict_mode:
                raise LocaleNotFoundError(msg)
            logging.debug(msg)
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
                logging.debug(msg)
        
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
                logging.debug(msg)
        
        if self.strict_mode:
            raise CatalogNotFoundError("No translation catalog found for locale: {}".format(locale))
        logging.debug("No translation catalog found for locale: {}".format(locale))
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
            elif line.startswith('"'):
                if current_msgstr is not None:
                    current_msgstr.append(line[1:-1])
        
        if current_msgid is not None:
            catalog.add_message(current_msgid, "".join(current_msgstr), current_context)
    
    def add_translation(self, msgid, msgstr, context=None):
        """Add a translation entry.
        
        Args:
            msgid: The message ID
            msgstr: The translated string
            context: The context for the message (optional)
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
            ValueError: If locale is None or empty
        """
        if not locale:
            raise ValueError("Locale cannot be None or empty")
            
        if locale != self._current_locale:
            locale_dir = os.path.join(self.locales_root, locale, "LC_MESSAGES")
            if not os.path.exists(locale_dir):
                raise LocaleNotFoundError(f"Locale directory not found: {locale_dir}")
                
            self._current_locale = locale
            if locale not in self._translations:
                self.load_catalog(locale)
    
    def tr(self, text, context=None, **kwargs):
        """Translate text.
        
        Args:
            text: Text to translate
            context: Message context
            **kwargs: Format parameters
            
        Returns:
            Translated text with parameters filled in, or original text if translation not found
            and strict_mode is False
            
        Raises:
            ValueError: If text is None
            KeyError: If required format parameters are missing
        """
        # Handle None input
        if text is None:
            raise ValueError("Translation text cannot be None")
            
        # Handle empty string
        if text == "":
            return ""
            
        # Ensure text is unicode in both Python 2 and 3
        if isinstance(text, binary_type):
            text = text.decode(DEFAULT_CHARSET)
            
        if context:
            # Add context separator
            msgid = context + "\x04" + text
        else:
            msgid = text
            
        # Log translation attempt
        logging.debug("Translating text: '{}' with context: '{}' and kwargs: {}".format(
            text, context, kwargs))
        
        translated = None
        # Try to get translation
        if self._current_locale in self._translations:
            trans = self._translations[self._current_locale]
            if context:
                translated = trans.pgettext(context, text)
            else:
                translated = trans.gettext(text)
        elif self._current_locale in self._catalogs:
            catalog = self._catalogs[self._current_locale]
            translated = catalog.get_message(msgid)
        
        # If no translation found and not in strict mode, use original text
        if translated is None:
            translated = text
            logging.debug("No translation found for text: {} (context: {}), using original text".format(
                text, context))
        
        # Log translation result
        logging.debug("Translation result: '{}'".format(translated))
        if kwargs:
            try:
                translated = translated.format(**kwargs)
            except KeyError as e:
                msg = "Missing format parameter in translation: {}".format(str(e))
                if self.strict_mode:
                    raise KeyError(msg)
                logging.debug(msg)
                return text
            except Exception as e:
                msg = "Error formatting translation: {}".format(str(e))
                if self.strict_mode:
                    raise
                logging.debug(msg)
                return text
        
        return translated
