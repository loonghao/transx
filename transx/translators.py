
import sys
import abc

# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    ABC = abc.ABCMeta("ABC", (object,), {"__slots__": ()})
    text_type = unicode  # noqa: F821
else:
    ABC = abc.ABC
    text_type = str

class BaseTranslator(ABC):
    """Base class for all translators."""
    
    @abc.abstractmethod
    def translate(self, text, source_lang="auto", target_lang="en"):
        # type: (str, str, str) -> str
        """Translate the given text from source language to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code (default: auto)
            target_lang: Target language code (default: en)
            
        Returns:
            str: Translated text
        """
        pass

class DummyTranslator(BaseTranslator):
    """A dummy translator that returns the input text unchanged."""
    
    def translate(self, text, source_lang="auto", target_lang="en"):
        # type: (str, str, str) -> str
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        return text_type(text)

class GoogleTranslatorAdapter(BaseTranslator):
    """Adapter for Google Translator."""
    
    def __init__(self, translator):
        # type: (object) -> None
        self.translator = translator
    
    def translate(self, text, source_lang="auto", target_lang="en"):
        # type: (str, str, str) -> str
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        result = self.translator.translate(text_type(text))
        return text_type(result)

def create_translator(translator_type="dummy", **kwargs):
    # type: (str, **dict) -> BaseTranslator
    """Factory function to create a translator instance.
    
    Args:
        translator_type: Type of translator to create ("dummy", "google", etc.)
        **kwargs: Additional arguments to pass to the translator constructor
        
    Returns:
        BaseTranslator: An instance of the requested translator
        
    Raises:
        ValueError: If translator_type is unknown
    """
    if translator_type == "dummy":
        return DummyTranslator()
    elif translator_type == "google":
        # This requires the google_trans_new package to be installed
        try:
            from google_trans_new import google_translator
        except ImportError:
            raise ImportError(
                "google-trans-new package is required for Google translation. "
                "Install it with: pip install google-trans-new"
            )
        translator = google_translator()
        return GoogleTranslatorAdapter(translator)
    else:
        raise ValueError("Unknown translator type: {}".format(translator_type))
