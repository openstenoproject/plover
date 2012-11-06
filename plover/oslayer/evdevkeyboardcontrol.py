#!/usr/bin/env python
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.
#
# evdevkeyboardcontrol.py - capturing and injecting linux keyboard events
#
# This code requires evdev and uinput, as well as access to the /dev/input/event* nodes

"""Keyboard capture and control using evdev.
"""

# import sys
import threading
import re
import select
import socket
from evdev import InputDevice, uinput, ecodes as e, events
import evdev

uinput_options = {
    'name' : 'plover-uinput',
    'bustype' : e.BUS_USB,
}

KEY_UP   = 0
KEY_DOWN = 1

char_to_scancode = {
    ' ':e.KEY_SPACE,
    '*':e.KEY_KPASTERISK,
    ',':e.KEY_COMMA,
    '-':e.KEY_MINUS,
    '.':e.KEY_DOT,
    '/':e.KEY_SLASH,
    '1':e.KEY_1,
    '2':e.KEY_2,
    '3':e.KEY_3,
    '4':e.KEY_4,
    '5':e.KEY_5,
    '6':e.KEY_6,
    '7':e.KEY_7,
    '8':e.KEY_8,
    '9':e.KEY_9,
    '0':e.KEY_0,
    ';':e.KEY_SEMICOLON,
    '=':e.KEY_EQUAL,
    '[':e.KEY_LEFTBRACE,
    '\'':e.KEY_APOSTROPHE,
    '\\':e.KEY_BACKSLASH,
    ']':e.KEY_RIGHTBRACE,
    '`':e.KEY_GRAVE,
    'a':e.KEY_A,
    'b':e.KEY_B,
    'c':e.KEY_C,
    'd':e.KEY_D,
    'e':e.KEY_E,
    'f':e.KEY_F,
    'g':e.KEY_G,
    'h':e.KEY_H,
    'i':e.KEY_I,
    'j':e.KEY_J,
    'k':e.KEY_K,
    'l':e.KEY_L,
    'm':e.KEY_M,
    'n':e.KEY_N,
    'o':e.KEY_O,
    'p':e.KEY_P,
    'q':e.KEY_Q,
    'r':e.KEY_R,
    's':e.KEY_S,
    't':e.KEY_T,
    'u':e.KEY_U,
    'v':e.KEY_V,
    'w':e.KEY_W,
    'x':e.KEY_X,
    'y':e.KEY_Y,
    'z':e.KEY_Z,
}
scancode_to_char = dict(zip(char_to_scancode.values(), char_to_scancode.keys()))

upperchar_to_scancode = {
    '<':e.KEY_COMMA,
    '_':e.KEY_MINUS,
    '>':e.KEY_DOT,
    '?':e.KEY_SLASH,
    '!':e.KEY_1,
    '@':e.KEY_2,
    '#':e.KEY_3,
    '$':e.KEY_4,
    '%':e.KEY_5,
    '^':e.KEY_6,
    '&':e.KEY_7,
    '*':e.KEY_8,
    '(':e.KEY_9,
    ')':e.KEY_0,
    ':':e.KEY_SEMICOLON,
    '+':e.KEY_EQUAL,
    '{':e.KEY_LEFTBRACE,
    '"':e.KEY_APOSTROPHE,
    '|':e.KEY_BACKSLASH,
    '}':e.KEY_RIGHTBRACE,
    '~':e.KEY_GRAVE,
    'A':e.KEY_A,
    'B':e.KEY_B,
    'C':e.KEY_C,
    'D':e.KEY_D,
    'E':e.KEY_E,
    'F':e.KEY_F,
    'G':e.KEY_G,
    'H':e.KEY_H,
    'I':e.KEY_I,
    'J':e.KEY_J,
    'K':e.KEY_K,
    'L':e.KEY_L,
    'M':e.KEY_M,
    'N':e.KEY_N,
    'O':e.KEY_O,
    'P':e.KEY_P,
    'Q':e.KEY_Q,
    'R':e.KEY_R,
    'S':e.KEY_S,
    'T':e.KEY_T,
    'U':e.KEY_U,
    'V':e.KEY_V,
    'W':e.KEY_W,
    'X':e.KEY_X,
    'Y':e.KEY_Y,
    'Z':e.KEY_Z,
}

