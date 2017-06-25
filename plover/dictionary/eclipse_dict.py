# Copyright (c) 2017 Open Steno Project
# See LICENSE.txt for details.
# Eclipse (.dix) handler
# written by Thomas Thurman <thomas@thurman.org.uk>

import zlib
import xml.etree.ElementTree as ET
from plover.steno import normalize_steno
from plover.steno_dictionary import StenoDictionary

class EclipseHandler(object):
    """Takes the XML from a .dix file and
    produces a generator which yields
    (steno, translation) pairs.
    
    Objects of this class are intended to be fed into ET.XMLParser."""

    def __init__(self):

        # Each (steno, translation) pair is represented in
        # the .dix file as an XML element:
        #
        #  <e><s>steno</s><t>translation</t></e>
        #
        # (The <e> element also has attributes for metadata;
        # these don't concern us and we ignore them.)
        #
        # Our main concern here is to capture the two fields
        # so we have data to provide when we reach the "</e>".

        self._steno = None
        self._translation = None

        # If we're interested in character data, this field
        # will hold a string; then any incoming character data will
        # be appended to that string. If we're not interested
        # in character data, this field will be None.
        self._text = None

        # Here we store the parsed data, ready for the generator,
        # results(), to yield it. In principle we could yield it as we
        # produce it, but since we're essentially in a callback
        # here anyway, it would make everything far more complicated
        # and require too much aspirin for the maintenance programmers.
        self._result = {}

    def data(self, ch):
        # If we're interested in character data, record it.
        if self._text is not None:
            self._text += ch

    def start(self, tag, attr):
        if tag in ('s', 't'):
            self._text = ''

    def end(self, tag):
        if tag=='s':
            self._steno = self._text.replace(' ','/')
            self._steno = normalize_steno(self._steno)
            self._text = None
        elif tag=='t':
            self._translation = self._text
            self._text = None
        elif tag=='e':
            self._result[self._steno] = self._translation
            self._steno = None
            self._translation = None

    def results(self):
        for (steno, translation) in self._result.items():
            yield (steno, translation)

class EclipseDictionary(StenoDictionary):
    """A StenoDictionary loaded from an Eclipse (.dix) file."""

    # We could provide _save(), if anyone would find it useful.
    # The only complication is that Eclipse stores information
    # that Plover doesn't track, such as the creation and last
    # reference time of a stroke. So we'd have to hang on to
    # that as a special case.

    def _load(self, filename):
        with open(filename, 'rb') as fp:

            # Skip past the header.
            fp.seek(0x14)

            contents = zlib.decompress(fp.read())

        handler = EclipseHandler()
        parser = ET.XMLParser(
                target = handler,
                # Workaround: the file is in ISO-8859-1, even though
                # the XML claims to be UTF-8. I assume this is a bug
                # on Advantage's part.
                encoding='ISO-8859-1',
                )
        parser.feed(contents)
        self.update(handler.results())


