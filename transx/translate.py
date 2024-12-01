import os
import sys
import abc
import logging

# Import local modules
from transx.formats.po import POFile
from transx.constants import (
    LANGUAGE_CODES,
    LANGUAGE_CODE_ALIASES,
    INVALID_LANGUAGE_CODE_ERROR,
    DEFAULT_LOCALE
)

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    ABC = abc.ABCMeta("ABC", (object,), {"__slots__": ()})
    text_type = unicode  # noqa: F821
else:
    ABC = abc.ABC
    text_type = str

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class Translator(ABC):
    """Base class for translation API."""
    
    @abc.abstractmethod
    def translate(self, text, source_lang="auto", target_lang="en"):
        """Translate text from source language to target language."""
        pass

class DummyTranslator(Translator):
    """A dummy translator that returns the input text unchanged."""
    
    def translate(self, text, source_lang="auto", target_lang="en"):
        return text

def ensure_dir(path):
    """Ensure directory exists, create it if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def normalize_locale(locale):
    """Normalize language code format.

    Convert various language code formats to standard format (e.g., 'zh-CN' -> 'zh_CN').
    Supported formats include:
    - ISO 639-1 language codes (e.g., 'en')
    - ISO 3166-1 country/region codes (e.g., 'zh_CN')
    - Common non-standard codes (e.g., 'cn' -> 'zh_CN')
    
    Args:
        locale (str): Language code (e.g., 'zh-CN', 'zh_cn', 'zh')
        
    Returns:
        str: Normalized language code (e.g., 'zh_CN')
        
    Raises:
        ValueError: If an invalid language code is provided

    """
    if not locale:
        return DEFAULT_LOCALE
        
    # Remove all whitespace and convert to lowercase
    normalized = locale.strip().lower()
    
    # Check if it's a standard code
    if normalized in LANGUAGE_CODES:
        return normalized
    
    # Check if it's an alias
    if normalized in LANGUAGE_CODE_ALIASES:
        return LANGUAGE_CODE_ALIASES[normalized]
    
    # If the code contains a separator, try to normalize the format
    if "-" in normalized or "_" in normalized:
        parts = normalized.replace("-", "_").split("_")
        if len(parts) == 2:
            lang, region = parts
            # Build a possible standard code
            possible_code = "{}_{}".format(lang, region.upper())
            if possible_code in LANGUAGE_CODES:
                return possible_code
    
    # If no matching code is found, generate an error message
    valid_codes = "\n".join(
        "- {} ({}): {}".format(
            code, 
            name, 
            ", ".join(["'" + a + "'" for a in aliases])
        )
        for code, (name, aliases) in sorted(LANGUAGE_CODES.items())
    )
    
    raise ValueError(
        INVALID_LANGUAGE_CODE_ERROR.format(
            code=locale,
            valid_codes=valid_codes
        )
    )

def translate_po_file(po_file_path, translator=None):
    """Translate a PO file using the specified translator.
    
    Args:
        po_file_path (str): Path to the PO file
        translator (Translator, optional): Translator instance to use
    """
    if translator is None:
        translator = DummyTranslator()
    
    # Ensure directory exists
    po_dir = os.path.dirname(po_file_path)
    ensure_dir(po_dir)
    
    logger.info("Loading PO file: %s", po_file_path)
    po = POFile(po_file_path)
    po.load()
    
    # Get target language and normalize
    lang_dir = os.path.basename(os.path.dirname(os.path.dirname(po_file_path)))
    lang = normalize_locale(lang_dir)
    logger.info("Target language: %s", lang)
    
    # Print the number of current translation entries
    logger.info("Total translation entries: %d", len(po.translations))
    
    # Iterate over all untranslated entries
    untranslated_count = 0
    for (msgid, context), msgstr in po.translations.items():
        if not msgstr:  # Only translate empty entries
            untranslated_count += 1
            try:
                logger.debug("Translating: %s", msgid)
                translation = translator.translate(msgid, target_lang=lang)
                po.translations[(msgid, context)] = translation
            except Exception as e:
                logger.error("Failed to translate '%s': %s", msgid, str(e))
    
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
    if translator is None:
        translator = DummyTranslator()
    
    if output_dir is None:
        output_dir = os.path.dirname(pot_file_path)
    
    # Ensure POT file exists
    if not os.path.exists(pot_file_path):
        raise FileNotFoundError("POT file not found: {}".format(pot_file_path))
    
    # Ensure output directory exists
    ensure_dir(output_dir)
    
    # Load POT file
    logger.info("Loading POT file: %s", pot_file_path)
    pot = POFile(pot_file_path)
    pot.load()
    
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
        pot.generate_language_files([lang], output_dir)
        translate_po_file(po_file, translator)