keymap_multi = {
    "Alt_L":e.KEY_LEFTALT,
    "Alt_R":e.KEY_RIGHTALT,
    "Control_L":e.KEY_LEFTCTRL,
    "Control_R":e.KEY_RIGHTCTRL,
    "Shift_L":e.KEY_LEFTSHIFT,
    "Shift_R":e.KEY_RIGHTSHIFT,
}

keymap_single = {
    "Caps_Lock":e.KEY_CAPSLOCK,
    "Num_Lock":e.KEY_NUMLOCK,
    "Scroll_Lock":e.KEY_SCROLLLOCK,
    "Shift_Lock":e.KEY_CAPSLOCK,  # This is the closest we have.

    "Return":e.KEY_ENTER,
    "Tab":e.KEY_TAB,
    "BackSpace":e.KEY_BACKSPACE,
    "Delete":e.KEY_DELETE,
    "Escape":e.KEY_ESC,
    "Break":e.KEY_BREAK,
    "Insert":e.KEY_INSERT,

    "Down":e.KEY_DOWN,
    "Up":e.KEY_UP,
    "Left":e.KEY_LEFT,
    "Right":e.KEY_RIGHT,
    "Page_Up":e.KEY_PAGEUP,
    "Page_Down":e.KEY_PAGEDOWN,
    "Home":e.KEY_HOME,
    "End":e.KEY_END,

    "Print":e.KEY_PRINT,
    "Help":e.KEY_HELP,
}
for i in xrange (1, 25):
    keymap_single['F%d' % i] = e.ecodes['KEY_F%s' % i]


# Modify InputEvent so it can return a 'keystring'
setattr (events.InputEvent, 'keystring',
    property (lambda self: scancode_to_char.get(self.code, e.KEY[self.code])))

class KeyboardCapture(threading.Thread):
    """Listen to keyboard press and release events."""

    def __init__(self):
        """Prepare to listen for keyboard events."""
        threading.Thread.__init__(self)

        # Assign default callback functions.
        self.key_down = lambda x: True
        self.key_up   = lambda x: True

        # Capture the input device for key events.  Right now,
        # we grab just SideWinder devices
        self.inputs = []
        for fn in evdev.list_devices():
            cand = InputDevice(fn)
            if "SiderWinder" in cand.name:
                self.inputs.append(cand)

    def run(self):
        self.interject, self.interrupt = socket.socketpair()

        running = True
        while running:
            rs,ws,xs = select.select(self.inputs + [self.interrupt], [], [])
            for r in rs:
                if r.fileno() == self.interrupt.fileno():
                    running = False
                    break
                for event in r.read():
                    self.process_events(event)

        self.interject.shutdown(socket.SHUT_RDWR)
        self.interrupt.shutdown(socket.SHUT_RDWR)
        self.interject = self.interrupt = None


    def start(self):
        """Starts the thread."""
        threading.Thread.start(self)

    def cancel(self):
        """Stop listening for keyboard events."""
        if self.interject: self.interject.send("stop")


    def can_suppress_keyboard(self):
        return True

    def suppress_keyboard(self, suppress):
        if suppress:
            for i in self.inputs:
                i.grab()
        else:
            for i in self.inputs:
                try:
                    i.ungrab()
                except IOError:
                    pass # workaround
        self._suppress_keyboard = suppress

    def is_keyboard_suppressed(self):
        return self._suppress_keyboard


    def process_events(self, event):
        """Handle keyboard events.

        This usually means passing them off to other callback methods.

        """
        if event.type == e.EV_KEY:
            if event.value == KEY_DOWN:
                return self.key_down(event)
            elif event.value == KEY_UP:
                return self.key_up(event)
            else : return

        # else .. Pass on the event to the output maybe?

        return;


