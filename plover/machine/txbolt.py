# Copyright (c) 2011 Hesky Fisher
# See LICENSE.txt for details.

"""Thread-based monitoring of a stenotype machine using the TX Bolt protocol."""

import plover.machine.base

# In the TX Bolt protocol, there are four sets of keys grouped in
# order from left to right. Each byte represents all the keys that
# were pressed in that set. The first two bits indicate which set this
# byte represents. The next bits are set if the corresponding key was
# pressed for the stroke.

# 00XXXXXX 01XXXXXX 10XXXXXX 110XXXXX
#   HWPKTS   UE*OAR   GLBPRF    #ZDST

# The protocol uses variable length packets of one, two, three or four
# bytes. Only those bytes for which keys were pressed will be
# transmitted. The bytes arrive in order of the sets so it is clear
# when a new stroke starts. Also, if a key is pressed in an earlier
# set in one stroke and then a key is pressed only in a later set then
# there will be a zero byte to indicate that this is a new stroke. So,
# it is reliable to assume that a stroke ended when a lower set is
# seen. Additionally, if there is no activity then the machine will
# send a zero byte every few seconds.

STENO_KEY_CHART = ("S-", "T-", "K-", "P-", "W-", "H-",  # 00
                   "R-", "A-", "O-", "*", "-E", "-U",   # 01
                   "-F", "-R", "-P", "-B", "-L", "-G",  # 10
                   "-T", "-S", "-D", "-Z", "#")         # 11


class Stenotype(plover.machine.base.SerialStenotypeBase):
    """TX Bolt interface.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """

    def __init__(self, **kwargs):
        plover.machine.base.SerialStenotypeBase.__init__(self, **kwargs)
        self._reset_stroke_state()
    
    def _reset_stroke_state(self):
        self._pressed_keys = []
        self._last_key_set = 0
        self._last_byte = 0

    def _finish_stroke(self):
        self._notify(self._pressed_keys)
        self._reset_stroke_state()

    def run(self):
        """Overrides base class run method. Do not call directly."""
        while not self.finished.isSet():
            # Grab data from the serial port.
            raw = self.serial_port.read(self.serial_port.inWaiting())
            
            # XXX : work around for python 3.1 and python 2.6 differences
            if isinstance(raw, str):
                raw = [ord(x) for x in raw]

            if not raw and len(self._pressed_keys) > 0:
                self._finish_stroke()
                continue

            for byte in raw:
                key_set = byte >> 6
                if (byte == 0 and self._last_byte != 0) or (key_set < self._last_key_set):
                    self._finish_stroke()
                else:
                    self._last_key_set = key_set
                    self._last_byte = byte
                    for i in xrange(6):
                        if (byte >> i) & 1:
                            self._pressed_keys.append(STENO_KEY_CHART[(key_set * 6) + i])
