# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"Thread-based monitoring of a stenotype machine using the passport protocol."

from plover.machine.base import SerialStenotypeBase
from itertools import izip_longest

# Passport protocol is documented here:
# http://www.eclipsecat.com/?q=system/files/Passport%20protocol_0.pdf

STENO_KEY_CHART = {
    '!': None,
    '#': '#',
    '^': None,
    '+': None,
    'S': 'S-',
    'C': 'S-',
    'T': 'T-',
    'K': 'K-',
    'P': 'P-',
    'W': 'W-',
    'H': 'H-',
    'R': 'R-',
    '~': '*',
    '*': '*',
    'A': 'A-',
    'O': 'O-',
    'E': '-E',
    'U': '-U',
    'F': '-F',
    'Q': '-R',
    'N': '-P',
    'B': '-B',
    'L': '-L',
    'G': '-G',
    'Y': '-T',
    'X': '-S',
    'D': '-D',
    'Z': '-Z',
}


class Stenotype(SerialStenotypeBase):
    """Passport interface."""

    def __init__(self, params):
        SerialStenotypeBase.__init__(self, params)
        self.packet = []

    def _read(self, b):
        b = chr(b)
        self.packet.append(b)
        if b == '>':
            self._handle_packet(''.join(self.packet))
            del self.packet[:]

    def _handle_packet(self, packet):
        encoded = packet.split('/')[1]
        keys = []
        for key, shadow in grouper(encoded, 2, 0):
            shadow = int(shadow, base=16)
            if shadow >= 8:
                key = STENO_KEY_CHART[key]
                if key:
                    keys.append(key)
        if keys:
            self._notify(keys)

    def run(self):
        """Overrides base class run method. Do not call directly."""
        self._ready()

        while not self.finished.isSet():
            # Grab data from the serial port.
            raw = self.serial_port.read(self.serial_port.inWaiting())

            # XXX : work around for python 3.1 and python 2.6 differences
            if isinstance(raw, str):
                raw = [ord(x) for x in raw]

            for b in raw:
                self._read(b)

    @staticmethod
    def get_option_info():
        """Get the default options for this machine."""
        bool_converter = lambda s: s == 'True'
        sb = lambda s: int(float(s)) if float(s).is_integer() else float(s)
        return {
            'port': (None, str), # TODO: make first port default
            'baudrate': (38400, int),
            'bytesize': (8, int),
            'parity': ('N', str),
            'stopbits': (1, sb),
            'timeout': (2.0, float),
            'xonxoff': (False, bool_converter),
            'rtscts': (False, bool_converter)
        }


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

