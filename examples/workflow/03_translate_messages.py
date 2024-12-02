#!/usr/bin/env python
"""Example of using transx with deep_translator for automatic translation."""


# Import built-in modules
import os
import sys

# Import third-party modules
from deep_translator import GoogleTranslator

# Import local modules
from transx.translate import Translator
from transx.translate import translate_pot_file


class DeepGoogleTranslator(Translator):
    """Translator implementation using deep_translator library."""

    def __init__(self):
        # Map standard language codes to deep_translator supported codes
        self.language_code_map = {
            "zh_CN": "zh-CN",
            "ja_JP": "ja",
            "ko_KR": "ko",
            "fr_FR": "fr",
            "es_ES": "es"
        }

    def translate(self, text, source_lang="auto", target_lang="en"):
        """Translate text using Google Translate API via deep_translator.

        Args:
            text (str): Text to translate
            source_lang (str): Source language code (default: auto)
            target_lang (str): Target language code (default: en)

        Returns:
            str: Translated text
        """
        # Convert language code to deep_translator supported format
        target_lang = self.language_code_map.get(target_lang, target_lang.split("_")[0].lower())
        print(f"Deep translator target language: {target_lang}")

        try:
            return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        except Exception as e:
            print(f"Translation error: {e!s}. Retrying...")
            # Retry once
            return GoogleTranslator(source=source_lang, target=target_lang).translate(text)


def ensure_example_files():
    """Ensure example files and directories exist."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    locale_dir = os.path.join(current_dir, "locales")

    # Create locale directory if not exists
    if not os.path.exists(locale_dir):
        os.makedirs(locale_dir)

    # Create example POT file if not exists
    pot_file = os.path.join(locale_dir, "messages.pot")
    if not os.path.exists(pot_file):
        with open(pot_file, "w", encoding="utf-8") as f:
            f.write("""msgid ""
msgstr ""
"Project-Id-Version: Example\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2023-01-01 00:00+0000\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

msgid "Hello, World!"
msgstr ""

msgid "Welcome to our application."
msgstr ""

msgid "Please select a language:"
msgstr ""

msgid "Settings"
msgstr ""

msgid "Help"
msgstr ""
""")

    return locale_dir


def main():
    try:
        # Ensure example files exist
        locale_dir = ensure_example_files()

        # Create translator instance
        translator = DeepGoogleTranslator()


        # Example 2: Generate and translate PO files for multiple languages from POT
        pot_file = os.path.join(locale_dir, "messages.pot")
        languages = ["zh_CN", "ja_JP", "ko_KR", "fr_FR", "es_ES"]
        print(f"\nGenerating and translating PO files for languages: {languages}")
        translate_pot_file(
            pot_file,
            languages,
            output_dir=locale_dir,
            translator=translator
        )

    except Exception as e:
        print(f"Error: {e!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
