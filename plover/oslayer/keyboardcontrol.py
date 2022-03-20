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

from plover.oslayer.config import PLATFORM

KEYBOARDCONTROL_NOT_FOUND_FOR_OS = \
        "No keyboard control module was found for platform: %s" % PLATFORM

if PLATFORM in {'linux', 'bsd'}:
    from plover.oslayer import xkeyboardcontrol as keyboardcontrol
elif PLATFORM == 'win':
    from plover.oslayer import winkeyboardcontrol as keyboardcontrol
elif PLATFORM == 'mac':
    from plover.oslayer import osxkeyboardcontrol as keyboardcontrol
else:
    raise Exception(KEYBOARDCONTROL_NOT_FOUND_FOR_OS)


class KeyboardCapture(keyboardcontrol.KeyboardCapture):
    """Listen to keyboard events."""

class KeyboardEmulation(keyboardcontrol.KeyboardEmulation):
    """Emulate printable key presses and backspaces."""
    pass
