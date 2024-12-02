"""Extract translatable messages to POT file."""
# Import built-in modules
import os

# Import local modules
from transx.api.pot import PotExtractor


def extract_messages():
    """Extract translatable messages from source code to POT file."""
    # Set POT file path
    pot_file = os.path.join(os.path.abspath("locales"), "messages.pot")

    # Ensure locales directory exists
    if not os.path.exists(os.path.abspath("locales")):
        os.makedirs(os.path.abspath("locales"))

    # Get source files to scan
    source_files = [os.path.abspath("demo.py")]  # Add all source files that need to be scanned

    # Create POT extractor with source files
    extractor = PotExtractor(source_files=source_files, pot_file=pot_file)

    # Extract messages from all source files
    extractor.extract_messages()

    # Save POT file and set project information
    extractor.save(
        project="Workflow Demo",
        version="1.0",
        copyright_holder="TransX",
        bugs_address="transx@example.com"
    )


if __name__ == "__main__":
    extract_messages()
