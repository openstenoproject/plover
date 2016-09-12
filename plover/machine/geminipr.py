# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Thread-based monitoring of a Gemini PR stenotype machine."""

# Python 2/3 compatibility.
from six import iterbytes

from plover.machine.base import SerialStenotypeBase

# In the Gemini PR protocol, each packet consists of exactly six bytes
# and the most significant bit (MSB) of every byte is used exclusively
# to indicate whether that byte is the first byte of the packet
# (MSB=1) or one of the remaining five bytes of the packet (MSB=0). As
# such, there are really only seven bits of steno data in each packet
# byte. This is why the STENO_KEY_CHART below is visually presented as
# six rows of seven elements instead of six rows of eight elements.
STENO_KEY_CHART = ("Fn", "#1", "#2", "#3", "#4", "#5", "#6",
                   "S1-", "S2-", "T-", "K-", "P-", "W-", "H-",
                   "R-", "A-", "O-", "*1", "*2", "res1", "res2",
                   "pwr", "*3", "*4", "-E", "-U", "-F", "-R",
                   "-P", "-B", "-L", "-G", "-T", "-S", "-D",
                   "#7", "#8", "#9", "#A", "#B", "#C", "-Z")

BYTES_PER_STROKE = 6


class GeminiPr(SerialStenotypeBase):
    """Standard stenotype interface for a Gemini PR machine.
    """

    KEYS_LAYOUT = '''
        #1 #2  #3 #4 #5 #6 #7 #8 #9 #A #B #C
        Fn S1- T- P- H- *1 *3 -F -P -L -T -D
           S2- K- W- R- *2 *4 -R -B -G -S -Z
                  A- O-       -E -U
        pwr
        res1
        res2
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
            steno_keys = []
            for i, b in enumerate(iterbytes(raw)):
                for j in range(1, 8):
                    if (b & (0x80 >> j)):
                        steno_keys.append(STENO_KEY_CHART[i * 7 + j - 1])

            steno_keys = self.keymap.keys_to_actions(steno_keys)
            if steno_keys:
                # Notify all subscribers.
                self._notify(steno_keys)

