"""Qt integration for TransX."""
# Import future modules
from __future__ import absolute_import
from __future__ import unicode_literals

# Import built-in modules
import logging
import os


def install_qt_translator(app, translator, locale, translations_path):
    """Install Qt's own translation files.

    Args:
        app: Application instance with installTranslator method
        translator: Translator instance with load method
        locale: Locale code (e.g. 'en_US', 'ja_JP')
        translations_path: Path to translations directory

    Returns:
        bool: True if translator was installed successfully
    """
    logger = logging.getLogger(__name__)
    if not all([app, translator, locale, translations_path]):
        return False

    try:
        qm_file = os.path.join(translations_path, "qt_{}.qm".format(locale))

        if translator.load(qm_file):
            app.installTranslator(translator)
            logger.debug("Installed Qt translator for locale: %s", locale)
            return True
        else:
            logger.debug("Failed to load Qt translation file: %s", qm_file)
            return False
    except Exception as e:
        logger.error("Error installing Qt translator: %s", str(e))
        return False
