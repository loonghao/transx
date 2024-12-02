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
        print("Error: POT file not found: {0}".format(pot_file))
        return

    # Update language catalogs
    languages = ["zh_CN", "ja", "ko", "fr", "es_ES"]
    locales_dir = os.path.abspath("locales")
    
    with PotExtractor(pot_file=pot_file) as extractor:
        extractor.create_language_catalogs(languages, locales_dir)
        print("Language catalogs updated.")


if __name__ == "__main__":
    update_translations()
