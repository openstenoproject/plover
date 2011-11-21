# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""For use with a Microsoft Sidewinder X4 keyboard used as stenotype machine."""

from plover.machine.base import StenotypeBase
from plover import keyboardcontrol

KEYCODE_TO_STENO_KEY = {38: "S-",  # a
                        24: "S-",  # q
                        25: "T-",  # w
                        39: "K-",  # s
                        26: "P-",  # e
                        40: "W-",  # d
                        27: "H-",  # r
                        41: "R-",  # f
                        54: "A-",  # c
                        55: "O-",  # v
                        28: "*",   # t
                        42: "*",   # g
                        29: "*",   # y
                        43: "*",   # h
                        57: "-E",  # n
                        58: "-U",  # m
                        30: "-F",  # u
                        44: "-R",  # j
                        31: "-P",  # i
                        45: "-B",  # k
                        32: "-L",  # o
                        46: "-G",  # l
                        33: "-T",  # p
                        47: "-S",  # ;
                        34: "-D",  # [
                        48: "-Z",  # '
                        10: "#",   # 1
                        11: "#",   # 2
                        12: "#",   # 3
                        13: "#",   # 4
                        14: "#",   # 5
                        15: "#",   # 6
                        16: "#",   # 7
                        17: "#",   # 8
                        18: "#",   # 9
                        19: "#",   # 0
                        20: "#",   # -
                        21: "#",}  # =

class Stenotype(StenotypeBase):
    """Standard stenotype interface for a Microsoft Sidewinder X4 keyboard.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """

    def __init__(self):
        """Monitor a Microsoft Sidewinder X4 keyboard via X events."""
        StenotypeBase.__init__(self)
        self.is_keyboard_suppressed = True
        self._keyboard_emulation = keyboardcontrol.KeyboardEmulation()
        self._keyboard_capture = keyboardcontrol.KeyboardCapture()
        self._keyboard_capture.key_down = self._key_down
        self._keyboard_capture.key_up = self._key_up
        self._down_keys = set()
        self._released_keys = set()

    def start_capture(self):
        """Begin listening for output from the stenotype machine."""
        self._keyboard_capture.start()

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        self._keyboard_capture.cancel()

    def _key_down(self, event):
        # Called when a key is pressed.
        if self.is_keyboard_suppressed and event.keystring is not None :
            self._keyboard_emulation.send_backspaces(1)
        self._down_keys.add(event.keycode)

    def _key_up(self, event):
        # Called when a key is released.
        # Remove invalid released keys.
        self._released_keys = self._released_keys.intersection(self._down_keys)
        # Process the newly released key.
        self._released_keys.add(event.keycode)
        # A stroke is complete if all pressed keys have been released.
        if self._down_keys == self._released_keys:
            steno_keys = [KEYCODE_TO_STENO_KEY[k] for k in self._down_keys
                          if k in KEYCODE_TO_STENO_KEY]
            self._down_keys.clear()
            self._released_keys.clear()
            self._notify(steno_keys)
