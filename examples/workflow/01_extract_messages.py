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
    os.makedirs(os.path.abspath("locales"), exist_ok=True)

    # Create POT extractor
    extractor = PotExtractor(pot_file)

    # Scan source code files
    source_files = [os.path.abspath("demo.py")]  # Add all source files that need to be scanned
    for file in source_files:
        if os.path.exists(file):
            print(f"Scanning {file} for translatable messages...")
            extractor.scan_file(file)
        else:
            print(f"Warning: {file} does not exist")

    # Save POT file and set project information
    extractor.save_pot(
        project="Workflow Demo",
        version="1.0",
        copyright_holder="TransX",
        bugs_address="transx@example.com"
    )



if __name__ == "__main__":
    extract_messages()
