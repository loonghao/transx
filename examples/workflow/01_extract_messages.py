#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract translatable messages from source files."""

# Import built-in modules

# Import third-party modules
from common import DEMO_FILE
from common import POT_FILE

# Import local modules
from transx.api.pot import PotExtractor


def extract_messages():
    """Extract messages from demo.py."""
    # Initialize extractor
    extractor = PotExtractor(
        source_files=[DEMO_FILE],
        pot_file=POT_FILE
    )

    # Extract messages
    extractor.extract_messages()

    # Save POT file with project information
    extractor.save_pot(
        project="TransX Demo",
        version="1.0",
        copyright_holder="TransX Team",
        bugs_address="transx@example.com"
    )


if __name__ == "__main__":
    extract_messages()
