# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: add options to remap keys
# TODO: look into programmatically pasting into other applications

"For use with a Microsoft Sidewinder X4 keyboard used as stenotype machine."

# TODO: Change name to NKRO Keyboard.

from plover.machine.base import StenotypeBase
from plover.oslayer import keyboardcontrol

KEYSTRING_TO_STENO_KEY = {"a": "S-",
                          "q": "S-",
                          "w": "T-",
                          "s": "K-",
                          "e": "P-",
                          "d": "W-",
                          "r": "H-",
                          "f": "R-",
                          "c": "A-",
                          "v": "O-",
                          "t": "*",
                          "g": "*",
                          "y": "*",
                          "h": "*",
                          "n": "-E",
                          "m": "-U",
                          "u": "-F",
                          "j": "-R",
                          "i": "-P",
                          "k": "-B",
                          "o": "-L",
                          "l": "-G",
                          "p": "-T",
                          ";": "-S",
                          "[": "-D",
                          "'": "-Z",
                          "1": "#",
                          "2": "#",
                          "3": "#",
                          "4": "#",
                          "5": "#",
                          "6": "#",
                          "7": "#",
                          "8": "#",
                          "9": "#",
                          "0": "#",
                          "-": "#",
                          "=": "#",
                         }


class Stenotype(StenotypeBase):
    """Standard stenotype interface for a Microsoft Sidewinder X4 keyboard.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """

    def __init__(self, params):
        """Monitor a Microsoft Sidewinder X4 keyboard via X events."""
        StenotypeBase.__init__(self)
        self._keyboard_emulation = keyboardcontrol.KeyboardEmulation()
        self._keyboard_capture = keyboardcontrol.KeyboardCapture()
        self._keyboard_capture.key_down = self._key_down
        self._keyboard_capture.key_up = self._key_up
        self.suppress_keyboard(True)
        self._down_keys = set()
        self._released_keys = set()
        # This is handy for debugging on a non-NKRO keyboard. Once there is an
        # options dialog for this machine then this can be used by regular
        # users.
        self.arpegiate = False

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
            and event.keystring is not None
            and not self._keyboard_capture.is_keyboard_suppressed()):
            self._keyboard_emulation.send_backspaces(1)
        if event.keystring in KEYSTRING_TO_STENO_KEY:
            self._down_keys.add(event.keystring)

    def _post_suppress(self, suppress, steno_keys):
        """Backspace the last stroke since it matched a command.
        
        The suppress function is passed in to prevent threading issues with the 
        gui.
        """
        suppress(len(steno_keys))

    def _key_up(self, event):
        """Called when a key is released."""
        if event.keystring in KEYSTRING_TO_STENO_KEY:            
            # Process the newly released key.
            self._released_keys.add(event.keystring)
            # Remove invalid released keys.
            self._released_keys = self._released_keys.intersection(self._down_keys)

        # A stroke is complete if all pressed keys have been released.
        # If we are in arpegiate mode then only send stroke when spacebar is pressed.
        send_strokes = (self._down_keys and 
                        self._down_keys == self._released_keys)
        if self.arpegiate:
            send_strokes &= event.keystring == ' '
        if send_strokes:
            steno_keys = [KEYSTRING_TO_STENO_KEY[k] for k in self._down_keys
                          if k in KEYSTRING_TO_STENO_KEY]
            if steno_keys:
                self._down_keys.clear()
                self._released_keys.clear()
                self._notify(steno_keys)
