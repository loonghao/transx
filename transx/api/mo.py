#!/usr/bin/env python
"""MO file format handler for TransX."""
from __future__ import unicode_literals

import struct
from collections import OrderedDict
import re

from transx.api.po import POFile, Message
from transx.constants import DEFAULT_CHARSET
from transx.compat import ensure_unicode, is_string

class MOFile:
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
        magic = struct.unpack('<I', fileobj.read(4))[0]
        if magic == 0xde120495:  # Big endian
            byte_order = '>'
        elif magic == 0x950412de:  # Little endian
            byte_order = '<'
        else:
            raise ValueError('Bad magic number')

        # Read version and number of strings
        version = struct.unpack(byte_order + 'I', fileobj.read(4))[0]
        if version not in (0, 1):
            raise ValueError('Bad version number')

        num_strings = struct.unpack(byte_order + 'I', fileobj.read(4))[0]
        orig_table_offset = struct.unpack(byte_order + 'I', fileobj.read(4))[0]
        trans_table_offset = struct.unpack(byte_order + 'I', fileobj.read(4))[0]
        hash_table_size = struct.unpack(byte_order + 'I', fileobj.read(4))[0]
        hash_table_offset = struct.unpack(byte_order + 'I', fileobj.read(4))[0]

        # Store header values
        self.magic = magic
        self.version = version
        self.num_strings = num_strings
        self.orig_table_offset = orig_table_offset
        self.trans_table_offset = trans_table_offset
        self.hash_table_size = hash_table_size
        self.hash_table_offset = hash_table_offset

        # Read string tables
        orig_strings = []
        trans_strings = []

        # Read original strings
        fileobj.seek(orig_table_offset)
        for i in range(num_strings):
            length = struct.unpack(byte_order + 'I', fileobj.read(4))[0]
            offset = struct.unpack(byte_order + 'I', fileobj.read(4))[0]
            orig_strings.append((length, offset))

        # Read translated strings
        fileobj.seek(trans_table_offset)
        for i in range(num_strings):
            length = struct.unpack(byte_order + 'I', fileobj.read(4))[0]
            offset = struct.unpack(byte_order + 'I', fileobj.read(4))[0]
            trans_strings.append((length, offset))

        # Read actual strings
        for i in range(num_strings):
            # Read original string
            fileobj.seek(orig_strings[i][1])
            orig = fileobj.read(orig_strings[i][0]).decode('utf-8')

            # Read translated string
            fileobj.seek(trans_strings[i][1])
            trans = fileobj.read(trans_strings[i][0]).decode('utf-8')

            # Handle context
            if '\x04' in orig:
                context, msgid = orig.split('\x04', 1)
            else:
                context, msgid = None, orig

            # Store in translations
            key = (msgid, context)
            self.translations[key] = Message(msgid=msgid, msgstr=trans, context=context)

            # Parse header if this is the header message
            if msgid == "":
                self.metadata.update(self._parse_header(trans))

    def _parse_header(self, header):
        """Parse the header into a dictionary."""
        headers = {}
        for line in header.split('\\n'):
            if not line:
                continue
            try:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
            except ValueError:
                continue
        return headers

    def _normalize_string(self, s):
        """Normalize string by handling escape sequences consistently.
        
        Args:
            s: Input string to normalize
            
        Returns:
            Normalized string with consistent escape sequences
        """
        if is_string(s):
            # 将所有单个反斜杠后跟特殊字符的情况替换为双反斜杠
            return re.sub(r'\\([ntr\\])', r'\\\\\\1', s)
        return s

    def gettext(self, msgid):
        """Get the translated string for a given msgid.
        
        Args:
            msgid: The message ID to translate
            
        Returns:
            The translated string if found, otherwise the original msgid
        """
        # Ensure msgid is unicode
        msgid = ensure_unicode(msgid)
            
        # Normalize the input msgid
        normalized_msgid = self._normalize_string(msgid)
        
        # Try with normalized msgid first
        key = (normalized_msgid, None)
        if key in self.translations:
            return self.translations[key].msgstr
            
        # Try with original msgid as fallback
        key = (msgid, None)
        if key in self.translations:
            return self.translations[key].msgstr
            
        # Return original string if no translation found
        return msgid

    def ngettext(self, msgid1, msgid2, n):
        """Get the pluralized translated string.
        
        Args:
            msgid1: The singular form
            msgid2: The plural form 
            n: The number determining plural form
            
        Returns:
            The translated string in appropriate plural form if found,
            otherwise the original msgid1/msgid2 based on n
        """
        # For now just handle basic singular/plural
        if n == 1:
            return self.gettext(msgid1)
        return self.gettext(msgid2)


def compile_po_file(po_file_path, mo_file_path):
    """Compile a PO file to MO format."""
    # Load PO file
    po = POFile(po_file_path)
    po.load()

    # Write MO file
    with open(mo_file_path, 'wb') as mo_file:
        write_mo(mo_file, po.translations)


def write_mo(fileobj, messages):
    """Write MO file format."""
    # Prepare data
    raw_messages = []
    for key, message in messages.items():
        msgid = key[0]  # Extract msgid from (msgid, context) tuple
        if msgid == "":  # Header
            # If no metadata, use msgstr directly
            if not message.metadata:
                msgstr = message.msgstr
            else:
                # Convert metadata to string format
                header_lines = []
                for meta_key, value in message.metadata.items():
                    header_lines.append(f"{meta_key}: {value}")
                msgstr = "\\n".join(header_lines) + "\\n"
        else:
            msgstr = message.msgstr
            if message.context:  # Add context prefix if present
                msgid = f"{message.context}\x04{msgid}"
        raw_messages.append((msgid, msgstr))

    # Sort by msgid
    raw_messages.sort()

    # Write header
    fileobj.write(struct.pack('<I', 0x950412de))  # Magic
    fileobj.write(struct.pack('<I', 0))  # Version
    fileobj.write(struct.pack('<I', len(raw_messages)))  # Number of strings
    fileobj.write(struct.pack('<I', 28))  # Start of original strings
    fileobj.write(struct.pack('<I', 28 + len(raw_messages) * 8))  # Start of translation strings
    fileobj.write(struct.pack('<I', 0))  # Size of hashing table
    fileobj.write(struct.pack('<I', 28 + len(raw_messages) * 16))  # Offset of hashing table

    # Write offset tables
    offset = 28 + len(raw_messages) * 16  # Skip headers and offset tables

    # Original strings
    for msgid, msgstr in raw_messages:
        encoded_msgid = msgid.encode('utf-8')
        length = len(encoded_msgid)
        fileobj.write(struct.pack('<II', length, offset))
        offset += length + 1  # Add null terminator

    # Translation strings
    for msgid, msgstr in raw_messages:
        encoded_msgstr = msgstr.encode('utf-8')
        length = len(encoded_msgstr)
        fileobj.write(struct.pack('<II', length, offset))
        offset += length + 1  # Add null terminator

    # Write strings
    for msgid, msgstr in raw_messages:
        encoded_msgid = msgid.encode('utf-8')
        fileobj.write(encoded_msgid + b'\0')

    for msgid, msgstr in raw_messages:
        encoded_msgstr = msgstr.encode('utf-8')
        fileobj.write(encoded_msgstr + b'\0')
