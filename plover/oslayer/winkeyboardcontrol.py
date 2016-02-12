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
import threading

import pyHook
from pywinauto.SendKeysCtypes import SendKeys as _SendKeys


# Global state used by KeyboardCapture to support multiple instances.

class HookManager(object):

    def __init__(self):
        self._lock = threading.Lock()
        self._hm = pyHook.HookManager()
        self._key_down_callbacks = []
        self._key_up_callbacks = []
        self._nb_callbacks = 0

        def _on_key_event(callback_list, event):
            if event.Injected:
                return True
            with self._lock:
                callback_list = list(callback_list)
            allow = True
            for callback in callback_list:
                allow = callback(event) and allow
            return allow

        self._hm.KeyUp = functools.partial(_on_key_event, self._key_up_callbacks)
        self._hm.KeyDown = functools.partial(_on_key_event, self._key_down_callbacks)

        def _set_key_callback(callback_list, enable, callback):
            with self._lock:
                if enable:
                    assert callback not in callback_list
                    callback_list.append(callback)
                    self._nb_callbacks += 1
                    if 1 == self._nb_callbacks:
                        self._hm.HookKeyboard()
                else:
                    assert callback in callback_list
                    callback_list.remove(callback)
                    self._nb_callbacks -= 1
                    if 0 == self._nb_callbacks:
                        self._hm.UnhookKeyboard()

        self.register_key_up = functools.partial(_set_key_callback,
                                                 self._key_up_callbacks,
                                                 True)
        self.unregister_key_up = functools.partial(_set_key_callback,
                                                   self._key_up_callbacks,
                                                   False)
        self.register_key_down = functools.partial(_set_key_callback,
                                                   self._key_down_callbacks,
                                                   True)
        self.unregister_key_down = functools.partial(_set_key_callback,
                                                     self._key_down_callbacks,
                                                     False)

_hook_manager = HookManager()


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
    52: '.', 53: '/', 57: 'space', 58: "BackSpace", 83: "Delete",
    80: "Down", 79: "End", 1: "Escape", 71: "Home", 82: "Insert",
    75: "Left", 73: "Page_Down", 81: "Page_Up", 28 : "Return",
    77: "Right", 15: "Tab", 72: "Up",
}


class KeyboardCapture(object):
    """Listen to all keyboard events."""

    CONTROL_KEYS = set(('Lcontrol', 'Rcontrol'))
    SHIFT_KEYS = set(('Lshift', 'Rshift'))
    ALT_KEYS = set(('Lmenu', 'Rmenu'))
    WIN_KEYS = set(('Lwin', 'Rwin'))
    PASSTHROUGH_KEYS = CONTROL_KEYS | SHIFT_KEYS | ALT_KEYS | WIN_KEYS

    def __init__(self):
        self._passthrough_down_keys = set()
        self._alive = False
        self._suppressed_keys = set()
        self.key_down = lambda key: None
        self.key_up = lambda key: None

        # NOTE(hesky): Does this need to be more efficient and less
        # general if it will be called for every keystroke?
        def on_key_event(func_name, event):
            if event.Key in self.PASSTHROUGH_KEYS:
                if func_name == 'key_down':
                    self._passthrough_down_keys.add(event.Key)
                elif func_name == 'key_up':
                    self._passthrough_down_keys.discard(event.Key)
            key = SCANCODE_TO_KEY.get(event.ScanCode)
            if key is not None and not self._passthrough_down_keys:
                getattr(self, func_name)(key)
                return key not in self._suppressed_keys
            return True

        self._on_key_up = functools.partial(on_key_event, 'key_up')
        self._on_key_down = functools.partial(on_key_event, 'key_down')

    def start(self):
        _hook_manager.register_key_up(self._on_key_up)
        _hook_manager.register_key_down(self._on_key_down)
        self._alive = True

    def cancel(self):
        if not self._alive:
            return
        _hook_manager.unregister_key_up(self._on_key_up)
        _hook_manager.unregister_key_down(self._on_key_down)
        # Guard against active passthrough key depressions on capture cancel.
        self._passthrough_down_keys.clear()
        self._alive = False

    def suppress_keyboard(self, suppressed_keys=()):
        self._suppressed_keys = set(suppressed_keys)


class KeyboardEmulation(object):
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

