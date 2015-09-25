#!/usr/bin/env python
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.
#
# keyboardcontrol.py - capturing and injecting X keyboard events
#
# This code requires the X Window System with the 'record' extension
# and python-xlib 1.4 or greater.
#
# This code is based on the AutoKey and pyxhook programs, both of
# which use python-xlib.

"""Keyboard capture and control using Xlib.

This module provides an interface for basic keyboard event capture and
emulation. Set the key_up and key_down functions of the
KeyboardCapture class to capture keyboard input. Call the send_string
and send_backspaces functions of the KeyboardEmulation class to
emulate keyboard input.

For an explanation of keycodes, keysyms, and modifiers, see:
http://tronche.com/gui/x/xlib/input/keyboard-encoding.html

"""

import sys
import threading

from Xlib import X, XK, display
from Xlib.ext import record, xtest
from Xlib.protocol import rq, event

RECORD_EXTENSION_NOT_FOUND = "Xlib's RECORD extension is required, \
but could not be found."

keyboard_capture_instances = []

KEYCODE_TO_PSEUDOKEY = {
    # Number row.
    49: ord("`"),
    10: ord("1"),
    11: ord("2"),
    12: ord("3"),
    13: ord("4"),
    14: ord("5"),
    15: ord("6"),
    16: ord("7"),
    17: ord("8"),
    18: ord("9"),
    19: ord("0"),
    20: ord("-"),
    21: ord("="),
    51: ord("\\"),
    # Upper row.
    24: ord("q"),
    25: ord("w"),
    26: ord("e"),
    27: ord("r"),
    28: ord("t"),
    29: ord("y"),
    30: ord("u"),
    31: ord("i"),
    32: ord("o"),
    33: ord("p"),
    34: ord("["),
    35: ord("]"),
    # Home row.
    38: ord("a"),
    39: ord("s"),
    40: ord("d"),
    41: ord("f"),
    42: ord("g"),
    43: ord("h"),
    44: ord("j"),
    45: ord("k"),
    46: ord("l"),
    47: ord(";"),
    48: ord("'"),
    # Bottom row.
    52: ord("z"),
    53: ord("x"),
    54: ord("c"),
    55: ord("v"),
    56: ord("b"),
    57: ord("n"),
    58: ord("m"),
    59: ord(","),
    60: ord("."),
    61: ord("/"),
    # Space bar.
    65: ord(" "),
}

class KeyboardCapture(threading.Thread):
    """Listen to keyboard press and release events."""

    def __init__(self):
        """Prepare to listen for keyboard events."""
        threading.Thread.__init__(self)
        self.context = None
        self.key_events_to_ignore = []

        # Assign default callback functions.
        self.key_down = lambda x: True
        self.key_up = lambda x: True

        # Get references to the display.
        self.local_display = display.Display()
        self.record_display = display.Display()

        self.is_suppressed = False
        self.grab_window = self.local_display.screen().root

    def run(self):
        # Check if the extension is present
        if not self.record_display.has_extension("RECORD"):
            raise Exception(RECORD_EXTENSION_NOT_FOUND)
            sys.exit(1)
        # Create a recording context for key events.
        self.context = self.record_display.record_create_context(
                                 0,
                                 [record.AllClients],
                                 [{'core_requests': (0, 0),
                                   'core_replies': (0, 0),
                                   'ext_requests': (0, 0, 0, 0),
                                   'ext_replies': (0, 0, 0, 0),
                                   'delivered_events': (0, 0),
                                   'device_events': (X.KeyPress, X.KeyRelease),
                                   'errors': (0, 0),
                                   'client_started': False,
                                   'client_died': False,
                                   }])

        # This method returns only after record_disable_context is
        # called. Until then, the callback function will be called
        # whenever an event occurs.
        self.record_display.record_enable_context(self.context,
                                                  self.process_events)
        # Clean up.
        self.record_display.record_free_context(self.context)

    def start(self):
        """Starts the thread after registering with a global list."""
        keyboard_capture_instances.append(self)
        threading.Thread.start(self)

    def cancel(self):
        """Stop listening for keyboard events."""
        if self.context is not None:
            self.local_display.record_disable_context(self.context)
        self.local_display.flush()
        if self in keyboard_capture_instances:
            keyboard_capture_instances.remove(self)

    def grab_key(self, keycode):
        for modifiers in (0, X.Mod2Mask):
            self.grab_window.grab_key(keycode, modifiers, False, X.GrabModeAsync, X.GrabModeAsync)

    def ungrab_key(self, keycode):
        for modifiers in (0, X.Mod2Mask):
            self.grab_window.ungrab_key(keycode, modifiers)

    def can_suppress_keyboard(self):
        return True

    def suppress_keyboard(self, suppress):
        if self.is_suppressed == suppress:
            return
        if suppress:
            fn = self.grab_key
        else:
            fn = self.ungrab_key
        for keycode in KEYCODE_TO_PSEUDOKEY.keys():
            fn(keycode)
        self.local_display.sync()
        self.is_suppressed = suppress

    def is_keyboard_suppressed(self):
        return self.is_suppressed

    def process_events(self, reply):
        """Handle keyboard events.

        This usually means passing them off to other callback methods. 
        """
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            # Ignoring swapped protocol data.
            return
        if not len(reply.data) or ord(reply.data[0]) < 2:
            # Not an event.
            return
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data,
                                       self.record_display.display, None, None)
            keycode = event.detail
            modifiers = event.state & ~0b10000 & 0xFF
            keysym = self.local_display.keycode_to_keysym(keycode, modifiers)
            if modifiers == 0:
                keysym = KEYCODE_TO_PSEUDOKEY.get(keycode, keysym)
            key_event = XKeyEvent(keycode, modifiers, keysym)
            # Either ignore the event...
            if self.key_events_to_ignore:
                ignore_keycode, ignore_event_type = self.key_events_to_ignore[0]
                if (keycode == ignore_keycode and
                    event.type == ignore_event_type):
                    self.key_events_to_ignore.pop(0)
                    continue
            # ...or pass it on to a callback method.
            if event.type == X.KeyPress:
                self.key_down(key_event)
            elif event.type == X.KeyRelease:
                self.key_up(key_event)

    def ignore_key_events(self, key_events):
        """A sequence of keycode, event type tuples to ignore.

        The sequence of keycode, event type pairs is added to a
        queue. The first keycode event that matches the head of the
        queue is ignored and the head of the queue is removed. This
        method can be used in combination with
        KeyboardEmulation.send_key_combination to prevent loops.

        Argument:

        key_events -- The sequence of keycode, event type tuples to
        ignore. Each element of the sequence is a two-tuple, the first
        element of which is a keycode (integer in [8-255], inclusive)
        and the second element of which is either Xlib.X.KeyPress or
        Xlib.X.KeyRelease.

        """
        self.key_events_to_ignore += key_events


