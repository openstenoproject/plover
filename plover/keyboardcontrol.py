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
from Xlib.ext import record
from Xlib.protocol import rq, event

RECORD_EXTENSION_NOT_FOUND = "Xlib's RECORD extension is required, \
but could not be found."


class KeyboardCapture(threading.Thread):
    """Listen to all keyboard events."""
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.finished = threading.Event()
        
        # Assign default function actions (do nothing).
        self.key_down = lambda x: True
        self.key_up = lambda x: True
        
        # Hook to our display.
        self.local_display = display.Display()
        self.record_display = display.Display()
        
        
    def run(self):
        # Check if the extension is present
        if not self.record_display.has_extension("RECORD"):
            raise Exception(RECORD_EXTENSION_NOT_FOUND)
            sys.exit(1)
        r = self.record_display.record_get_version(0, 0)
        # See r.major_version and r.minor_version for RECORD extension version.

        # Create a recording context; we only want key events
        self.ctx = self.record_display.record_create_context(
                0,
                [record.AllClients],
                [{
                        'core_requests': (0, 0),
                        'core_replies': (0, 0),
                        'ext_requests': (0, 0, 0, 0),
                        'ext_replies': (0, 0, 0, 0),
                        'delivered_events': (0, 0),
                        'device_events': (X.KeyPress, X.KeyRelease),
                        'errors': (0, 0),
                        'client_started': False,
                        'client_died': False,
                }])

        # Enable the context; this only returns after a call to
        # record_disable_context, while calling the callback function
        # in the meantime.
        self.record_display.record_enable_context(self.ctx,
                                                  self.process_events)
        # Finally free the context.
        self.record_display.record_free_context(self.ctx)

    def cancel(self):
        self.finished.set()
        self.local_display.record_disable_context(self.ctx)
        self.local_display.flush()
    
    def process_events(self, reply):
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
            event, data = rq.EventField(None).parse_binary_value(data, \
                                       self.record_display.display, None, None)
            keycode = event.detail
            keysym = self.local_display.keycode_to_keysym(keycode, 0)
            key_event = XKeyEvent(keycode, keysym)
            if event.type == X.KeyPress:
                self.key_down(key_event)
            elif event.type == X.KeyRelease:
                self.key_up(key_event)


class KeyboardEmulation :
    """Emulate printable key presses and backspaces."""

    def __init__(self) :
        self.display = display.Display()
        self.modifier_mapping = self.display.get_modifier_mapping()

    def send_backspaces(self, number_of_backspaces):
        for x in xrange(number_of_backspaces) :
            self.send_keycode(22)

    def keysym_to_keycode_and_modifiers(self, keysym):
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
            if offset == 1 or offset == 3:
                # The keycode needs the Shift modifier.
                modifiers |= X.ShiftMask
            if offset == 2 or offset == 3:
                # The keysym is in group Group 2 instead of Group 1.
                for i, mod_keycodes in enumerate(self.modifier_mapping):
                    if keycode in mod_keycodes:
                        modifiers |= (1 << i)
            return (keycode, modifiers)
        return (None, None)

    def send_string(self, s) :
        for char in s:
            keysym = ord(char)
            keycode, modifiers = self.keysym_to_keycode_and_modifiers(keysym)
            if keycode is not None:
                self.send_keycode(keycode, modifiers)

    def send_keycode(self, keycode, modifiers=0):
        self.send_key_event(keycode, modifiers, event.KeyPress)
        self.send_key_event(keycode, modifiers, event.KeyRelease)

    def send_key_event(self, keycode, modifiers, eventClass) :
        targetWindow = self.display.get_input_focus().focus
        keyEvent = eventClass( detail=keycode,
                               time=X.CurrentTime,
                               root=self.display.screen().root,
                               window=targetWindow,
                               child=X.NONE,
                               root_x=1,
                               root_y=1,
                               event_x=1,
                               event_y=1,
                               state=modifiers,
                               same_screen=1
                               )
        targetWindow.send_event(keyEvent)        


class XKeyEvent:
    """A class to hold all the information about a key event."""
    
    def __init__(self, keycode, keysym):
        """Create an event instance.
        
        Arguments:
        
        keycode -- The keycode that identifies a physical key.
        
        keysym -- The symbol obtained when the key corresponding to
        keycode without any modifiers. The KeyboardEmulation class
        does not track modifiers such as Shift and Control.

        """
        self.keycode = keycode
        self.keysym = keysym
        # Only want printable characters.
        if keysym < 255 or keysym in (XK.XK_Return, XK.XK_Tab):
            self.keystring = XK.keysym_to_string(keysym)
        else:
            self.keystring = None
    
    def __str__(self):
        return '\n'.join([('%s: %s' % (k, str(v))) \
                                      for k, v in self.__dict__.items()])

if __name__ == '__main__':
    kc = KeyboardCapture()
    ke = KeyboardEmulation()
    
    def test(event):
        print event.keystring, event.keycode
        #ke.send_backspaces(5)
        #ke.send_string('Foo:~')
        
    kc.key_down = test
    kc.key_up = test
    kc.start()
    print 'Press CTRL-c to quit.'
    try :
        while True :
            pass
    except KeyboardInterrupt :
        kc.cancel()
