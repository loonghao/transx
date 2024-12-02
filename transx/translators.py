
# Import built-in modules
import abc
import sys


# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    ABC = abc.ABCMeta("ABC", (object,), {"__slots__": ()})
    text_type = unicode
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

class DummyTranslator(BaseTranslator):
    """A dummy translator that returns the input text unchanged."""

    def translate(self, text, source_lang="auto", target_lang="en"):
        # type: (str, str, str) -> str
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        return text_type(text)
