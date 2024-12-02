# Import built-in modules
import abc
import logging
import os
import sys

# Import local modules
from transx.api.po import POFile
from transx.api.pot import PotExtractor
from transx.api.message import Message
from transx.constants import DEFAULT_LOCALE
from transx.constants import INVALID_LANGUAGE_CODE_ERROR
from transx.constants import LANGUAGE_CODES
from transx.constants import LANGUAGE_CODE_ALIASES
from transx.api.locale import normalize_locale

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    ABC = abc.ABCMeta("ABC", (object,), {"__slots__": ()})
    text_type = unicode
else:
    ABC = abc.ABC
    text_type = str


class Translator(ABC):
    """Base class for translation API."""

    @abc.abstractmethod
    def translate(self, text, source_lang="auto", target_lang="en"):
        """Translate text from source language to target language."""

class DummyTranslator(Translator):
    """A dummy translator that returns the input text unchanged."""

    def translate(self, text, source_lang="auto", target_lang="en"):
        return text

def ensure_dir(path):
    """Ensure directory exists, create it if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)


def translate_po_file(po_file_path, translator=None):
    """Translate a PO file using the specified translator.

    Args:
        po_file_path (str): Path to the PO file
        translator (Translator, optional): Translator instance to use
    """
    logger = logging.getLogger(__name__)
    if translator is None:
        translator = DummyTranslator()

    logger.info("Translating PO file: %s", po_file_path)

    with POFile(po_file_path) as po:
        # Get target language and normalize
        lang_dir = os.path.basename(os.path.dirname(os.path.dirname(po_file_path)))
        lang = normalize_locale(lang_dir)
        logger.info("Target language: %s", lang)

        # Get all entries and count untranslated ones
        entries = po.get_all_entries()
        logger.info("Total translation entries: %d", len(entries))

        # Translate untranslated entries
        untranslated_count = 0
        for entry in entries:
            if not entry['msgstr']:  # Only translate empty entries
                untranslated_count += 1
                try:
                    logger.debug("Translating: %s", entry['msgid'])
                    translation = translator.translate(entry['msgid'], target_lang=lang)
                    # Create a new Message object with the translation
                    message = Message(msgid=entry['msgid'], msgstr=translation, context=entry['context'])
                    po.translations[(entry['msgid'], entry['context'])] = message
                except Exception as e:
                    logger.error("Failed to translate '%s': %s", entry['msgid'], str(e))

        if untranslated_count > 0:
            logger.info("Translated %d entries", untranslated_count)
            po.save()
        else:
            logger.info("No untranslated entries found")

def translate_pot_file(pot_file_path, languages, output_dir=None, translator=None):
    """Generate and translate PO files from a POT file for specified languages.

    Args:
        pot_file_path (str): Path to the POT file
        languages (list): List of language codes to generate (e.g. ['en', 'zh_CN'])
        output_dir (str, optional): Output directory for PO files
        translator (Translator, optional): Translator instance to use
    """
    logger = logging.getLogger(__name__)
    if translator is None:
        translator = DummyTranslator()

    if output_dir is None:
        output_dir = os.path.dirname(pot_file_path)

    # Ensure POT file exists
    if not os.path.exists(pot_file_path):
        raise FileNotFoundError(f"POT file not found: {pot_file_path}")

    # Ensure output directory exists
    ensure_dir(output_dir)

    # Load POT file and process translations
    with PotExtractor(pot_file=pot_file_path) as pot:
        # Normalize language codes and create PO files
        for lang in languages:
            lang = normalize_locale(lang)
            logger.info("Processing language: %s", lang)

            # Create language directory structure
            lang_dir = os.path.join(output_dir, lang, "LC_MESSAGES")
            ensure_dir(lang_dir)

            # Generate PO file path
            po_file = os.path.join(lang_dir, os.path.basename(pot_file_path).replace(".pot", ".po"))

            # Create and translate PO file
            logger.info("Generating PO file: %s", po_file)
            pot.create_language_catalogs([lang], output_dir)
            translate_po_file(po_file, translator)
