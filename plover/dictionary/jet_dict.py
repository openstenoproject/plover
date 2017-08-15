# Standalone Jet (.mdb, .dct) reader for Plover.
# written by Thomas Thurman <thomas@thurman.org.uk>
#
# Copyright (c) 2017 Open Steno Project
# See LICENSE.txt for details.
#
# We make the assumption that we're reading a well-formed Jet4 file.
# Jet4 is used in Access 2000 and beyond. All the .dct files I've
# examined are Jet4. We could handle Jet3 files as well with a little
# work, but so far it seems unnecessary.
#
# We also make the assumption that this is a dictionary database,
# in the format that Eclipse produces.
#
# This implementation owes a debt of thanks to the mdbtools documentation:
# https://github.com/brianb/mdbtools/blob/master/HACKING

import struct
import zlib
import xml.etree.ElementTree as ET
from plover.steno import normalize_steno
from plover.steno_dictionary import StenoDictionary


##############################################
#
# A whole lot of constants.

PAGE_SIZE = 4096
PAGE_TYPE_OFFSET = 0

# The types of pages in the file.
DATA_PAGE_TYPE = 1
TABLE_CONTROL_PAGE_TYPE = 2

# Table control pages:
COLUMN_COUNT_OFFSET = 45
REALINDEX_COUNT_OFFSET = 51
COLUMNS_START_OFFSET = 63
REALINDEX_ENTRY_SIZE = 12
COLUMN_ENTRY_SIZE = 25

# Data pages:
CONTROLLING_TABLE_OFFSET = 4
ROW_COUNT_OFFSET = 12
ROW_TABLE_OFFSET = 14

# Types of columns:
COLUMN_TYPE_TEXT = 10
COLUMN_TYPE_INT = 3

# Mapping from Jet's type codes to Python's struct codes.
SIZE_TO_FORMAT = {
    1: "<B",
    2: "<H",
    4: "<I",
}

# The columns we want to find in the Dictionary table.
# We also use these to identify the table, rather than
# looking for a table called "Dictionary".
USEFUL_COLUMNS = ('Steno', 'English', 'Flags')

##############################################

class JetReader(object):
    """An iterator over the steno table inside a Jet4 database.
    """
    def __init__(self, filename):

        self._fh = open(filename, 'rb')
        self._control = self._find_control_page()

    def _find_control_page(self):
        """
        Find the control page for the Dictionary table.
        Return a dictionary with the keys:
            'page': the page number in the database file
            each member of USEFUL_COLUMNS: the metadata
                for that column, as a dictionary
                containing the keys:
                    'number'
                    'type'
                    'offset_V'
                    'offset_F'

                    Not all of these are useful.

        Note that we match columns to USEFUL_COLUMNS only
        by their name; we don't bother with type checking.

        If no dictionary table is found, raise ValueError.

               Ordinarily this would involve finding the catalogue table,
        then using it to look up the address. But since we assume
        this is a standard dictionary database, there should be
        exactly one table whose control page looks like a dictionary.
        So we can just spin through and look for that.
        """

        # The earliest possible index of the dictionary table is 3.
        page = 3

        while True:

            self._load_page(page)
            if not self._page:
                # hit the end of the file; give up
                raise ValueError("no dictionary found")

            page_type = self.get_int(PAGE_TYPE_OFFSET, 1)
            if page_type==TABLE_CONTROL_PAGE_TYPE:

                column_count = self.get_int(COLUMN_COUNT_OFFSET, size=2)
                index_count = self.get_int(REALINDEX_COUNT_OFFSET, size=4)

                # Skip the realindexes.
                cursor = COLUMNS_START_OFFSET + index_count*REALINDEX_ENTRY_SIZE

                columns = {}
                result = {}

                for i in range(column_count):
                    columns[i] = {
                        'number': self.get_int(cursor+5, 2),
                        'type': self.get_int(cursor, 1),
                        'offset_V': self.get_int(cursor+7, 2),
                        'offset_F': self.get_int(cursor+21, 2),
                    }
                    cursor += COLUMN_ENTRY_SIZE

                for i in range(column_count):

                    name_length = self.get_int(cursor, 2)
                    cursor += 2

                    name = self.get_string(cursor, name_length)

                    if name in USEFUL_COLUMNS:
                        result[name] = columns[i]

                    cursor += name_length

                if len(result)==len(USEFUL_COLUMNS):
                    # we've caught them all!
                    result['page'] = page
                    return result

            page += 1

    def __iter__(self):

        # I suspect that data pages can't occur before the
        # corresponding control page, but I don't know
        # this for sure, so let's be on the safe side
        # and start reading from the beginning.
        page = 3

        while True:
            self._load_page(page)
            if not self._page:
                # hit the end of the file; we're done
                return

            page_type = self.get_int(PAGE_TYPE_OFFSET, 1)
            if page_type==DATA_PAGE_TYPE:

                controlling_table = self.get_int(CONTROLLING_TABLE_OFFSET, 4)
                if controlling_table==self._control['page']:
                    row_count = self.get_int(ROW_COUNT_OFFSET, 2)

                    end_of_record = PAGE_SIZE-1
                    for i in range(row_count):
                        start_of_record = self.get_int(ROW_TABLE_OFFSET+i*2, 2)

                        if start_of_record & 0x8000:
                            #  0x8000 = deleted row
                            continue
                        elif start_of_record & 0x4000:
                            #  0x4000 = 4-byte reference to another data page,
                            #         which we're going to find and
                            #         read anyway
                            end_of_record -= 4
                            continue

                        field_count = self.get_int(start_of_record, 1)
                        nullmask_size = (field_count+7)//8
                        variable_field_count = self.get_int(end_of_record - (nullmask_size+1), 2)
                        variable_fields_offset = end_of_record - (nullmask_size+1+variable_field_count*2)

                        end_of_field = (variable_fields_offset - start_of_record)-3

                        var_data = []
                        for j in range(variable_field_count):
                            start_of_field = self.get_int(variable_fields_offset+j*2, 2)
                            var_data.insert(0,
                                self.get_string(start_of_field+start_of_record,
                                    (end_of_field-start_of_field)+1))
                            end_of_field = start_of_field-1

                        result = {}

                        for field in USEFUL_COLUMNS:
                            schema = self._control[field]
                            if schema['type']==COLUMN_TYPE_TEXT:
                                result[field] = var_data[schema['offset_V']]
                            else:
                                result[field] = self.get_int(schema['offset_F'] + start_of_record + 2)

                        yield result

                        # Records are stored backwards.
                        end_of_record = start_of_record-1

            page += 1

    def get_int(self, offset=0, size=2):
        """
        Returns a particular integer value from the
        current page of the database file.

        offset: The offset from the start of the page,
                in bytes.
        size:   Size of the integer. Must be
                one of the keys of SIZE_TO_FORMAT.
        returns: The integer value.
        """
        encoded = self._page[offset:offset+size]
        return struct.unpack(SIZE_TO_FORMAT[size], encoded)[0]

    def get_string(self, offset=0, length=0):
        """
        Returns a particular string value from the
        current page of the database file.

        offset:  The offset from the start of the page,
                  in bytes.
        length:  Length of the string.
        returns: The string.

        TODO: Jet4 has a weird optional string compression
            thing going on. In theory we have to handle that, but we
            don't yet, since I've never encountered it in .dct files.
            See https://github.com/brianb/mdbtools/blob/master/HACKING
            at the end of the document for details.

        """
        encoded = self._page[offset:offset+length]

        if encoded[0:1]==(0xff, 0xfe):
            raise ValueError("compressed string handling is not yet implemented")

        return bytes.decode(encoded, encoding='UTF-16')

    def _load_page(self, page_number):
        """
        Sets the current page.

        page_number:  The number of the page within the file.
        returns:     None
        """
        self._fh.seek(page_number*PAGE_SIZE)
        self._page = self._fh.read(PAGE_SIZE)


