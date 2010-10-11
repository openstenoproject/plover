# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Thread-based monitoring of a Gemini TX stenotype machine."""

import plover.machine.geminipr

STENO_KEY_CHART = (("S-","T-","K-","P-","W-","H-"), # If two high bits not set.
                   ("R-","A-","O-","*","-E","-U"),  # If second highest bit set.
                   ("-F","-R","-P","-B","-L","-G"), # If highest bit set.
                   ("-T","-S","-D","-Z","#"))       # If two highest bits set.


class Stenotype(plover.machine.geminipr.Stenotype):
    """Standard stenotype interface for a Gemini TX machine.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """
    
    def run(self):
        """Overrides base class run method. Do not call directly."""
        while not self.finished.isSet() :

            # The first byte of a packet is the number of remaining bytes.
            num_bytes = self.serial_port.read()
            if not num_bytes :
                continue
            raw = self.serial_port.read(num_bytes)
            
            # XXX : work around for python 3.1 and python 2.6 differences
            if isinstance(raw, str) :
                num_bytes = ord(num_bytes)
                raw = [ord(x) for x in raw]

            # Make sure this is a valid steno stroke.
            if not len(raw) == num_bytes:
                serial_port.flushInput()
                continue

            # Convert the raw machine output to a list of steno keys.
            steno_keys= []
            for b in raw:
                chart = STENO_KEY_CHART[b >> 6]
                mask = 1
                for key in chart:
                    if (b & mask):
                        steno_keys.append(key)
                    mask <<= 1
                
            # Notify all subscribers.
            for callback in self.subscribers:
                callback(steno_keys)
