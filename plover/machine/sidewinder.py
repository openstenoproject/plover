# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""For use with a Microsoft Sidewinder X4 keyboard used as stenotype machine."""

from plover import keyboardcontrol

QWERTY_TO_STENO = {"a": "S-",
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
                   "=": "#",}

class Stenotype :
    """Standard stenotype interface for a Microsoft Sidewinder X4 keyboard.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """

    def __init__(self):
        """Monitor a Microsoft Sidewinder X4 keyboard via X events."""
        self.keyboard_emulation = keyboardcontrol.KeyboardEmulation()
        self.keyboard_capture = keyboardcontrol.KeyboardCapture()
        self.keyboard_capture.key_down = self._key_down
        self.keyboard_capture.key_up = self._key_up
        self.subscribers = []
        self.down_keys = set()
        self.released_keys = set()

    def start_capture(self):
        """Begin listening for output from the stenotype machine."""
        self.keyboard_capture.start()

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        self.keyboard_capture.cancel()

    def add_callback(self, callback):
        """Subscribe to output from the stenotype machine.

        Argument:

        callback -- The function to call whenever there is output from
        the stenotype machine and output is being captured.

        """
        self.subscribers.append(callback)

    def _key_down(self, event):
        # Called when a key is pressed.
        if event.char != '\x00' :
            self.keyboard_emulation.send_backspaces(1)
        self.down_keys.add(event.char)

    def _key_up(self, event):
        # Called when a key is released.
        # Remove invalid released keys.
        self.released_keys = self.released_keys.intersection(self.down_keys)
        # Process the newly released key.
        self.released_keys.add(event.char)
        # A stroke is complete if all pressed keys have been released.
        if self.down_keys == self.released_keys:
            steno_keys = [QWERTY_TO_STENO[k] for k in self.down_keys
                         if k in QWERTY_TO_STENO]
            self.down_keys.clear()
            self.released_keys.clear()
            for callback in self.subscribers :
                callback(steno_keys)
