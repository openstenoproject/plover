# Copyright (c) 2011 Hesky Fisher.
# See LICENSE.txt for details.
#
# winkeyboardcontrol.py - capturing and injecting keyboard events in windows.

"""Keyboard capture and control in windows.

This module provides an interface for basic keyboard event capture and
emulation. Set the key_up and key_down functions of the
KeyboardCapture class to capture keyboard input. Call the send_string
and send_backspaces functions of the KeyboardEmulation class to
emulate keyboard input.

"""

import re
import functools

import pyHook
import win32api
import win32con
from pywinauto.SendKeysCtypes import SendKeys as _SendKeys

def SendKeys(s):
    _SendKeys(s, with_spaces=True, pause=0)

# For the purposes of this class, we'll only report key presses that
# result in these outputs in order to exclude special key combos.
SCANCODE_TO_KEY = {
    59: 'F1', 60: 'F2', 61: 'F3', 62: 'F4', 63: 'F5', 64: 'F6',
    65: 'F7', 66: 'F8', 67: 'F9', 68: 'F10', 87: 'F11', 88: 'F12',
    41: '`', 2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 
    9: '8', 10: '9', 11: '0', 12: '-', 13: '=', 16: 'q', 
    17: 'w', 18: 'e', 19: 'r', 20: 't', 21: 'y', 22: 'u', 23: 'i',
    24: 'o', 25: 'p', 26: '[', 27: ']', 43: '\\',
    30: 'a', 31: 's', 32: 'd', 33: 'f', 34: 'g', 35: 'h', 36: 'j',
    37: 'k', 38: 'l', 39: ';', 40: '\'', 44: 'z', 45: 'x',
    46: 'c', 47: 'v', 48: 'b', 49: 'n', 50: 'm', 51: ',', 
    52: '.', 53: '/', 57: ' ',
}


class KeyboardCapture():
    """Listen to all keyboard events."""

    CONTROL_KEYS = set(('Lcontrol', 'Rcontrol'))
    SHIFT_KEYS = set(('Lshift', 'Rshift'))
    ALT_KEYS = set(('Lmenu', 'Rmenu'))
    WIN_KEYS = set(('Lwin', 'Rwin'))
    PASSTHROUGH_KEYS = CONTROL_KEYS | SHIFT_KEYS | ALT_KEYS | WIN_KEYS
    
    def __init__(self, suppressed_keys):

        self.suppress_keyboard(True)
        self.passthrough_down_keys = set()
        self.alive = False
        self.suppressed_keys = suppressed_keys

        # NOTE(hesky): Does this need to be more efficient and less
        # general if it will be called for every keystroke?
        def on_key_event(func_name, event):
            key = SCANCODE_TO_KEY.get(event.ScanCode, None)
            if not event.Injected:
                if event.Key in self.PASSTHROUGH_KEYS:
                    if func_name == 'key_down':
                        self.passthrough_down_keys.add(event.Key)
                    if func_name == 'key_up':
                        self.passthrough_down_keys.discard(event.Key)
                if key in self.suppressed_keys and not self.passthrough_down_keys:
                    getattr(self, func_name, lambda x: True)(key)
                    return not self.is_keyboard_suppressed()
            
            return True

        self.hm = pyHook.HookManager()
        self.hm.KeyDown = functools.partial(on_key_event, 'key_down')
        self.hm.KeyUp = functools.partial(on_key_event, 'key_up')

    def start(self):
        self.alive = True
        self.run()

    def run(self):
        self.hm.HookKeyboard()

    def cancel(self):
        if self.alive:
            self.hm.UnhookKeyboard()
            # guard against active passthrough key depressions on capture cancel
            self.passthrough_down_keys.clear()
            self.alive = False

    def can_suppress_keyboard(self):
        return True

    def suppress_keyboard(self, suppress):
        self._suppress_keyboard = suppress

    def is_keyboard_suppressed(self):
        return self._suppress_keyboard


class KeyboardEmulation:
    "Mapping found here: http://msdn.microsoft.com/en-us/library/8c6yea83"
    ''' Need to test: I can't generate any of these sequences via querty '''
    keymap_multi = {
        "Alt_L": "%",
        "Alt_R": "%",
        "Control_L": "^",
        "Control_R": "^",
        "Shift_L": "+",
        "Shift_R": "+",
        }

    keymap_single = {
        # This library doesn't do anything with just keypresses for alt, ctrl
        # and shift.
        "Alt_L": "",
        "Alt_R": "",
        "Control_L": "",
        "Control_R": "",
        "Shift_L": "",
        "Shift_R": "",

        "Caps_Lock": "{CAPSLOCK}",
        "Num_Lock": "{NUMLOCK}",
        "Scroll_Lock": "{SCROLLLOCK}",
        "Shift_Lock": "{CAPSLOCK}",  # This is the closest we have.

        "Return": "{ENTER}",
        "Tab": "{TAB}",
        "BackSpace": "{BS}",
        "Delete": "{DEL}",
        "Escape": "{ESC}",
        "Break": "{BREAK}",
        "Insert": "{INS}",

        "Down": "{DOWN}",
        "Up": "{UP}",
        "Left": "{LEFT}",
        "Right": "{RIGHT}",
        "Page_Up": "{PGUP}",
        "Page_Down": "{PGDN}",
        "Home": "{HOME}",
        "End": "{END}",

        "Print": "{PRTSC}",
        "Help": "{HELP}",

        "F1": "{F1}",
        "F2": "{F2}",
        "F3": "{F3}",
        "F4": "{F4}",
        "F5": "{F5}",
        "F6": "{F6}",
        "F7": "{F7}",
        "F8": "{F8}",
        "F9": "{F9}",
        "F10": "{F10}",
        "F11": "{F11}",
        "F12": "{F12}",
        "F13": "{F13}",
        "F14": "{F14}",
        "F15": "{F15}",
        "F16": "{F16}",
    }

    SPECIAL_CHARS_PATTERN = re.compile(r'([]{}()+^%~[])')
    
    def send_backspaces(self, number_of_backspaces):
        for _ in xrange(number_of_backspaces):
            SendKeys(self.keymap_single['BackSpace'])

    def send_string(self, s):
        SendKeys(re.sub(self.SPECIAL_CHARS_PATTERN, r'{\1}', s))

    def send_key_combination(self, s):
        combo = []
        tokens = re.split(r'[() ]', s)
        for token in tokens:
            if token in self.keymap_multi:
                combo.append(self.keymap_multi[token])
            elif token in self.keymap_single:
                combo.append(self.keymap_single[token])
            elif token == ' ':
                pass
            else:
                combo.append(token)
        SendKeys(''.join(combo))

