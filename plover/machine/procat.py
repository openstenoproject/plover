# Copyright (c) 2016 Ted Morin
# See LICENSE.txt for details.

"""Thread-based monitoring of a ProCAT stenotype machine."""

# Python 2/3 compatibility.
from six import iterbytes

from plover.machine.base import SerialStenotypeBase

"""
ProCAT machines send 4 bytes per stroke, with the last byte only consisting of
FF. So we need only look at the first 3 bytes to see our steno. The leading
bit is 0.
"""
STENO_KEY_CHART = ('', '#', 'S-', 'T-', 'K-', 'P-', 'W-', 'H-',
                   'R-', 'A-', 'O-', '*', '-E', '-U', '-F', '-R',
                   '-P', '-B', '-L', '-G', '-T', '-S', '-D', '-Z',
                   )

BYTES_PER_STROKE = 4


class ProCAT(SerialStenotypeBase):
    """Interface for ProCAT machines.
    """

    KEYS_LAYOUT = '''
        #  #  #  #  #  #  #  #  #  #
        S- T- P- H- * -F -P -L -T -D
        S- K- W- R- * -R -B -G -S -Z
               A- O- -E -U
    '''

    def run(self):
        """Overrides base class run method. Do not call directly."""
        self._ready()
        while not self.finished.isSet():

            # Grab data from the serial port.
            raw = self.serial_port.read(BYTES_PER_STROKE)
            if not raw:
                continue

            # Convert the raw to a list of steno keys.
            steno_keys = self.keymap.keys_to_actions(
                self.process_steno_packet(raw)
            )
            if steno_keys:
                # Notify all subscribers.
                self._notify(steno_keys)

    @staticmethod
    def process_steno_packet(raw):
        # Raw packet has 4 bytes, we only care about the first 3
        steno_keys = []
        for i, b in enumerate(iterbytes(raw[:3])):
            for j in range(0, 8):
                if b & 0x80 >> j:
                    key = STENO_KEY_CHART[i * 8 + j]
                    if key:
                        steno_keys.append(key)
        return steno_keys


