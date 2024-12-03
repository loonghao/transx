#!/usr/bin/env python
"""Core translation functionality."""

# Import built-in modules
import logging
import os
from string import Template

# Import local modules
from transx.api.mo import MOFile, compile_po_file
from transx.api.po import POFile
from transx.api.translation_catalog import TranslationCatalog
from transx.compat import ensure_unicode, string_types
from transx.constants import (
    DEFAULT_LOCALE,
    DEFAULT_LOCALES_DIR,
    DEFAULT_MESSAGES_DOMAIN,
    MO_FILE_EXTENSION,
    PO_FILE_EXTENSION,
)
from transx.exceptions import CatalogNotFoundError, LocaleNotFoundError


class TransX:
    """Main translation class for handling translations."""

    def __init__(self, locales_root=None, default_locale=DEFAULT_LOCALE, strict_mode=False, auto_compile=True):
        """Initialize translator.

        Args:
            locales_root: Root directory for translation files. Defaults to './locales'
            default_locale: Default locale to use. Defaults to 'en'
            strict_mode: If True, raise exceptions for missing translations. Defaults to False
        """
        self.logger = logging.getLogger(__name__)
        self.auto_compile = auto_compile
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
        self.logger.debug("Initialized TransX with locales_root: %s, default_locale: %s, strict_mode: %s" % (
            self.locales_root, self.default_locale, self.strict_mode))
            
        # Load catalog for default locale
        if default_locale:
            self.load_catalog(default_locale)

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
        if locale is None:
            raise ValueError("Locale cannot be None")

        # Get paths
        locale_dir = os.path.join(self.locales_root, locale, "LC_MESSAGES")
        if not os.path.exists(locale_dir):
            msg = "Locale directory not found: %s" % locale_dir
            if self.strict_mode:
                raise LocaleNotFoundError(msg)
            self.logger.debug(msg)
            return False

        mo_file = os.path.join(locale_dir, DEFAULT_MESSAGES_DOMAIN + MO_FILE_EXTENSION)
        po_file = os.path.join(locale_dir, DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
        
        self.logger.debug("Checking MO file: %s" % mo_file)
        self.logger.debug("Checking PO file: %s" % po_file)
        
        # First try loading .mo file
        if os.path.exists(mo_file):
            try:
                with open(mo_file, "rb") as fp:
                    mo = MOFile(fp)
                    self._translations[locale] = mo
                    self._catalogs[locale] = TranslationCatalog(translations=mo.translations, locale=locale)
                    self.logger.debug("Loaded MO file: %s" % mo_file)
                    self.logger.debug("Translations loaded: %d" % len(mo.translations))
                    return True
            except Exception as e:
                msg = "Failed to load MO file %s: %s" % (mo_file, str(e))
                self.logger.debug(msg)
                # Don't raise error here, try PO file next
    
        # If .mo file doesn't exist or failed to load, try .po file
        if os.path.exists(po_file):
            try:
                catalog = POFile(path=po_file, locale=locale)
                catalog.load()
                self._translations[locale] = catalog
                self._catalogs[locale] = TranslationCatalog(translations=catalog.translations, locale=locale)
                self.logger.debug("Loaded PO file: %s" % po_file)
                self.logger.debug("Translations loaded: %d" % len(catalog.translations))
                if self.auto_compile:
                    # Try to compile PO to MO for better performance next time
                    try:
                        compile_po_file(po_file, mo_file)
                        self.logger.debug("Compiled PO file to MO: %s" % mo_file)
                    except Exception as e:
                        self.logger.warning("Failed to compile PO to MO: %s" % str(e))
                return True
            except Exception as e:
                msg = "Failed to load PO file %s: %s" % (po_file, str(e))
                if self.strict_mode:
                    raise CatalogNotFoundError(msg)
                self.logger.debug(msg)
                return False

        msg = "No translation files found for locale: %s" % locale
        if self.strict_mode:
            raise CatalogNotFoundError(msg)
        self.logger.debug(msg)
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
        if locale is None:
            raise ValueError("Locale cannot be None")

        # Check if locale directory exists
        locale_dir = os.path.join(self.locales_root, locale, "LC_MESSAGES")
        if not os.path.exists(locale_dir) and self.strict_mode:
            raise LocaleNotFoundError("Locale directory not found: %s" % locale_dir)

        # Set the locale first
        self._current_locale = locale
        
        # Load catalog if not already loaded
        if locale not in self._catalogs:
            self.logger.debug("Loading catalog for locale: %s" % locale)
            success = self.load_catalog(locale)
            self.logger.debug("Catalog load %s for locale: %s" % ("succeeded" if success else "failed", locale))
            if not success and self.strict_mode:
                raise LocaleNotFoundError("Failed to load catalog for locale: %s" % locale)

    def translate(self, msgid, catalog=None, **kwargs):
        """Translate a message.
        
        Args:
            msgid: Message ID to translate
            catalog: Optional catalog to use. If None, uses current locale's catalog
            **kwargs: Format arguments
            
        Returns:
            Translated string
            
        Raises:
            CatalogNotFoundError: If no catalog is available
        """
        if catalog is None:
            if not self._catalogs:
                raise CatalogNotFoundError("No catalogs available")
            catalog = self._catalogs.get(self._current_locale)
            if not catalog:
                raise CatalogNotFoundError("No catalog for locale: %s" % self._current_locale)

        message = catalog.get_message(msgid)
        if not message:
            return msgid

        # Handle both string and Message object returns
        msgstr = message if isinstance(message, string_types) else message.msgstr
        
        try:
            return msgstr.format(**kwargs) if kwargs else msgstr
        except KeyError as e:
            raise KeyError("Missing parameter in translation: %s" % str(e))
        except Exception:
            return msgstr

    def tr(self, text, context=None, catalog=None, **kwargs):
        """Translate text using the current locale.
        
        Args:
            text: Text to translate
            context: Optional context for the text
            catalog: Optional specific catalog to use
            **kwargs: Format arguments for the translated text
            
        Returns:
            str: Translated text or original text if no translation found
        """
        self.logger.debug("Translating text: %s", text)
        self.logger.debug("Current locale: %s", self.current_locale)
        self.logger.debug("Available catalogs: %s", list(self._catalogs.keys()))
        
        try:
            return self.translate(text, catalog, **kwargs)
        except (CatalogNotFoundError, KeyError) as e:
            self.logger.warning("Translation failed: %s", str(e))
            return text