def _decode_steno(encoded,

        # This part is steno-specific, so we want to rethink
        # it if we do palantype etc here.
        #
        # FIXME I don't know what to do if the "?" comes up.
        # Throw an exception?
        keys = '?#STKPWHRAO*EU-FRPBLGTSDZ',

        # We need a hyphen if there are no vowels or * present,
        # but there are right-hand keys present.
        #
        # So the bitmasks are:
        #   ?#ST KPWH RAO* EUFR PBLG TSDZ
        #          111 11          - vowels and *
        #            11 1111 1111  - right-hand keys
        vowel_bitmask      = 0x007C00,
        right_hand_bitmask = 0x0003FF,
    ):
    """
    Converts stroke representations from the format used in
    .dct files (a hex string) to the format used in Plover.

    encoded:  A hex string representing a stroke.
    keys:     Layout of keys to expect in "encoded";
                best to leave this at the default.
    vowel_bitmask:    Bitmask of vowels in "encoded".
    right_hand_bitmask:   Bitmask of right-hand consonants
                    in "encoded".
                best to leave this at the default.
    returns:  A tuple of strings representing a stroke in Plover format
                (such as ("SPAOPB", "-FL")).
    """

    result = []

    while encoded:
        result.append('')
        stroke = int(encoded[:6], 16)

        needs_hyphen = (stroke & right_hand_bitmask) \
            and not (stroke & vowel_bitmask)

        for i in keys:
            if i=='-':
                if needs_hyphen:
                    result[-1] += '-'
            else:
                if stroke & 0x800000:
                    result[-1] += i
                stroke <<= 1

        encoded = encoded[6:]

    return tuple(result)

##############################################

class JetToStenoAdapter(object):
    """An iterator that maps the steno table in a Jet4 database
    to dictionary entries Plover can use.
    """
    def __init__(self, source):
        self._source = source

    def __iter__(self):

        for row in self._source:

            steno = _decode_steno(row['Steno'])
            translation = row['English']
            flags = row['Flags']

            affix = False

            if flags & 0x8000:
                translation = '^'+translation
                affix = True

            if flags % 0x4000:
                translation += '^'
                affix = True

            if affix:
                translation = "{%s}" % (translation,)

            if flags % 0x2000:
                translation += '{-|}'

            yield (steno, translation)

##############################################

class JetDictionary(StenoDictionary):
    """A StenoDictionary loaded from a Jet (.mdb, .dct) file."""

    def _load(self, filename):

        reader = JetReader(filename)
        adapter = JetToStenoAdapter(reader)

        self.update(adapter)