class KeyboardEmulation:
    """Emulate keyboard events."""

    def __init__(self):
        """Prepare to emulate keyboard events."""
        self.output = uinput.UInput(**uinput_options)


    def send_backspaces(self, number_of_backspaces):
        """Emulate the given number of backspaces.

        Argument:

        number_of_backspace -- The number of backspaces to emulate.

        """
        self._send_keycodes([e.KEY_BACKSPACE] * number_of_backspaces)

    def send_string(self, s):
        """Emulate the given string.

        Argument:

        s -- The string to emulate.

        """
        keycode_list = []

        for char in s:
            code = upperchar_to_scancode.get(char, None)
            if code:
                keycode_list.append([e.KEY_LEFTSHIFT, KEY_DOWN])
                keycode_list.append(code)
                keycode_list.append([e.KEY_LEFTSHIFT, KEY_UP])
                continue

            code = char_to_scancode.get(char, None)
            if code:
                keycode_list.append(code)

        self._send_keycodes(keycode_list)

    def send_key_combination(self, combo_string):
        """Emulate a sequence of key combinations.

        Argument:

        combo_string -- A string representing a sequence of key
        combinations. Keys are represented by their names in the
        Xlib.XK module, without the 'XK_' prefix. For example, the
        left Alt key is represented by 'Alt_L'. Keys are either
        separated by a space or a left or right parenthesis.
        Parentheses must be properly formed in pairs and may be
        nested. A key immediately followed by a parenthetical
        indicates that the key is pressed down while all keys enclosed
        in the parenthetical are pressed and released in turn. For
        example, Alt_L(Tab) means to hold the left Alt key down, press
        and release the Tab key, and then release the left Alt key.

        """
        # Convert the argument into a sequence of keycodes
        # that, if executed in order, would emulate the key
        # combination represented by the argument.

        keycode_list = []
        key_down_stack = []
        last_command = None

        tokens = re.split(r'([()]|\s+)', combo_string)

        for token in tokens:
            if last_command is not None:
                if token == '(':
                    # Ack, we got ourselves a modifier keydown to deal with
                    keycode_list.append([last_command, KEY_DOWN])
                    key_down_stack.append(last_command)
                else:
                    # We are just pressing the key (does this ever happen?)
                    keycode_list.append(token)
                last_command = None

            elif key_down_stack and token == ')':
                # As above, but now we release the modifier key.
                keycode_list.append([key_down_stack.pop(), KEY_UP])


            elif token in keymap_multi:
                # *Just in case*
                if last_command:
                    keycode_list.append(last_command)

                # Store the command. The next token will dictate what happens.
                last_command = keymap_multi[token]

            elif token in keymap_single:
                keycode_list.append(keymap_single[token])

            else:
                # Oh, a normal string? How rare.
                for char in token:
                    code = upperchar_to_scancode.get(char, None)
                    if code:
                        keycode_list.append([e.KEY_LEFTSHIFT, KEY_DOWN])
                        keycode_list.append(code)
                        keycode_list.append([e.KEY_LEFTSHIFT, KEY_UP])
                        continue
                    code = char_to_scancode.get(char, None)
                    if code:
                        keycode_list.append(code)

        # Case where we only looped once and it was a multi-modifier.
        if last_command:
            keycode_list.append(last_command)
            last_command = None

        if keycode_list:
            self._send_keycodes(keycode_list)

    def _send_keycodes(self, keycodes):
        for keycode in keycodes:
            if type(keycode) is list:
                self.output.write(e.EV_KEY, keycode[0], keycode[1])
            else:
                self.output.write(e.EV_KEY, keycode, KEY_DOWN)
                self.output.write(e.EV_KEY, keycode, KEY_UP)
            self.output.syn()

if __name__ == '__main__':
    import time
    kc = KeyboardCapture()
    ke = KeyboardEmulation()

    kc.start()

    ke.send_key_combination("~hello~: werld")
    time.sleep(1)
    ke.send_backspaces(5)
    ke.send_key_combination("earth")
    time.sleep(1)
    ke.send_backspaces(5)
    ke.send_key_combination("Shift_L(sexy) Shift_L(l)aaydies")
    time.sleep(1)
    print

    kc.cancel()
