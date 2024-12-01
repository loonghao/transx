"""Message extraction utilities."""
import os
import re
from datetime import datetime
from transx.constants import (
    DEFAULT_ENCODING,
    METADATA_KEYS,
    DEFAULT_METADATA
)
import logging

logger = logging.getLogger(__name__)

class PotExtractor:
    """Extract translatable messages from source files."""
    
    def __init__(self, output_file):
        """Initialize a new POT extractor.
        
        Args:
            output_file (str): Path to output POT file
        """
        self.output_file = output_file
        self.messages = set()  # Set of (msgid, context) tuples
        
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
        logger.debug("Extracted messages from %s: %s", filepath, self.messages)
    
    def save_pot(self):
        """Save extracted messages to POT file."""
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        with open(self.output_file, "w", encoding=DEFAULT_ENCODING) as f:
            # Write header
            f.write('msgid ""\nmsgstr ""\n')
            metadata = DEFAULT_METADATA.copy()
            metadata[METADATA_KEYS["PO_REVISION_DATE"]] = datetime.now().strftime("%Y-%m-%d %H:%M%z")
            
            for key, value in metadata.items():
                f.write('"{0}: {1}\\n"\n'.format(key, value))
            f.write("\n")
            
            # Write messages
            for msgid, context in sorted(self.messages):
                if context:
                    f.write('msgctxt "{0}"\n'.format(context))
                f.write('msgid "{0}"\n'.format(msgid))
                f.write('msgstr ""\n\n')
        
        # Log saved messages
        logger.debug("Saved messages to %s: %s", self.output_file, self.messages)
