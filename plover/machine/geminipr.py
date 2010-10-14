# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Thread-based monitoring of a Gemini PR stenotype machine."""

import plover.machine.base

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
            for i in range(len(raw)):
                b = raw[i]
                for j in range(8):
                    if i == 0 and j == 0:
                        continue # Ignore the first bit 
                    if (b & (0x80 >> j)):
                        steno_keys.append(STENO_KEY_CHART[i*7 + j-1]) 
                
            # Notify all subscribers.
            self._notify(steno_keys)
