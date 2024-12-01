#!/usr/bin/env python
"""MO file format handler for TransX."""

# Import built-in modules
import struct
import logging
import sys


# Python 2 and 3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode  # noqa: F821
    binary_type = str
else:
    text_type = str
    binary_type = bytes

logger = logging.getLogger(__name__)

def _unescape(string):
    """Unescape a string using string literal evaluation."""
    try:
        # First try to handle it as a regular string
        return eval('"""' + string + '"""')
    except Exception:
        # If that fails, try to handle escapes manually
        return string.encode("raw_unicode_escape").decode("unicode_escape")

def _read_po_file(po_file):
    """Read a PO file and return a catalog of messages."""
    catalog = {}
    metadata = {}
    current_msgid = []
    current_msgstr = []
    current_msgctxt = None
    
    def _store_current():
        if current_msgid:
            msgid = "".join(current_msgid)
            if not msgid:  # Metadata
                msgstr = "".join(current_msgstr)
                for item in msgstr.split("\\n"):
                    if not item:
                        continue
                    try:
                        key, val = item.split(":", 1)
                        metadata[key.strip()] = val.strip()
                    except ValueError:
                        continue
            else:
                key = msgid
                if current_msgctxt:
                    key = current_msgctxt + "\x04" + msgid
                catalog[key] = "".join(current_msgstr)
    
    with open(po_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if line.startswith('msgctxt "'):
                _store_current()
                current_msgctxt = _unescape(line[9:-1])
                current_msgid = []
                current_msgstr = []
            elif line.startswith('msgid "'):
                _store_current()
                current_msgid = [_unescape(line[7:-1])]
                current_msgstr = []
            elif line.startswith('msgstr "'):
                current_msgstr = [_unescape(line[8:-1])]
            elif line.startswith('"'):
                if current_msgstr is not None:
                    current_msgstr.append(_unescape(line[1:-1]))
                elif current_msgid is not None:
                    current_msgid.append(_unescape(line[1:-1]))
    
    # Store the last message
    _store_current()
    
    return catalog, metadata

def _write_mo(fileobj, catalog, metadata):
    """Write a catalog to MO file format."""
    # Prepare metadata
    meta_str = []
    for key, val in sorted(metadata.items()):
        meta_str.append(f"{key}: {val}")
    catalog[""] = "\n".join(meta_str) + "\n"
    
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

def compile_po_file(po_file, mo_file):
    """Compile a PO file into MO format."""
    try:
        # Read PO file
        catalog, metadata = _read_po_file(po_file)
        
        # Write MO file
        with open(mo_file, "wb") as f:
            _write_mo(f, catalog, metadata)
        
        logger.info("Successfully compiled %s to %s", po_file, mo_file)
        
    except Exception as e:
        logger.error("Error compiling %s: %s", po_file, str(e))
        raise