class KeyboardEmulation(object):
    """Emulate keyboard events."""

    def __init__(self):
        """Prepare to emulate keyboard events."""
        self.display = display.Display()
        self.modifier_mapping = self.display.get_modifier_mapping()
        # Determine the backspace keycode.
        backspace_keysym = XK.string_to_keysym('BackSpace')
        self.backspace_keycode, mods = self._keysym_to_keycode_and_modifiers(
                                                backspace_keysym)
        self.time = 0

    def send_backspaces(self, number_of_backspaces):
        """Emulate the given number of backspaces.

        The emulated backspaces are not detected by KeyboardCapture.

        Argument:

        number_of_backspace -- The number of backspaces to emulate.

        """
        for x in xrange(number_of_backspaces):
            self._send_keycode(self.backspace_keycode)

    def send_string(self, s):
        """Emulate the given string.

        The emulated string is not detected by KeyboardCapture.

        Argument:

        s -- The string to emulate.

        """
        for char in s:
            keysym = ord(char)
            keycode, modifiers = self._keysym_to_keycode_and_modifiers(keysym)
            if keycode is not None:
                self._send_keycode(keycode, modifiers)
                self.display.sync()

    def send_key_combination(self, combo_string):
        """Emulate a sequence of key combinations.

        KeyboardCapture instance would normally detect the emulated
        key events. In order to prevent this, all KeyboardCapture
        instances are told to ignore the emulated key events.

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
        # Convert the argument into a sequence of keycode, event type pairs
        # that, if executed in order, would emulate the key
        # combination represented by the argument.
        keycode_events = []
        key_down_stack = []
        current_command = []
        for c in combo_string:
            if c in (' ', '(', ')'):
                keystring = ''.join(current_command)
                keysym = XK.string_to_keysym(keystring)
                keycode, mods = self._keysym_to_keycode_and_modifiers(keysym)
                current_command = []
                if keycode is None:
                    continue
                if c == ' ':
                    # Record press and release for command's key.
                    keycode_events.append((keycode, X.KeyPress))
                    keycode_events.append((keycode, X.KeyRelease))
                elif c == '(':
                    # Record press for command's key.
                    key_down_stack.append(keycode)
                    keycode_events.append((keycode, X.KeyPress))
                elif c == ')':
                    # Record press and release for command's key and
                    # release previously held key.
                    keycode_events.append((keycode, X.KeyPress))
                    keycode_events.append((keycode, X.KeyRelease))
                    if len(key_down_stack):
                        keycode = key_down_stack.pop()
                        keycode_events.append((keycode, X.KeyRelease))
            else:
                current_command.append(c)
        # Record final command key.
        keystring = ''.join(current_command)
        keysym = XK.string_to_keysym(keystring)
        keycode, mods = self._keysym_to_keycode_and_modifiers(keysym)
        if keycode is not None:
            keycode_events.append((keycode, X.KeyPress))
            keycode_events.append((keycode, X.KeyRelease))
        # Release all keys.
        for keycode in key_down_stack:
            keycode_events.append((keycode, X.KeyRelease))

        # Tell all KeyboardCapture instances to ignore the key
        # events that are about to be sent.
        for capture in keyboard_capture_instances:
            capture.ignore_key_events(keycode_events)

        # Emulate the key combination by sending key events.
        for keycode, event_type in keycode_events:
            xtest.fake_input(self.display, event_type, keycode)
            self.display.sync()

    def _send_keycode(self, keycode, modifiers=0):
        """Emulate a key press and release.

        Arguments:

        keycode -- An integer in the inclusive range [8-255].

        modifiers -- An 8-bit bit mask indicating if the key pressed
        is modified by other keys, such as Shift, Capslock, Control,
        and Alt.

        """
        self._send_key_event(keycode, modifiers, event.KeyPress)
        self._send_key_event(keycode, modifiers, event.KeyRelease)

    def _send_key_event(self, keycode, modifiers, event_class):
        """Simulate a key press or release.

        These events are not detected by KeyboardCapture.

        Arguments:

        keycode -- An integer in the inclusive range [8-255].

        modifiers -- An 8-bit bit mask indicating if the key pressed
        is modified by other keys, such as Shift, Capslock, Control,
        and Alt.

        event_class -- One of Xlib.protocol.event.KeyPress or
        Xlib.protocol.event.KeyRelease.

        """
        target_window = self.display.get_input_focus().focus
        # Make sure every event time is different than the previous one, to
        # avoid an application thinking its an auto-repeat.
        self.time = (self.time + 1) % 4294967295
        key_event = event_class(detail=keycode,
                                 time=self.time,
                                 root=self.display.screen().root,
                                 window=target_window,
                                 child=X.NONE,
                                 root_x=1,
                                 root_y=1,
                                 event_x=1,
                                 event_y=1,
                                 state=modifiers,
                                 same_screen=1
                                 )
        target_window.send_event(key_event)

    def _keysym_to_keycode_and_modifiers(self, keysym):
        """Return a keycode and modifier mask pair that result in the keysym.

        There is a one-to-many mapping from keysyms to keycode and
        modifiers pairs; this function returns one of the possibly
        many valid mappings, or the tuple (None, None) if no mapping
        exists.

        Arguments:

        keysym -- A key symbol.

        """
        keycodes = self.display.keysym_to_keycodes(keysym)
        if len(keycodes) > 0:
            keycode, offset = keycodes[0]
            modifiers = 0
            if offset == 1 or offset == 3 or offset == 5:
                # The keycode needs the Shift modifier.
                modifiers |= X.ShiftMask
            if offset == 4 or offset == 5:
                # 3rd (AltGr) level.
                modifiers |= X.Mod5Mask
            if offset == 2 or offset == 3:
                # The keysym is in group Group 2 instead of Group 1.
                for i, mod_keycodes in enumerate(self.modifier_mapping):
                    if keycode in mod_keycodes:
                        modifiers |= (1 << i)
            return (keycode, modifiers)
        return (None, None)



class XKeyEvent(object):
    """A class to hold all the information about a key event."""

    def __init__(self, keycode, modifiers, keysym):
        """Create an event instance.

        Arguments:

        keycode -- The keycode that identifies a physical key.

        modifiers -- An 8-bit mask. A set bit means the corresponding
        modifier is active. See Xlib.X.ShiftMask, Xlib.X.LockMask,
        Xlib.X.ControlMask, and Xlib.X.Mod1Mask through
        Xlib.X.Mod5Mask.

        keysym -- The symbol obtained when the key corresponding to
        keycode without any modifiers. The KeyboardEmulation class
        does not track modifiers such as Shift and Control.

        """
        self.keycode = keycode
        self.modifiers = modifiers
        self.keysym = keysym
        # Only want printable characters.
        if keysym < 255 or keysym in (XK.XK_Return, XK.XK_Tab):
            self.keystring = XK.keysym_to_string(keysym)
            if self.keystring == '\x00':
                self.keystring = None
        else:
            self.keystring = None

    def __str__(self):
        return ' '.join([('%s: %s' % (k, str(v)))
                                      for k, v in self.__dict__.items()])

if __name__ == '__main__':
    kc = KeyboardCapture()
    ke = KeyboardEmulation()

    import time

    def test(event):
        if not event.keycode:
            return
        print event
        time.sleep(0.1)
        keycode_events = ke.send_key_combination('Alt_L(Tab)')
        #ke.send_backspaces(5)
        #ke.send_string('Foo:~')

    #kc.key_down = test
    kc.key_up = test
    kc.start()
    print 'Press CTRL-c to quit.'
    try:
        while True:
            pass
    except KeyboardInterrupt:
        kc.cancel()
