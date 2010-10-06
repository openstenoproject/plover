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

TODO: This code does not conform to Plover code standards and needs to
be cleaned up.

"""

import sys
import re
import threading

from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.protocol import rq, event

MODIFIERS = ( XK.XK_Shift_L, 
              XK.XK_Shift_R,
              XK.XK_Caps_Lock,
              XK.XK_Control_L,
              XK.XK_Control_R,
              XK.XK_Alt_L,
              XK.XK_Alt_R,
              XK.XK_Super_L,
              XK.XK_Super_R,
              XK.XK_Num_Lock )

MASK_INDEXES = [ (X.ShiftMapIndex, X.ShiftMask),
                 (X.ControlMapIndex, X.ControlMask),
                 (X.LockMapIndex, X.LockMask),
                 (X.Mod1MapIndex, X.Mod1Mask),
                 (X.Mod2MapIndex, X.Mod2Mask),
                 (X.Mod3MapIndex, X.Mod3Mask),
                 (X.Mod4MapIndex, X.Mod4Mask),
                 (X.Mod5MapIndex, X.Mod5Mask) ]

RECORD_EXTENSION_NOT_FOUND = "Xlib's RECORD extension is required, \
but could not be found."

class KeyboardCapture(threading.Thread):
    """Listen to all keyboard events."""
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.finished = threading.Event()
        
        # Give these some initial values
        self.ison = {"shift":False, "caps":False}
        
        # Compile our regex statements.
        self.isshift = re.compile('^Shift')
        self.iscaps = re.compile('^Caps_Lock')
        self.shiftablechar = re.compile("""^[a-z0-9]$|^minus$|^equal$|
                                           ^bracketleft$|^bracketright$|
                                           ^semicolon$|^backslash$|
                                           ^apostrophe$|^comma$|^period$|
                                           ^slash$|^grave$""",
                                        re.VERBOSE)
        
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
            if event.type == X.KeyPress:
                hookevent = self.on_key_down(event)
                self.key_down(hookevent)
            elif event.type == X.KeyRelease:
                hookevent = self.on_key_up(event)
                self.key_up(hookevent)

    def on_key_down(self, event):
        matchto = self.lookup_keysym(self.local_display.keycode_to_keysym( \
                                                              event.detail, 0))
        if self.shiftablechar.match(self.lookup_keysym( \
                       self.local_display.keycode_to_keysym(event.detail, 0))):
            # This is a character that can be typed.
            if self.ison["shift"] == False:
                keysym = self.local_display.keycode_to_keysym(event.detail, 0)
                return self.makekeyhookevent(keysym, event)
            else:
                keysym = self.local_display.keycode_to_keysym(event.detail, 1)
                return self.makekeyhookevent(keysym, event)
        else:
            # Not a typable character.
            keysym = self.local_display.keycode_to_keysym(event.detail, 0)
            if self.isshift.match(matchto):
                self.ison["shift"] = self.ison["shift"] + 1
            elif self.iscaps.match(matchto):
                if self.ison["caps"] == False:
                    self.ison["shift"] = self.ison["shift"] + 1
                    self.ison["caps"] = True
                if self.ison["caps"] == True:
                    self.ison["shift"] = self.ison["shift"] - 1
                    self.ison["caps"] = False
            return self.makekeyhookevent(keysym, event)
    
    def on_key_up(self, event):
        if self.shiftablechar.match(self.lookup_keysym( \
                       self.local_display.keycode_to_keysym(event.detail, 0))):
            if self.ison["shift"] == False:
                keysym = self.local_display.keycode_to_keysym(event.detail, 0)
            else:
                keysym = self.local_display.keycode_to_keysym(event.detail, 1)
        else:
            keysym = self.local_display.keycode_to_keysym(event.detail, 0)
        matchto = self.lookup_keysym(keysym)
        if self.isshift.match(matchto):
            self.ison["shift"] = self.ison["shift"] - 1
        return self.makekeyhookevent(keysym, event)

    # Need the following because XK.keysym_to_string() only does
    # printable chars rather than being the correct inverse of
    # XK.string_to_keysym().
    def lookup_keysym(self, keysym):
        for name in dir(XK):
            if name.startswith("XK_") and getattr(XK, name) == keysym:
                return name.lstrip("XK_")
        return "[%d]" % keysym

    def asciivalue(self, keysym):
        asciinum = XK.string_to_keysym(self.lookup_keysym(keysym))
        if asciinum < 256:
            return asciinum
        else:
            return 0
    
    def makekeyhookevent(self, keysym, event):
        storewm = self.xwindowinfo()
        if event.type == X.KeyPress:
            MessageName = "key down"
        elif event.type == X.KeyRelease:
            MessageName = "key up"
        return XKeyEvent(storewm["handle"],
                         storewm["name"],
                         storewm["class"],
                         self.lookup_keysym(keysym),
                         self.asciivalue(keysym),
                         False,
                         event.detail,
                         MessageName)
    
    def xwindowinfo(self):
        try:
            windowvar = self.local_display.get_input_focus().focus
            wmname = windowvar.get_wm_name()
            wmclass = windowvar.get_wm_class()
            wmhandle = str(windowvar)[20:30]
        except:
            # This is to keep things running smoothly. It almost never
            # happens, but still...
            return {"name":None, "class":None, "handle":None}
        if (wmname == None) and (wmclass == None):
            try:
                windowvar = windowvar.query_tree().parent
                wmname = windowvar.get_wm_name()
                wmclass = windowvar.get_wm_class()
                wmhandle = str(windowvar)[20:30]
            except:
                # This is to keep things running smoothly. It almost
                # never happens, but still...
                return {"name":None, "class":None, "handle":None}
        if wmclass == None:
            return {"name":wmname, "class":wmclass, "handle":wmhandle}
        else:
            return {"name":wmname, "class":wmclass[0], "handle":wmhandle}


class KeyboardEmulation :
    """Emulate printable key presses and backspaces."""

    def __init__(self) :

        # Grab a reference to the display.
        self.local_display = display.Display()

        # Build modifier mask mapping
        self.modMasks = {}
        mapping = self.local_display.get_modifier_mapping()
        for keySym in MODIFIERS :
            keyCodeList = self.local_display.keysym_to_keycodes(keySym)
            found = False
            for keyCode, lvl in keyCodeList:                    
                for index, mask in MASK_INDEXES:
                    if keyCode in mapping[index]:
                        self.modMasks[keySym] = mask
                        found = True
                        break
                if found: break

    def send_backspaces(self, number_of_backspaces):
        for x in xrange(number_of_backspaces) :
            self.send_keycode(22)

    def send_string(self, s) :
        for char in s:
            keyCodeList = self.local_display.keysym_to_keycodes(ord(char))
            if len(keyCodeList) > 0:
                keyCode, offset = keyCodeList[0]
                if offset == 0:
                    modifiers = 0
                elif offset == 1:
                    modifiers = self.modMasks[XK.XK_Shift_L]
                self.send_keycode(keyCode, modifiers)

    def send_keycode(self, keyCode, modifiers=0):
        self.send_key_event(keyCode, modifiers, event.KeyPress)
        self.send_key_event(keyCode, modifiers, event.KeyRelease)

    def send_key_event(self, keyCode, modifiers, eventClass) :
        targetWindow = self.local_display.get_input_focus().focus
        keyEvent = eventClass( detail=keyCode,
                               time=X.CurrentTime,
                               root=self.local_display.screen().root,
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
    
    def __init__(self, Window, WindowName, WindowProcName, Key, Ascii,
                 KeyID, ScanCode, MessageName):
        """Create an event instance.
        
        Arguments:
        
        Window -- The handle of the window.
        
        WindowName -- The name of the window.
        
        WindowProcName -- The backend process for the window.
        
        Key -- The key pressed, shifted to the correct caps value.
        
        Ascii -- An ascii representation of the key. It returns 0 if
        the ascii value is not between 31 and 256.
        
        KeyID -- This is just False for now. Under windows, it is the
        Virtual Key Code, but that's a windows-only thing.
        
        ScanCode -- Please don't use this. It differs for pretty much
        every type of keyboard. X11 abstracts this information anyway.
        
        MessageName -- 'key down' or 'key up'.
        
        """
        self.Window = Window
        self.WindowName = WindowName
        self.WindowProcName = WindowProcName
        self.Key = Key
        self.Ascii = Ascii
        self.KeyID = KeyID
        self.ScanCode = ScanCode
        self.MessageName = MessageName
        self.char = chr(Ascii)
    
    def __str__(self):
        return '\n'.join([('%s: %s' % (k, str(v))) \
                                      for k, v in self.__dict__.items()])

if __name__ == '__main__':
    kc = KeyboardCapture()
    ke = KeyboardEmulation()
    
    def test(event):
        print event
        ke.send_backspaces(3)
        ke.send_string('foo')
        
    kc.key_down = test
    kc.key_up = test
    kc.start()
    print 'Press CTRL-c to quit.'
    try :
        while True :
            pass
    except KeyboardInterrupt :
        kc.cancel()
