"""Update translation files."""
# Import built-in modules
import os

# Import local modules
from transx.api.pot import PotExtractor


def update_translations():
    """Update translation files for all languages."""
    # Set file paths
    pot_file = os.path.join(os.path.abspath("locales"), "messages.pot")
    if not os.path.exists(pot_file):
        print(f"Error: POT file not found: {pot_file}")
        return

    # Create POT extractor and load
    extractor = PotExtractor(pot_file)
    extractor.messages.load(pot_file)

    # Generate language files
    languages = ["zh_CN", "ja", "ko", "fr", "es_ES"]
    locales_dir = os.path.abspath("locales")
    extractor.generate_language_files(languages, locales_dir)
    print("Language files updated.")

if __name__ == "__main__":
    update_translations()
