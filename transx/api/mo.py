#!/usr/bin/env python
"""MO file format handler for TransX."""

# Import built-in modules
import gettext
import logging
import struct
import sys

# Import local modules
from transx.constants import DEFAULT_CHARSET
from transx.api.po import POFile  # Import POFile class


# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode
    binary_type = str
else:
    text_type = str
    binary_type = bytes

logger = logging.getLogger(__name__)

def _unescape(string):
    """Unescape a string using string literal evaluation."""
    try:
        # First try to handle it as a regular string
        return eval('"""' + string + '"""', {"__builtins__": {}})
    except Exception:
        # If that fails, try to handle escapes manually
        return string.encode("raw_unicode_escape").decode("unicode_escape")

def _read_mo_file(mo_file):
    """Read a MO file and return a catalog of messages."""
    with open(mo_file, "rb") as f:
        # MO file format magic number and version
        data = f.read()
        if len(data) < 20:  # At least magic(4) + version(4) + numstrings(4) + orig_offset(4) + trans_offset(4)
            raise ValueError("Invalid MO file format: file too small")

        magic = data[:4]
        if magic == b"\x95\x04\x12\xde":  # Little endian
            version, num_strings, orig_offset, trans_offset = struct.unpack("<4I", data[4:20])
        elif magic == b"\xde\x12\x04\x95":  # Big endian
            version, num_strings, orig_offset, trans_offset = struct.unpack(">4I", data[4:20])
        else:
            raise ValueError("Invalid MO file format: wrong magic number")

        # Read string table
        catalog = {}
        for i in range(num_strings):
            # Read original string
            if orig_offset + (i + 1) * 8 > len(data):
                break
            length, offset = struct.unpack("<2I", data[orig_offset + i * 8:orig_offset + (i + 1) * 8])
            if offset + length > len(data):
                break
            msgid = data[offset:offset + length].decode("utf-8")

            # Read translation
            if trans_offset + (i + 1) * 8 > len(data):
                break
            length, offset = struct.unpack("<2I", data[trans_offset + i * 8:trans_offset + (i + 1) * 8])
            if offset + length > len(data):
                break
            msgstr = data[offset:offset + length].decode("utf-8")

            catalog[msgid] = msgstr

        # Extract metadata
        metadata = {}
        if "" in catalog:
            meta_str = catalog[""]
            for line in meta_str.split("\n"):
                if not line or ": " not in line:
                    continue
                key, val = line.split(": ", 1)
                metadata[key] = val

        return catalog, metadata

def _write_mo(fileobj, catalog, metadata):
    """Write a catalog to MO file format."""
    # Prepare metadata
    meta_str = []
    # Ensure required metadata fields are present
    if "Project-Id-Version" not in metadata:
        metadata["Project-Id-Version"] = "1.0"
    if "POT-Creation-Date" not in metadata:
        metadata["POT-Creation-Date"] = "2023-01-01 00:00+0000"
    if "PO-Revision-Date" not in metadata:
        metadata["PO-Revision-Date"] = "2023-01-01 00:00+0000"
    if "Last-Translator" not in metadata:
        metadata["Last-Translator"] = "Unknown"
    if "Language-Team" not in metadata:
        metadata["Language-Team"] = "Unknown"
    if "MIME-Version" not in metadata:
        metadata["MIME-Version"] = "1.0"
    if "Content-Type" not in metadata:
        metadata["Content-Type"] = "text/plain; charset=UTF-8"
    if "Content-Transfer-Encoding" not in metadata:
        metadata["Content-Transfer-Encoding"] = "8bit"
    if "Language" not in metadata:
        metadata["Language"] = "en_US"  # Only set default if not present in PO file

    for key, val in sorted(metadata.items()):
        meta_str.append(f"{key}: {val}")
    catalog[""] = "\n".join(meta_str) + "\n\n"  # Add two newlines for proper metadata format

    # Sort messages to ensure deterministic output
    messages = sorted(catalog.items())

    # Compute size of string table
    msgids = msgstrs = b""
    offsets = []

    # Write strings and compute offsets
    for msgid, msgstr in messages:
        # Convert strings to bytes
        if isinstance(msgid, text_type):
            msgid = msgid.encode("utf-8")
        if isinstance(msgstr, text_type):
            msgstr = msgstr.encode("utf-8")

        # Add offsets and strings
        offsets.append((len(msgids), len(msgid), len(msgstrs), len(msgstr)))
        msgids += msgid + b"\x00"
        msgstrs += msgstr + b"\x00"

    # Compute header size and string table size
    N = len(messages)

    # Compute base offsets
    keystart = 7 * 4 + 16 * len(messages)  # After header and index tables
    valuestart = keystart + len(msgids)

    # Build offset tables
    koffsets = []
    voffsets = []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    offsets = koffsets + voffsets

    # Write header
    fileobj.write(struct.pack("<I", 0x950412de))  # Magic number (LE)
    fileobj.write(struct.pack("<I", 0))           # Version
    fileobj.write(struct.pack("<I", N))           # Number of strings
    fileobj.write(struct.pack("<I", 7 * 4))       # Start of key index
    fileobj.write(struct.pack("<I", 7 * 4 + N * 8))  # Start of value index
    fileobj.write(struct.pack("<I", 0))           # Size of hash table
    fileobj.write(struct.pack("<I", 0))           # Offset of hash table

    # Write offset tables
    for offset in offsets:
        fileobj.write(struct.pack("<I", offset))

    # Write string tables
    fileobj.write(msgids)
    fileobj.write(msgstrs)

class MOFile(gettext.GNUTranslations):
    """Custom MO file handler with proper encoding support."""

    def _parse(self, fp):
        """Parse MO file with UTF-8 encoding."""
        self._charset = DEFAULT_CHARSET
        self._output_charset = DEFAULT_CHARSET
        super(MOFile, self)._parse(fp)

def compile_po_file(po_file, mo_file):
    """Compile a PO file into MO format."""
    try:
        # Load PO file using POFile class
        with POFile(po_file) as po:
            # Convert PO file to MO format
            catalog = {}
            for entry in po.get_all_entries():
                msgid = entry['msgid']
                if entry['context'] is not None:
                    # Handle context by adding context prefix
                    msgid = f"{entry['context']}\x04{msgid}"
                catalog[msgid] = entry['msgstr']

            # Write MO file
            with open(mo_file, "wb") as f:
                _write_mo(f, catalog, po.metadata)

            logger.info("Successfully compiled %s to %s", po_file, mo_file)

    except Exception as e:
        logger.error("Error compiling %s: %s", po_file, str(e))
        raise
