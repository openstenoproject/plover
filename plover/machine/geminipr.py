# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Thread-based monitoring of a Gemini PR stenotype machine."""

import plover.machine.base

# In the Gemini PR protocol, each packet consists of exactly six bytes
# and the most significant bit (MSB) of every byte is used exclusively
# to indicate whether that byte is the first byte of the packet
# (MSB=1) or one of the remaining five bytes of the packet (MSB=0). As
# such, there are really only seven bits of steno data in each packet
# byte. This is why the STENO_KEY_CHART below is visually presented as
# six rows of seven elements instead of six rows of eight elements.
STENO_KEY_CHART = ("Fn","#","#","#","#","#","#",
                   "S-","S-","T-","K-","P-","W-","H-",
                   "R-","A-","O-","*","*","res","res",
                   "pwr","*","*","-E","-U","-F","-R",
                   "-P","-B","-L","-G","-T","-S","-D",
                   "#","#","#","#","#","#","-Z")

BYTES_PER_STROKE = 6

class Stenotype(plover.machine.base.SerialStenotypeBase):
    """Standard stenotype interface for a Gemini PR machine.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """
    
    def run(self):
        """Overrides base class run method. Do not call directly."""
        while not self.finished.isSet() :

            # Grab data from the serial port.
            raw = self.serial_port.read(BYTES_PER_STROKE)
            if not raw :
                continue
            
            # XXX : work around for python 3.1 and python 2.6 differences
            if isinstance(raw, str) :
                raw = [ord(x) for x in raw]

            # Make sure this is a valid steno stroke.
            if not ((len(raw) == BYTES_PER_STROKE) and
                    (raw[0] & 0x80) and
                    (len([b for b in raw if b & 0x80]) == 1)):
                serial_port.flushInput()
                continue
    
            # Convert the raw to a list of steno keys.
            steno_keys= []
            for i, b in enumerate(raw):
                for j in range(1,8):
                    if (b & (0x80 >> j)):
                        steno_keys.append(STENO_KEY_CHART[i*7 + j-1])
                
            # Notify all subscribers.
            self._notify(steno_keys)
