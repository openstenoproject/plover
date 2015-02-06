# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: add options to remap keys
# TODO: look into programmatically pasting into other applications

"For use with a Kinesis Advantage keyboard used as stenotype machine."

# TODO: Change name to NKRO Keyboard.

from plover.machine.base import StenotypeBase
from plover.oslayer import keyboardcontrol

KEYCODE_TO_STENO_KEY = {38: "S-",
                        24: "S-",
                        25: "T-",
                        39: "K-",
                        26: "P-",
                        40: "W-",
                        27: "H-",
                        41: "R-",
                        55: "A-", # key V, should be 22 backspace
                        56: "O-", # key B, should be 119 delete
                        28: "*",
                        42: "*",
                        29: "*",
                        43: "*",
                        57: "-E", # key N, should be 36 enter
                        58: "-U", # key M, should be 56 space
                        30: "-F",
                        44: "-R",
                        31: "-P",
                        45: "-B",
                        32: "-L",
                        46: "-G",
                        33: "-T",
                        47: "-S",
                        51: "-D",
                        48: "-Z",
                        10: "#",
                        11: "#",
                        12: "#",
                        13: "#",
                        14: "#",
                        15: "#",
                        16: "#",
                        17: "#",
                        18: "#",
                        19: "#",
                        20: "#",
                        21: "#",
                    }


class Stenotype(StenotypeBase):
    """Standard stenotype interface for a Kinesis Advantage keyboard.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """

    def __init__(self, params):
        """Monitor a Kinesis Advantage keyboard via X events."""
        StenotypeBase.__init__(self)
        self._keyboard_emulation = keyboardcontrol.KeyboardEmulation()
        self._keyboard_capture = keyboardcontrol.KeyboardCapture()
        self._keyboard_capture.key_down = self._key_down
        self._keyboard_capture.key_up = self._key_up
        self.suppress_keyboard(True)
        self._down_keys = set()
        self._released_keys = set()
        self.arpeggiate = params['arpeggiate']

    def start_capture(self):
        """Begin listening for output from the stenotype machine."""
        self._keyboard_capture.start()
        self._ready()

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        self._keyboard_capture.cancel()
        self._stopped()

    def suppress_keyboard(self, suppress):
        self._is_keyboard_suppressed = suppress
        self._keyboard_capture.suppress_keyboard(suppress)

    def _key_down(self, event):
        """Called when a key is pressed."""
        if (self._is_keyboard_suppressed
            and event.keycode is not None
            and not self._keyboard_capture.is_keyboard_suppressed()):
            self._keyboard_emulation.send_backspaces(1)
        if event.keycode in KEYCODE_TO_STENO_KEY:
            self._down_keys.add(event.keycode)

    def _post_suppress(self, suppress, steno_keys):
        """Backspace the last stroke since it matched a command.
        
        The suppress function is passed in to prevent threading issues with the 
        gui.
        """
        n = len(steno_keys)
        if self.arpeggiate:
            n += 1
        suppress(n)

    def _key_up(self, event):
        """Called when a key is released."""
        if event.keycode in KEYCODE_TO_STENO_KEY:            
            # Process the newly released key.
            self._released_keys.add(event.keycode)
            # Remove invalid released keys.
            self._released_keys = self._released_keys.intersection(self._down_keys)

        # A stroke is complete if all pressed keys have been released.
        # If we are in arpeggiate mode then only send stroke when spacebar is pressed.
        send_strokes = bool(self._down_keys and 
                            self._down_keys == self._released_keys)
        # if self.arpeggiate:
        #     send_strokes &= event.keystring == ' '
        if send_strokes:
            steno_keys = [KEYCODE_TO_STENO_KEY[k] for k in self._down_keys
                          if k in KEYCODE_TO_STENO_KEY]
            if steno_keys:
                self._down_keys.clear()
                self._released_keys.clear()
                self._notify(steno_keys)

    @staticmethod
    def get_option_info():
        bool_converter = lambda s: s == 'True'
        return {
            'arpeggiate': (False, bool_converter),
        }
