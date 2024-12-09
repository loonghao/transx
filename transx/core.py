#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Core translation functionality."""
# Import built-in modules
import logging
import os

# Import local modules
from transx.api.interpreter import InterpreterFactory
from transx.api.locale import get_system_locale
from transx.api.locale import normalize_language_code
from transx.api.mo import MOFile
from transx.api.mo import compile_po_file
from transx.api.po import POFile
from transx.api.translation_catalog import TranslationCatalog
from transx.constants import DEFAULT_CHARSET
from transx.constants import DEFAULT_LOCALE
from transx.constants import DEFAULT_LOCALES_DIR
from transx.constants import DEFAULT_MESSAGES_DOMAIN
from transx.constants import MO_FILE_EXTENSION
from transx.constants import PO_FILE_EXTENSION
from transx.exceptions import CatalogNotFoundError
from transx.exceptions import LocaleNotFoundError


class TransX:
    """Main translation class for handling translations.

    Example usage:
        >>> tx = TransX(locales_root='./locales', default_locale='en_US')
        >>> tx.switch_locale('ja_JP')
        >>> result = tx.tr('Open File')  # Returns Japanese translation
        >>> result = tx.tr('Settings')   # Returns Japanese translation

        # Qt integration
        >>> tx.register_qt_translator(
        ...     QApplication.instance(),
        ...     QTranslator(),
        ...     QLibraryInfo.location(QLibraryInfo.TranslationsPath)
        ... )
    """
    logger = logging.getLogger(__name__)

    def __init__(self, locales_root=None, default_locale=None, strict_mode=False, auto_compile=True, app_name=None):
        """Initialize translator.

        Args:
            locales_root: Root directory for translation files. Defaults to './locales'
            default_locale: Default locale to use. If None, uses system locale or falls back to 'en_US'
            strict_mode: If True, raise exceptions for missing translations. Defaults to False
            auto_compile: If True, automatically compile PO files to MO files. Defaults to True
            app_name: Optional application name for context
        """
        self.auto_compile = auto_compile
        self.locales_root = os.path.abspath(locales_root or DEFAULT_LOCALES_DIR)
        self.app_name = app_name
        self.strict_mode = strict_mode

        # Create context for compatibility with tests
        class Context:
            def __init__(self, parent):
                self.parent = parent
                self._default_locale = None
                self._current_locale = None

            @property
            def default_locale(self):
                """Get default locale."""
                return self._default_locale or DEFAULT_LOCALE

            @default_locale.setter
            def default_locale(self, value):
                """Set default locale."""
                if value:
                    self._default_locale = normalize_language_code(value)

            @property
            def current_locale(self):
                """Get current locale."""
                return self._current_locale or self.default_locale

            @current_locale.setter
            def current_locale(self, value):
                """Set current locale."""
                if value:
                    self._current_locale = normalize_language_code(value)

            def switch_locale(self, locale):
                """Switch to a new locale."""
                if not locale:
                    raise ValueError("Locale cannot be empty")
                self._current_locale = normalize_language_code(locale)

        self._context = Context(self)
        self._translations = {}  # {locale: gettext.GNUTranslations}
        self._catalogs = {}  # {locale: TranslationCatalog}

        # Create locales directory if it doesn't exist
        if not os.path.exists(self.locales_root):
            os.makedirs(self.locales_root)
            self.logger.debug("Created locales directory: %s", self.locales_root)

        # Set default locale
        if default_locale is None:
            default_locale = get_system_locale() or DEFAULT_LOCALE
            self.logger.debug("Using system locale: %s", default_locale)

        # Set default and current locales
        self._context.default_locale = default_locale
        self._context.current_locale = default_locale

        # Load catalog for default locale
        if default_locale:
            self.load_catalog(default_locale)

    @property
    def default_locale(self):
        return self._context.default_locale

    @default_locale.setter
    def default_locale(self, value):
        self._context.default_locale = value

    @property
    def current_locale(self):
        return self._context.current_locale

    @current_locale.setter
    def current_locale(self, value):
        self._context.current_locale = value

    @property
    def context(self):
        """Get the context object.

        Returns:
            Context: The context object
        """
        return self._context

    def switch_locale(self, locale):
        """Switch to a new locale and load its translations.

        Args:
            locale: Locale to switch to

        Returns:
            bool: True if switch was successful

        Raises:
            ValueError: If locale is empty
            LocaleNotFoundError: If locale is not found
        """
        if not locale:
            raise ValueError("Locale cannot be empty")

        locale =  normalize_language_code(locale)

        # If same locale, return True
        if locale == self._context.current_locale:
            return True

        # Load catalog if not already loaded
        if locale not in self._catalogs and not self.load_catalog(locale) and self.strict_mode:
            return False

        # Update current locale only (not default)
        self._context.switch_locale(locale)

        return True

    def register_qt_translator(self, app, translator, translations_path):
        """Register Qt's own translator.

        Args:
            app: Qt application instance with installTranslator method
            translator: Translator instance with load method
            translations_path: Path to translations directory

        Returns:
            bool: True if translator was installed successfully
        """
        from .extensions.qt import install_qt_translator
        return install_qt_translator(
            app,
            translator,
            self.current_locale,
            translations_path
        )

    @property
    def available_locales(self):
        """Get a list of available locales.

        Returns:
            list: List of available locale codes (e.g. ['en_US', 'zh_CN', 'ja_JP'])
        """
        locales = []
        if os.path.exists(self.locales_root):
            for item in os.listdir(self.locales_root):
                locale_path = os.path.join(self.locales_root, item)
                messages_path = os.path.join(locale_path, "LC_MESSAGES")
                if os.path.isdir(locale_path) and os.path.exists(messages_path):
                    po_file = os.path.join(messages_path, DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
                    mo_file = os.path.join(messages_path, DEFAULT_MESSAGES_DOMAIN + MO_FILE_EXTENSION)
                    if os.path.exists(po_file) or os.path.exists(mo_file):
                        locales.append(item)
        return sorted(locales)

    def _get_translation(self, msgid, context=None):
        """Get translation for the specified msgid and context.

        Args:
            msgid (str): Message ID to translate.
            context (str, optional): Message context.

        Returns:
            str: Translated text.
        """
        if context:
            msgid = context + "\x04" + msgid
        catalog = self._catalogs.get(self.current_locale)
        if catalog:
            return catalog.get_message(msgid)
        return None

    def translate(self, msgid, context=None, **kwargs):
        """Translate a message with optional context and parameter substitution.

        Args:
            msgid (str): Message ID to translate.
            context (str, optional): Message context.
            **kwargs: Parameters for string formatting.

        Returns:
            str: Translated text with parameters substituted.
        """
        try:
            # Get translation
            msgstr = self._get_translation(msgid, context)
            if not msgstr:
                msgstr = msgid

            # If we have kwargs, use parameter-only chain
            if kwargs:
                executor = InterpreterFactory.create_parameter_only_chain()
                return executor.execute_safe(msgstr, kwargs)

            return msgstr

        except Exception as e:
            self.logger.warning("Translation substitution failed: %s", str(e))
            return msgid

    def tr(self, text, context=None, **kwargs):
        """Translate a text with optional parameter substitution.

        Args:
            text (str): Text to translate.
            context (str, optional): Message context for disambiguation.
            **kwargs: Parameters for string formatting.

        Returns:
            str: Translated text with parameters substituted.
        """
        # Create interpreter chain
        executor = InterpreterFactory.create_translation_chain(self)
        fallback_chain = InterpreterFactory.create_parameter_only_chain()

        return executor.execute_safe(text, kwargs, fallback_chain.interpreters)

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
        if not locale:
            raise ValueError("Locale cannot be None")

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

        try:
            if os.path.exists(mo_file):
                # Use optimized MOFile reader
                mo = MOFile(mo_file, locale)
                catalog = TranslationCatalog(
                    locale=locale,
                    charset=mo.metadata.get("Content-Type", "").split("charset=")[-1] or DEFAULT_CHARSET
                )

                # Add all translations
                for msgid, message in mo.translations.items():
                    if msgid:  # Skip metadata
                        catalog.add_message(msgid, message.msgstr)

                self._catalogs[locale] = catalog
                return True

            elif os.path.exists(po_file):
                # Load PO file
                po = POFile(po_file)
                po.load()

                catalog = TranslationCatalog(
                    locale=locale,
                    charset=po.metadata.get("Content-Type", "").split("charset=")[-1] or DEFAULT_CHARSET
                )

                # Add all translations
                for _key, message in po.translations.items():
                    if message.msgid:  # Skip metadata
                        catalog.add_message(message.msgid, message.msgstr, message.context)

                self._catalogs[locale] = catalog

                if self.auto_compile:
                    # Try to compile PO to MO for better performance
                    try:
                        compile_po_file(po_file, mo_file)
                        self.logger.debug("Compiled PO file to MO: %s" % mo_file)
                    except Exception as e:
                        self.logger.warning("Failed to compile PO to MO: %s" % str(e))
                return True

        except Exception as e:
            msg = "Failed to load catalog: %s" % str(e)
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
        if self._context.current_locale not in self._catalogs:
            self._catalogs[self._context.current_locale] = TranslationCatalog(locale=self._context.current_locale)
        self._catalogs[self._context.current_locale].add_message(msgid, msgstr)
