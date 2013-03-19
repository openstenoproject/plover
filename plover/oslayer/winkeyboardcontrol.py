#!/usr/bin/env python
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
import pythoncom
import threading
import win32api
import win32com.client
import win32con
# For the purposes of this class, we'll only report key presses that
# result in these outputs in order to exclude special key combos.

WATCHED_KEYS = set(['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-',
                    '=', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[',
                    ']', '\\', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l',
                    ';', '\'', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.',
                    '/', ' '])


class KeyboardCapture(threading.Thread):
    """Listen to all keyboard events."""

    def __init__(self):
        threading.Thread.__init__(self)

        self.suppress_keyboard(True)

        # NOTE(hesky): Does this need to be more efficient and less
        # general if it will be called for every keystroke?
        def on_key_event(func_name, event):
            if not event.Injected and chr(event.Ascii) in WATCHED_KEYS:
                getattr(self, func_name,
                        lambda x: True)(KeyboardEvent(event.Ascii))
                return not self.is_keyboard_suppressed()
            else:
                return True

        self.hm = pyHook.HookManager()
        self.hm.KeyDown = functools.partial(on_key_event, 'key_down')
        self.hm.KeyUp = functools.partial(on_key_event, 'key_up')

    def run(self):
        self.hm.HookKeyboard()
        pythoncom.PumpMessages()

    def cancel(self):
        if self.is_alive():
            self.hm.UnhookKeyboard()
            win32api.PostThreadMessage(self.ident, win32con.WM_QUIT)

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

    def __init__(self):
        # Todo(Hesky): Is this hacky? Should we use keybd_event (deprecated) or
        # its replacement SendInput?
        self.shell = win32com.client.Dispatch("WScript.Shell")
        self.SPECIAL_CHARS_PATTERN = re.compile(r'([{}[\]()+^%~])')

    def send_backspaces(self, number_of_backspaces):
        for _ in xrange(number_of_backspaces):
            self.shell.SendKeys(self.keymap_single['BackSpace'])

    def send_string(self, s):
        self.shell.SendKeys(re.sub(self.SPECIAL_CHARS_PATTERN, r'{\1}', s))

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
        self.shell.SendKeys(''.join(combo))


class KeyboardEvent(object):
    """A keyboard event."""

    def __init__(self, char):
        self.keystring = chr(char)

if __name__ == '__main__':
    kc = KeyboardCapture()
    ke = KeyboardEmulation()

    def test(event):
        print event.keystring
        ke.send_backspaces(1)
        ke.send_string(' you pressed: "' + event.keystring + '" ')

    kc.key_up = test
    kc.start()
    print 'Press CTRL-c to quit.'
    try:
        while True:
            pass
    except KeyboardInterrupt:
        kc.cancel()
