#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Core translation functionality."""

# Import built-in modules
import os
from string import Template

# Import local modules
from transx.api.interpreter import InterpreterFactory
from transx.api.locale import get_system_locale
from transx.api.mo import MOFile
from transx.api.mo import compile_po_file
from transx.api.po import POFile
from transx.api.translation_catalog import TranslationCatalog
from transx.constants import DEFAULT_LOCALE
from transx.constants import DEFAULT_LOCALES_DIR
from transx.constants import DEFAULT_MESSAGES_DOMAIN
from transx.constants import MO_FILE_EXTENSION
from transx.constants import PO_FILE_EXTENSION
from transx.exceptions import CatalogNotFoundError
from transx.exceptions import LocaleNotFoundError
from transx.internal.compat import string_types
from transx.internal.filesystem import read_file
from transx.internal.logging import get_logger


class TransX:
    """Main translation class for handling translations."""

    # Class-level logger
    logger = get_logger(__name__)

    def __init__(self, locales_root=None, default_locale=None, strict_mode=False, auto_compile=True):
        """Initialize translator.

        Args:
            locales_root: Root directory for translation files. Defaults to './locales'
            default_locale: Default locale to use. If None, uses system locale or falls back to 'en_US'
            strict_mode: If True, raise exceptions for missing translations. Defaults to False
            auto_compile: If True, automatically compile PO files to MO files. Defaults to True
        """
        self.auto_compile = auto_compile
        self.locales_root = os.path.abspath(locales_root or DEFAULT_LOCALES_DIR)

        # Try to get system locale if default_locale is not specified
        if default_locale is None:
            default_locale = get_system_locale() or DEFAULT_LOCALE
            self.logger.debug("Using system locale: %s", default_locale)

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
                content = read_file(mo_file, binary=True)
                mo = MOFile()
                mo._parse(content)
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

        # Load catalog if not already loaded
        if locale not in self._catalogs:
            self.logger.debug("Loading catalog for locale: %s" % locale)
            success = self.load_catalog(locale)
            self.logger.debug("Catalog load %s for locale: %s" % ("succeeded" if success else "failed", locale))
            if not success and self.strict_mode:
                raise LocaleNotFoundError("Failed to load catalog for locale: %s" % locale)

        # Set the locale after successfully loading catalog
        self._current_locale = locale

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
        # Use a unique marker that's unlikely to appear in normal text
        DOLLAR_MARKER = "__DOUBLE_DOLLAR_SIGN_8A7B6C5D__"

        try:
            if catalog is None:
                if not self._catalogs:
                    raise CatalogNotFoundError("No catalogs available")
                catalog = self._catalogs.get(self.current_locale)
                if catalog is None:
                    raise CatalogNotFoundError(
                        "No catalog found for locale: %s" % self.current_locale)

            # Get translation
            message = catalog.get_message(msgid)
            if not message:
                return msgid

            # Handle both string and Message object returns
            msgstr = message if isinstance(message, string_types) else message.msgstr
            if not msgstr:
                return msgid

            # First handle parameter substitution using Template
            # Temporarily replace $$ with the marker
            msgstr = msgstr.replace(u"$$", DOLLAR_MARKER)
            template = Template(msgstr)
            result = template.safe_substitute(kwargs) if kwargs else msgstr
            # Handle environment variables
            result = os.path.expandvars(result)
            # Restore $$ last
            result = result.replace(DOLLAR_MARKER, u"$$")
            return result

        except Exception as e:
            self.logger.warning("Translation substitution failed: %s", str(e))
            return msgid

    def tr(self, text, **kwargs):
        """Translate a text with optional parameter substitution.

        Args:
            text (str): Text to translate.
            **kwargs: Parameters for string formatting.

        Returns:
            str: Translated text with parameters substituted.
        """
        # Create interpreter chain
        executor = InterpreterFactory.create_translation_chain(self)
        fallback_chain = InterpreterFactory.create_parameter_only_chain()

        return executor.execute_safe(text, kwargs, fallback_chain.interpreters)
