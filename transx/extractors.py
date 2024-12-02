"""Message extraction utilities."""
# Import built-in modules
import logging
import os
import re
import time

# Import local modules
from transx.constants import DEFAULT_ENCODING
from transx.constants import DEFAULT_METADATA
from transx.constants import METADATA_KEYS


class PotExtractor:
    """Extract translatable messages from source files."""

    def __init__(self, output_file):
        """Initialize a new POT extractor.

        Args:
            output_file (str): Path to output POT file
        """
        self.output_file = output_file
        self.messages = set()  # Set of (msgid, context) tuples
        self.logger = logging.getLogger(__name__)

    def scan_file(self, filepath):
        """Scan a file for translatable messages.

        Args:
            filepath (str): Path to file to scan
        """
        with open(filepath, encoding=DEFAULT_ENCODING) as f:
            content = f.read()

        # Find all tr() calls
        tr_pattern = r'tr\(["\'](.+?)["\'](,\s*context=["\'](.+?)["\'])?'
        matches = re.finditer(tr_pattern, content)

        for match in matches:
            msgid = match.group(1)
            context = match.group(3) if match.group(2) else None
            self.messages.add((msgid, context))

        # Log extracted messages
        self.logger.debug("Extracted messages from %s: %s", filepath, self.messages)

    def save_pot(self):
        """Save extracted messages to POT file."""
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        with open(self.output_file, "w", encoding=DEFAULT_ENCODING) as f:
            # Write header
            f.write('msgid ""\nmsgstr ""\n')
            metadata = DEFAULT_METADATA.copy()
            metadata[METADATA_KEYS["PO_REVISION_DATE"]] = time.strftime("%Y-%m-%d %H:%M+0000", time.gmtime())

            for key, value in metadata.items():
                f.write(f'"{key}: {value}\\n"\n')
            f.write("\n")

            # Write messages
            for msgid, context in sorted(self.messages):
                if context:
                    f.write(f'msgctxt "{context}"\n')
                f.write(f'msgid "{msgid}"\n')
                f.write('msgstr ""\n\n')

        # Log saved messages
        self.logger.debug("Saved messages to %s: %s", self.output_file, self.messages)
