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

from .config import PLATFORM


if PLATFORM in {'linux', 'bsd'}:
    from . import xkeyboardcontrol as keyboardcontrol
elif PLATFORM == 'win':
    from . import winkeyboardcontrol as keyboardcontrol
elif PLATFORM == 'mac':
    from . import osxkeyboardcontrol as keyboardcontrol
else:
    raise Exception("No keyboard control module for platform %s" % PLATFORM)

KeyboardCapture = keyboardcontrol.KeyboardCapture
KeyboardEmulation = keyboardcontrol.KeyboardEmulation
