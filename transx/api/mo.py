#!/usr/bin/env python
"""MO file format handler for TransX."""
# fmt: off
# isort: skip
# black: disable
# Import future modules
from __future__ import unicode_literals

# Import built-in modules
# fmt: on
import re
import struct


try:
    # Import built-in modules
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

# Import local modules
from transx.api.message import Message
from transx.api.po import POFile
from transx.constants import DEFAULT_ENCODING
from transx.internal.compat import binary_type
from transx.internal.compat import ensure_unicode
from transx.internal.compat import text_type


class MOFile(object):
    """Class representing a MO file."""

    def __init__(self, fileobj=None):
        """Initialize a new MO file handler.

        Args:
            fileobj: Optional file object to read from
        """
        self.magic = 0x950412de  # Little endian magic
        self.version = 0
        self.num_strings = 0
        self.orig_table_offset = 0
        self.trans_table_offset = 0
        self.hash_table_size = 0
        self.hash_table_offset = 0
        self.translations = OrderedDict()
        self.metadata = OrderedDict()

        if fileobj is not None:
            self._parse(fileobj)

    def _parse(self, fileobj):
        """Parse MO file format.

        See: https://www.gnu.org/software/gettext/manual/html_node/MO-Files.html
        """
        # Read header
        magic = struct.unpack("<I", fileobj.read(4))[0]
        if magic == 0xde120495:  # Big endian
            byte_order = ">"
        elif magic == 0x950412de:  # Little endian
            byte_order = "<"
        else:
            raise ValueError("Bad magic number")

        # Read version and number of strings
        version = struct.unpack(byte_order + "I", fileobj.read(4))[0]
        if version not in (0, 1):
            raise ValueError("Bad version number")

        self.version = version
        self.num_strings = struct.unpack(byte_order + "I", fileobj.read(4))[0]
        self.orig_table_offset = struct.unpack(byte_order + "I", fileobj.read(4))[0]
        self.trans_table_offset = struct.unpack(byte_order + "I", fileobj.read(4))[0]
        self.hash_table_size = struct.unpack(byte_order + "I", fileobj.read(4))[0]
        self.hash_table_offset = struct.unpack(byte_order + "I", fileobj.read(4))[0]

        # Read strings
        for i in range(self.num_strings):
            # Read original string
            fileobj.seek(self.orig_table_offset + i * 8)
            length = struct.unpack(byte_order + "I", fileobj.read(4))[0]
            offset = struct.unpack(byte_order + "I", fileobj.read(4))[0]
            fileobj.seek(offset)
            msgid = fileobj.read(length)

            # Read translation
            fileobj.seek(self.trans_table_offset + i * 8)
            length = struct.unpack(byte_order + "I", fileobj.read(4))[0]
            offset = struct.unpack(byte_order + "I", fileobj.read(4))[0]
            fileobj.seek(offset)
            msgstr = fileobj.read(length)

            # Convert to unicode
            msgid = ensure_unicode(msgid)
            msgstr = ensure_unicode(msgstr)

            # Add to translations
            message = Message(msgid=msgid, msgstr=msgstr)
            self.translations[msgid] = message

            # Parse metadata from empty msgid
            if not msgid and msgstr:
                self._parse_metadata(msgstr)

    def _parse_metadata(self, msgstr):
        """Parse metadata from msgstr."""
        if isinstance(msgstr, binary_type):
            msgstr = msgstr.decode(DEFAULT_ENCODING)
        for line in msgstr.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                key, value = line.split(":", 1)
                self.metadata[key.strip()] = value.strip()
            except ValueError:
                continue

    def _normalize_string(self, s):
        """Normalize string for writing to MO file.

        Args:
            s: String to normalize

        Returns:
            Normalized string with consistent escape sequences
        """
        if isinstance(s, text_type):
            s = s.encode(DEFAULT_ENCODING)
        return s

    def save(self, fileobj):
        """Save MO file.

        Args:
            fileobj: File object to write to
        """
        # Sort messages by msgid
        messages = sorted(self.translations.values(), key=lambda m: m.msgid)

        # Prepare data
        output_data = []
        ids_data = []
        strs_data = []

        # Add metadata if present
        if self.metadata:
            metadata_str = "\n".join("%s: %s" % (k, v) for k, v in self.metadata.items())
            messages.insert(0, Message(msgid="", msgstr=metadata_str))

        # Collect strings data
        for message in messages:
            msgid = self._normalize_string(message.msgid)
            msgstr = self._normalize_string(message.msgstr or "")  # Handle None msgstr

            # Add to data sections
            ids_data.append(msgid)
            strs_data.append(msgstr)

        # Calculate sizes and offsets
        keystart = 7 * 4 + 8 * len(messages) * 2
        valuestart = keystart + sum(len(s) + 1 for s in ids_data)  # +1 for NUL
        koffsets = []
        voffsets = []
        offset = keystart
        for msgid in ids_data:
            koffsets.append((len(msgid), offset))
            offset += len(msgid) + 1
        offset = valuestart
        for msgstr in strs_data:
            voffsets.append((len(msgstr), offset))
            offset += len(msgstr) + 1

        # Write header
        output_data.append(struct.pack("<I", self.magic))  # Magic
        output_data.append(struct.pack("<I", 0))  # Version
        output_data.append(struct.pack("<I", len(messages)))  # Number of strings
        output_data.append(struct.pack("<I", 7 * 4))  # Offset of table with original strings
        output_data.append(struct.pack("<I", 7 * 4 + 8 * len(messages)))  # Offset of table with translation strings
        output_data.append(struct.pack("<I", 0))  # Size of hashing table
        output_data.append(struct.pack("<I", 0))  # Offset of hashing table

        # Write offsets for msgid
        for length, offset in koffsets:
            output_data.append(struct.pack("<II", length, offset))

        # Write offsets for msgstr
        for length, offset in voffsets:
            output_data.append(struct.pack("<II", length, offset))

        # Write messages
        for msgid in ids_data:
            output_data.append(msgid + b"\0")
        for msgstr in strs_data:
            output_data.append(msgstr + b"\0")

        # Write to file
        for data in output_data:
            fileobj.write(data)

    def gettext(self, msgid):
        """Get the translated string for a given msgid.

        Args:
            msgid: Message ID to translate

        Returns:
            Translated string or original string if not found
        """
        if not isinstance(msgid, (text_type, binary_type)):
            return msgid

        msgid = ensure_unicode(msgid)
        message = self.translations.get(msgid)
        return message.msgstr if message and message.msgstr else msgid

    def ngettext(self, msgid1, msgid2, n):
        """Get the plural form for a given msgid and count.

        Args:
            msgid1: Singular form
            msgid2: Plural form
            n: Count

        Returns:
            Appropriate plural form
        """
        if not isinstance(msgid1, (text_type, binary_type)) or not isinstance(msgid2, (text_type, binary_type)):
            return msgid1 if n == 1 else msgid2

        msgid1 = ensure_unicode(msgid1)
        msgid2 = ensure_unicode(msgid2)

        message = self.translations.get(msgid1)
        if message and message.msgstr:
            try:
                plural_forms = message.msgstr.split("\0")
                if len(plural_forms) > 1:
                    # Get plural form index from plural_forms metadata
                    plural_form = 0  # Default to first form
                    if "Plural-Forms" in self.metadata:
                        match = re.search(r"plural=(.+?);", self.metadata["Plural-Forms"])
                        if match:
                            # Evaluate plural form expression
                            try:
                                plural_form = int(eval(match.group(1).replace("n", str(n))))
                                plural_form = min(plural_form, len(plural_forms) - 1)
                            except (SyntaxError, ValueError):
                                pass
                    return plural_forms[plural_form]
            except (IndexError, AttributeError):
                pass
        return msgid1 if n == 1 else msgid2

def compile_po_file(po_file_path, mo_file_path):
    """Compile a PO file to MO format.

    Args:
        po_file_path: Path to input PO file
        mo_file_path: Path to output MO file

    Raises:
        IOError: If the input file cannot be read or the output file cannot be written
        ValueError: If the input file is not a valid PO file
    """
    try:
        # Load PO file
        po = POFile(po_file_path)
        po.load()

        # Create MO file
        mo = MOFile()
        mo.translations = po.translations
        mo.metadata = po.metadata

        # Save MO file
        with open(mo_file_path, "wb") as f:
            mo.save(f)
    except (IOError, OSError) as e:
        raise IOError("Failed to compile PO file: %s" % str(e))
    except Exception as e:
        raise ValueError("Invalid PO file: %s" % str(e))
