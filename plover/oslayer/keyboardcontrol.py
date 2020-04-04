#!/usr/bin/env python3
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.
#
# keyboardcontrol.py - Abstracted keyboard control.
#
# Uses OS appropriate module.

"""Keyboard capture and control.

This module provides an interface for basic keyboard event capture and
emulation. Set the key_up and key_down functions of the
KeyboardCapture class to capture keyboard input. Call the send_string
and send_backspaces functions of the KeyboardEmulation class to
emulate keyboard input.

"""

import sys

KEYBOARDCONTROL_NOT_FOUND_FOR_OS = \
        "No keyboard control module was found for os %s" % sys.platform

if sys.platform.startswith('linux'):
    from plover.oslayer import xkeyboardcontrol as keyboardcontrol
elif sys.platform.startswith('win32'):
    from plover.oslayer import winkeyboardcontrol as keyboardcontrol
elif sys.platform.startswith('darwin'):
    from plover.oslayer import osxkeyboardcontrol as keyboardcontrol
else:
    raise Exception(KEYBOARDCONTROL_NOT_FOUND_FOR_OS)


class KeyboardCapture(keyboardcontrol.KeyboardCapture):
    """Listen to keyboard events."""

    # Supported keys.
    SUPPORTED_KEYS_LAYOUT = '''
    Escape  F1 F2 F3 F4  F5 F6 F7 F8  F9 F10 F11 F12

      `  1  2  3  4  5  6  7  8  9  0  -  =  \\ BackSpace  Insert Home Page_Up
     Tab  q  w  e  r  t  y  u  i  o  p  [  ]               Delete End  Page_Down
           a  s  d  f  g  h  j  k  l  ;  '      Return
            z  x  c  v  b  n  m  ,  .  /                          Up
                     space                                   Left Down Right
    '''
    SUPPORTED_KEYS = tuple(SUPPORTED_KEYS_LAYOUT.split())


class KeyboardEmulation(keyboardcontrol.KeyboardEmulation):
    """Emulate printable key presses and backspaces."""
    pass


if __name__ == '__main__':

    import time

    kc = KeyboardCapture()
    ke = KeyboardEmulation()

    pressed = set()
    status = 'pressed: '

    def test(key, action):
        global status
        print(key, action)
        if 'pressed' == action:
            pressed.add(key)
        elif key in pressed:
            pressed.remove(key)
        new_status = 'pressed: ' + '+'.join(pressed)
        if status != new_status:
            ke.send_backspaces(len(status))
            ke.send_string(new_status)
            status = new_status

    kc.key_down = lambda k: test(k, 'pressed')
    kc.key_up = lambda k: test(k, 'released')
    kc.suppress_keyboard(KeyboardCapture.SUPPORTED_KEYS)
    kc.start()
    print('Press CTRL-c to quit.')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        kc.cancel()
