#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Core translation functionality."""
# Import built-in modules
import logging
import os


try:
    # Import third-party modules
    from HTMLParser import HTMLParser
except ImportError:
    from html import unescape as html_unescape

# Import local modules
from transx.api.interpreter import InterpreterFactory
from transx.api.locale import get_system_locale
from transx.api.locale import normalize_language_code
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
from transx.internal.compat import ensure_unicode


class TransX:


    """Main translation class for handling translations.

    Example usage:
        >>> tx = TransX(locales_root='./locales', default_locale='en_US')
        >>> tx.switch_locale('ja_JP')
        >>> result = tx.tr('Open File')  # Returns Japanese translation
        >>> result = tx.tr('Settings')   # Returns Japanese translation

        # Multiple locale roots
        >>> tx = TransX(
        ...     locales_root=['./pkg_a/locales', './pkg_b/locales'],
        ...     default_locale='en_US',
        ... )

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
            locales_root: Root directory (or directories) for translation files.
                Accepts str, list[str], tuple[str, ...], or None.
                If None, defaults to './locales'.
                If a list or tuple is provided, translations from all roots are
                merged using a first-wins strategy for duplicate msgid entries.
            default_locale: Default locale to use. If None, uses system locale or falls back to 'en_US'
            strict_mode: If True, raise exceptions for missing translations. Defaults to False
            auto_compile: If True, automatically compile PO files to MO files. Defaults to True
            app_name: Optional application name for context
        """
        self.auto_compile = auto_compile
        self.app_name = app_name
        self.strict_mode = strict_mode

        # Normalize locales_root into a list of absolute paths
        self._locales_roots = self._normalize_roots(locales_root)

        # Backward-compatible: self.locales_root points to the first valid root
        self.locales_root = self._locales_roots[0] if self._locales_roots else os.path.abspath(DEFAULT_LOCALES_DIR)

        # Create context for compatibility with tests
        class Context:
            def __init__(self, parent):
                self.parent = parent
                self._default_locale = None
                self._current_locale = None
                # ``current_locale`` is read on every translation; resolve it
                # once and invalidate it whenever a locale changes.
                self._resolved_locale = None

            @property
            def default_locale(self):
                """Get default locale."""
                return self._default_locale or DEFAULT_LOCALE

            @default_locale.setter
            def default_locale(self, value):
                """Set default locale."""
                if value:
                    self._default_locale = normalize_language_code(value)
                    self._resolved_locale = None

            @property
            def current_locale(self):
                """Get current locale."""
                resolved = self._resolved_locale
                if resolved is None:
                    resolved = self._current_locale or self._default_locale or DEFAULT_LOCALE
                    self._resolved_locale = resolved
                return resolved

            @current_locale.setter
            def current_locale(self, value):
                """Set current locale."""
                if value:
                    self._current_locale = normalize_language_code(value)
                    self._resolved_locale = None

            def switch_locale(self, locale):
                """Switch to a new locale."""
                if not locale:
                    raise ValueError("Locale cannot be empty")
                self._current_locale = normalize_language_code(locale)
                self._resolved_locale = None

        self._context = Context(self)
        self._translations = {}  # {locale: gettext.GNUTranslations}
        self._catalogs = {}  # {locale: TranslationCatalog}
        # Final results of ``tr()``: {(locale, text, context, params_key): result}
        self._parameter_cache = {}
        # Formatted strings produced by ``translate()``: {(msgstr, params_key): result}
        self._format_cache = {}
        # Interpreter chains are created once per instance; they do not depend
        # on the number of parameters, so no per-count bookkeeping is needed.
        self._translation_chain = None
        self._parameter_chain = None
        self._locale_cache = {}  # {locale: {(msgid, context): translated_text}}
        # Results of the parameterless ``tr()`` fast path, keyed by locale then
        # by the source text. Kept separate from ``_locale_cache`` so a warm
        # lookup is a plain string-keyed dict hit with no tuple to build.
        self._plain_cache = {}  # {locale: {text: result}}
        # Shortcuts to the dicts of the active locale, so a lookup does not have
        # to go through the outer dicts on every single translation.
        self._active_locale = None
        self._active_cache = None
        self._active_plain = None

        # Create the first locales directory if it doesn't exist
        if not os.path.exists(self.locales_root):
            os.makedirs(self.locales_root)

        # Set default locale
        if default_locale is None:
            default_locale = get_system_locale() or DEFAULT_LOCALE

        # Set default and current locales
        self._context.default_locale = default_locale
        self._context.current_locale = default_locale

        # Load catalog for default locale
        if default_locale:
            self.load_catalog(default_locale)

    @staticmethod
    def _normalize_roots(locales_root):
        """Normalize locales_root parameter into a list of absolute paths.

        Args:
            locales_root: str, list, tuple, or None

        Returns:
            list[str]: List of absolute paths to locale root directories.
        """
        if locales_root is None:
            return [os.path.abspath(DEFAULT_LOCALES_DIR)]

        if isinstance(locales_root, (list, tuple)):
            roots = []
            for path in locales_root:
                abs_path = os.path.abspath(path)
                if abs_path not in roots:
                    roots.append(abs_path)
            return roots if roots else [os.path.abspath(DEFAULT_LOCALES_DIR)]

        # Single string
        return [os.path.abspath(locales_root)]

    @property
    def locales_roots(self):
        """Get the list of all locale root directories.

        Returns:
            list[str]: All resolved locale root paths.
        """
        return list(self._locales_roots)

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

        locale = normalize_language_code(locale)
        if locale == self._context.current_locale:
            return True

        # Try to load catalog if needed
        needs_catalog = locale not in self._catalogs
        if needs_catalog and not self.load_catalog(locale) and self.strict_mode:
            return False

        # Create empty catalog for non-strict mode if needed
        if needs_catalog and locale not in self._catalogs:
            self._catalogs[locale] = TranslationCatalog(locale=locale)

        # Update locale using context's switch_locale to handle Python 2.7 property refresh issue
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
        """Get a list of available locales from all locale roots.

        Returns:
            list: Sorted list of available locale codes (e.g. ['en_US', 'zh_CN', 'ja_JP'])
        """
        locales = set()
        for root in self._locales_roots:
            if not os.path.exists(root):
                continue
            for item in os.listdir(root):
                locale_path = os.path.join(root, item)
                messages_path = os.path.join(locale_path, "LC_MESSAGES")
                if os.path.isdir(locale_path) and os.path.exists(messages_path):
                    po_file = os.path.join(messages_path, DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)
                    mo_file = os.path.join(messages_path, DEFAULT_MESSAGES_DOMAIN + MO_FILE_EXTENSION)
                    if os.path.exists(po_file) or os.path.exists(mo_file):
                        locales.add(item)
        return sorted(locales)

    def _locale_dict(self, locale):
        """Return the per-locale translation cache, creating it if needed.

        Args:
            locale (str): Locale whose cache should be returned

        Returns:
            dict: Mapping of ``(msgid, context)`` to translated text
        """
        if self._active_locale != locale:
            self._active_locale = locale
            cache = self._locale_cache.get(locale)
            if cache is None:
                cache = {}
                self._locale_cache[locale] = cache
            self._active_cache = cache
            plain = self._plain_cache.get(locale)
            if plain is None:
                plain = {}
                self._plain_cache[locale] = plain
            self._active_plain = plain
        return self._active_cache

    def _plain_dict(self, locale):
        """Return the per-locale cache of parameterless ``tr()`` results.

        Args:
            locale (str): Locale whose cache should be returned

        Returns:
            dict: Mapping of source text to the final translated text
        """
        if self._active_locale != locale:
            self._locale_dict(locale)
        return self._active_plain

    def _get_translation(self, msgid, context=None, locale=None):
        """Get translation for the specified msgid and context.

        Args:
            msgid (str): Message ID to translate.
            context (str, optional): Message context.
            locale (str, optional): Locale to use. Defaults to the current one.

        Returns:
            str: Translated text.
        """
        # Get from locale cache first
        if locale is None:
            locale = self.current_locale
        locale_cache = self._locale_dict(locale)

        cache_key = (msgid, context)
        result = locale_cache.get(cache_key)
        if result is not None:
            return result

        # Get from catalog
        if context:
            msgid = context + "\x04" + msgid
        catalog = self._catalogs.get(locale)
        if catalog:
            result = catalog.get_message(msgid)
            if result:
                result = self._decode_html_entities(result)
                locale_cache[cache_key] = result
                return result

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
        # Get translation
        msgstr = self._get_translation(msgid, context)
        if not msgstr:
            msgstr = msgid

        # If no parameters, return directly
        if not kwargs:
            return msgstr

        # Create cache key for parameters
        cache_key = (msgstr, self._create_params_key(kwargs))

        # Check parameter cache
        result = self._format_cache.get(cache_key)
        if result is not None:
            return result

        # Get or create the interpreter chain
        interpreter_chain = self._parameter_chain
        if interpreter_chain is None:
            interpreter_chain = InterpreterFactory.create_parameter_only_chain()
            self._parameter_chain = interpreter_chain

        try:
            # Use cached interpreter chain
            result = interpreter_chain.execute_safe(msgstr, kwargs)
            self._format_cache[cache_key] = result
            return result
        except Exception:
            return msgstr

    def tr(self, text, context=None, **kwargs):
        """Translate a text with optional parameter substitution.

        Args:
            text (str): Text to translate.
            context (str, optional): Message context for disambiguation.
            **kwargs: Parameters for string formatting.

        Returns:
            str: Translated text with parameters substituted.
        """
        locale = self.current_locale

        # Fast path: without parameters the interpreter chain can only change
        # the text if it contains a ``$``, so a catalog lookup is the answer
        # for everything else. ``context`` is excluded because the chain drops
        # it anyway. The result cache is checked before the ``$`` scan so a
        # warm lookup never has to touch the string.
        if context is None and not kwargs:
            plain = self._plain_dict(locale)
            result = plain.get(text)
            if result is not None:
                return result
            if "$" not in text:
                result = self._get_translation(text, None, locale) or text
                plain[text] = result
                return result

        # Create cache key
        cache_key = (locale, text, context, self._create_params_key(kwargs))

        # Check cache
        result = self._parameter_cache.get(cache_key)
        if result is not None:
            return result

        # Get or create interpreter chains
        translation_chain = self._translation_chain
        if translation_chain is None:
            translation_chain = InterpreterFactory.create_translation_chain(self)
            self._translation_chain = translation_chain
        parameter_chain = self._parameter_chain
        if parameter_chain is None:
            parameter_chain = InterpreterFactory.create_parameter_only_chain()
            self._parameter_chain = parameter_chain

        try:
            result = translation_chain.execute_safe(
                text, kwargs, parameter_chain.interpreters)
            self._parameter_cache[cache_key] = result
            return result
        except Exception:
            return text

    def load_catalog(self, locale):
        """Load translation catalog for the specified locale from all locale roots.

        When multiple roots are configured, translations are merged using a
        first-wins strategy: the first root that provides a translation for a
        given (msgid, context) pair is authoritative. If a later root provides
        a *different* translation for the same key, a WARNING is logged.

        Args:
            locale: Locale to load catalog for

        Returns:
            bool: True if catalog was loaded from at least one root, False otherwise

        Raises:
            LocaleNotFoundError: If locale directory not found in any root (only in strict mode)
            ValueError: If locale is None
        """
        if not locale:
            raise ValueError("Locale cannot be None")

        catalog = TranslationCatalog(locale=locale)
        # Track seen (msgid, context) -> (msgstr, root_path) for conflict detection
        seen = {}
        loaded_any = False

        for root in self._locales_roots:
            success = self._load_catalog_from_root(root, locale, catalog, seen)
            if success:
                loaded_any = True

        if loaded_any:
            self._catalogs[locale] = catalog
            return True

        msg = "No translation files found for locale '%s' in any root" % locale
        if self.strict_mode:
            raise LocaleNotFoundError(msg)
        self.logger.debug(msg)
        return False

    def _load_catalog_from_root(self, root, locale, catalog, seen):
        """Load translations from a single root into the catalog.

        Args:
            root: Locale root directory path
            locale: Locale code
            catalog: TranslationCatalog to merge into
            seen: Dict mapping (msgid, context) -> (msgstr, root_path) for conflict detection

        Returns:
            bool: True if translations were loaded from this root
        """
        locale_dir = os.path.join(root, locale, "LC_MESSAGES")
        if not os.path.exists(locale_dir):
            self.logger.debug("Locale directory not found: %s" % locale_dir)
            return False

        mo_file = os.path.join(locale_dir, DEFAULT_MESSAGES_DOMAIN + MO_FILE_EXTENSION)
        po_file = os.path.join(locale_dir, DEFAULT_MESSAGES_DOMAIN + PO_FILE_EXTENSION)

        self.logger.debug("Checking MO file: %s" % mo_file)
        self.logger.debug("Checking PO file: %s" % po_file)

        try:
            if os.path.exists(mo_file):
                mo = MOFile(mo_file, locale)
                for raw_msgid, message in mo.translations.items():
                    if raw_msgid:  # Skip metadata
                        # MO files may encode context as "context\x04msgid"
                        if "\x04" in raw_msgid:
                            ctx, msgid = raw_msgid.split("\x04", 1)
                        else:
                            ctx, msgid = None, raw_msgid
                        self._merge_message(catalog, seen, msgid, message.msgstr, ctx, root, locale)
                return True

            elif os.path.exists(po_file):
                po = POFile(po_file)
                po.load()

                for _key, message in po.translations.items():
                    if message.msgid:  # Skip metadata
                        self._merge_message(catalog, seen, message.msgid, message.msgstr, message.context, root, locale)

                if self.auto_compile:
                    try:
                        compile_po_file(po_file, mo_file)
                        self.logger.debug("Compiled PO file to MO: %s" % mo_file)
                    except Exception as e:
                        self.logger.warning("Failed to compile PO to MO: %s" % str(e))
                return True

        except Exception as e:
            msg = "Failed to load catalog from root '%s': %s" % (root, str(e))
            if self.strict_mode:
                raise CatalogNotFoundError(msg)
            self.logger.debug(msg)
            return False

        self.logger.debug("No translation files found in '%s' for locale: %s" % (root, locale))
        return False

    @staticmethod
    def _decode_html_entities(text):
        """Decode HTML entities in translation texts."""
        if not text:
            return text
        try:
            text = ensure_unicode(text)
            if "html_unescape" in globals():
                return html_unescape(text)
            return HTMLParser().unescape(text)
        except Exception:
            return text


    def _merge_message(self, catalog, seen, msgid, msgstr, context, root, locale):
        """Merge a single translation message into the catalog with conflict detection.

        Uses first-wins strategy: the first root providing a (msgid, context) pair
        is authoritative. Conflicting translations from later roots are logged as warnings.

        Args:
            catalog: TranslationCatalog to merge into
            seen: Dict mapping (msgid, context) -> (msgstr, root_path)
            msgid: Message ID (plain, without context prefix)
            msgstr: Translated string
            context: Optional message context
            root: Root path this message came from
            locale: Locale code (for log messages)
        """
        msgstr = self._decode_html_entities(msgstr)
        key = (msgid, context)


        if key in seen:
            existing_msgstr, existing_root = seen[key]
            if existing_msgstr != msgstr:
                self.logger.warning(
                    "Duplicate msgid conflict for locale '%s':\n"
                    "  msgid   : '%s'\n"
                    "  context : '%s'\n"
                    "  kept    : '%s'  (from '%s')\n"
                    "  ignored : '%s'  (from '%s')",
                    locale, msgid, context,
                    existing_msgstr, existing_root,
                    msgstr, root,
                )
            # First-wins: do not overwrite
            return

        seen[key] = (msgstr, root)

        # Build composite key matching _get_translation's lookup pattern:
        # _get_translation prepends "context\x04" and calls get_message without context.
        # So we store with the composite msgid and no separate context parameter.
        if context:
            composite_msgid = context + "\x04" + msgid
        else:
            composite_msgid = msgid
        catalog.add_message(composite_msgid, msgstr)

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
        msgstr = self._decode_html_entities(msgstr)
        self._catalogs[self._context.current_locale].add_message(msgid, msgstr)

    #: Types that can go into a cache key unchanged - checked first because a
    #: parameter set with many entries pays this check once per entry.
    _ATOMIC_TYPES = (str, bytes, int, float, bool, type(None))

    @staticmethod
    def _freeze(value):
        """Convert a parameter value into a hashable, stable representation."""
        if isinstance(value, TransX._ATOMIC_TYPES):
            return value
        if isinstance(value, dict):
            return tuple(sorted((k, TransX._freeze(v)) for k, v in value.items()))
        if isinstance(value, (set, frozenset)):
            # Set iteration order is not stable across processes, so sort by a
            # total, type-agnostic key to keep the cache key deterministic.
            return tuple(sorted((TransX._freeze(v) for v in value), key=repr))
        if isinstance(value, (list, tuple)):
            return tuple(TransX._freeze(v) for v in value)
        return value

    def _create_params_key(self, params):
        """Create a hashable cache key for a set of formatting parameters.

        The previous implementation collapsed the parameters into a single
        ``hash()`` value, which both costs a full traversal of nested values
        and can collide. Returning the frozen structure itself keeps the key
        exact.

        Args:
            params (dict): Parameters for string formatting

        Returns:
            tuple or None: Cache key, or None when there are no parameters
        """
        if not params:
            return None
        return tuple(sorted((key, self._freeze(value)) for key, value in params.items()))

    def _create_cache_key(self, template, params):
        """Create a cache key for template and parameters.

        Args:
            template (str): Template string
            params (dict): Parameters for string formatting

        Returns:
            tuple: Cache key
        """
        return template, self._create_params_key(params)
