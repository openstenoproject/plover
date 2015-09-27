#!/usr/bin/env python
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
    import evdevkeyboardcontrol as keyboardcontrol
elif sys.platform.startswith('win32'):
    import winkeyboardcontrol as keyboardcontrol
elif sys.platform.startswith('darwin'):
    import osxkeyboardcontrol as keyboardcontrol
else:
    raise Exception(KEYBOARDCONTROL_NOT_FOUND_FOR_OS)


class KeyboardCapture(keyboardcontrol.KeyboardCapture):
    """Listen to keyboard events."""
    pass


class KeyboardEmulation(keyboardcontrol.KeyboardEmulation):
    """Emulate printable key presses and backspaces."""
    pass


if __name__ == '__main__':
    kc = KeyboardCapture()
    ke = KeyboardEmulation()

    def test(event):
        print event
        ke.send_backspaces(3)
        ke.send_string('foo')

    # For the windows version
    kc._create_own_pump = True

    kc.key_down = test
    kc.key_up = test
    kc.start()
    print 'Press CTRL-c to quit.'
    try:
        while True:
            pass
    except KeyboardInterrupt:
        kc.cancel()
