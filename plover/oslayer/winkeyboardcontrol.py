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

import ctypes
import multiprocessing
import os
import threading

from ctypes import windll, wintypes

# Python 2/3 compatibility.
from six.moves import winreg

from plover.key_combo import parse_key_combo
from plover.oslayer.winkeyboardlayout import KeyboardLayout
from plover import log
from plover.misc import characters

SendInput = windll.user32.SendInput
LONG = ctypes.c_long
DWORD = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(DWORD)
WORD = ctypes.c_ushort
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_UNICODE = 0x0004
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1


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

KEY_TO_SCANCODE = {v: k for k, v in SCANCODE_TO_KEY.items()}

# Keys that need an extended key flag for Windows input
EXTENDED_KEYS = {
    # Control   Alt         INS   DEL   HOME  END   PG UP PG DN Arrows
    0xA2, 0xA3, 0xA4, 0xA5, 0x2D, 0x2E, 0x21, 0x22, 0x24, 0x23, 0x25, 0x26,
    # Arrow     NmLk  Break PtSc  Divide
    0x27, 0x28, 0x90, 0x03, 0x2C, 0x6F
}

"""
SendInput code and classes based off of code
from user "inControl" on StackOverflow:
http://stackoverflow.com/questions/11906925/python-simulate-keydown
"""

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (('dx', LONG),
                ('dy', LONG),
                ('mouseData', DWORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (('wVk', WORD),
                ('wScan', WORD),
                ('dwFlags', DWORD),
                ('time', DWORD),
                ('dwExtraInfo', ULONG_PTR))


class _INPUTunion(ctypes.Union):
    _fields_ = (('mi', MOUSEINPUT),
                ('ki', KEYBDINPUT))


class INPUT(ctypes.Structure):
    _fields_ = (('type', DWORD),
                ('union', _INPUTunion))


def pid_exists(pid):
    """Check whether pid exists in the current process table."""
    # Code based on psutil implementation.
    kernel32 = ctypes.windll.kernel32

    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    ERROR_INVALID_PARAMETER = 87
    ERROR_ACCESS_DENIED = 5
    STILL_ACTIVE = 0x00000103

    process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, 0, pid)
    if not process:
        err = kernel32.GetLastError()
        if err == ERROR_INVALID_PARAMETER:
            # Invalid parameter is no such process.
            return False
        if err == ERROR_ACCESS_DENIED:
            # Access denied obviously means there's a process to deny access to...
            return True
        raise WindowsError(err, '')

    try:
        exitcode = DWORD()
        out = kernel32.GetExitCodeProcess(process, ctypes.byref(exitcode))
        if not out:
            err = kernel32.GetLastError()
            if err == ERROR_ACCESS_DENIED:
                # Access denied means there's a process
                # there so we'll assume it's running.
                return True
            raise WindowsError(err, '')

        return exitcode.value == STILL_ACTIVE

    finally:
        kernel32.CloseHandle(process)


class HeartBeat(threading.Thread):

    def __init__(self, ppid, atexit):
        super(HeartBeat, self).__init__()
        self._ppid = ppid
        self._atexit = atexit
        self._finished = threading.Event()

    def run(self):
        while pid_exists(self._ppid):
            if self._finished.wait(1):
                break
        self._atexit()

    def stop(self):
        self._finished.set()
        self.join()


class KeyboardCaptureProcess(multiprocessing.Process):

    CONTROL_KEYS = set((0xA2, 0xA3))
    SHIFT_KEYS = set((0xA0, 0xA1))
    ALT_KEYS = set((0xA4, 0xA5))
    WIN_KEYS = set((0x5B, 0x5C))
    PASSTHROUGH_KEYS = CONTROL_KEYS | SHIFT_KEYS | ALT_KEYS | WIN_KEYS

    def __init__(self):
        super(KeyboardCaptureProcess, self).__init__()
        self.daemon = True
        self._ppid = os.getpid()
        self._update_registry()
        self._tid = None
        self._queue = multiprocessing.Queue()
        self._suppressed_keys_bitmask = multiprocessing.Array(ctypes.c_uint64, (max(SCANCODE_TO_KEY.keys()) + 63) // 64)
        self._suppressed_keys_bitmask[:] = (0xffffffffffffffff,) * len(self._suppressed_keys_bitmask)

    @staticmethod
    def _update_registry():
        # From MSDN documentation:
        #
        # The hook procedure should process a message in less time than the
        # data entry specified in the LowLevelHooksTimeout value in the
        # following registry key:
        #
        # HKEY_CURRENT_USER\Control Panel\Desktop
        #
        # The value is in milliseconds. If the hook procedure times out, the
        # system passes the message to the next hook. However, on Windows 7 and
        # later, the hook is silently removed without being called. There is no
        # way for the application to know whether the hook is removed.


        def _open_key(rights):
            return winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                  r'Control Panel\Desktop',
                                  0, rights)

        REG_LLHOOK_KEY_FULL_NAME = r'HKEY_CURRENT_USER\Control Panel\Desktop\LowLevelHooksTimeout'
        REG_LLHOOK_KEY_VALUE_NAME = 'LowLevelHooksTimeout'
        REG_LLHOOK_KEY_VALUE_TYPE = winreg.REG_DWORD
        REG_LLHOOK_KEY_VALUE = 5000

        read_key = _open_key(winreg.KEY_READ)
        try:
            value, value_type = winreg.QueryValueEx(read_key, REG_LLHOOK_KEY_VALUE_NAME)
        except WindowsError:
            value, value_type = (None, None)

        if value_type != REG_LLHOOK_KEY_VALUE_TYPE or value != REG_LLHOOK_KEY_VALUE:
            try:
                write_key = _open_key(winreg.KEY_WRITE)
                winreg.SetValueEx(write_key, REG_LLHOOK_KEY_VALUE_NAME, 0,
                                  REG_LLHOOK_KEY_VALUE_TYPE, REG_LLHOOK_KEY_VALUE)
            except WindowsError:
                log.warning('could not update registry key: %s, see documentation',
                            REG_LLHOOK_KEY_FULL_NAME)
            else:
                log.warning('the following registry key has been updated, '
                            'you should reboot: %s', REG_LLHOOK_KEY_FULL_NAME)

    def run(self):

        heartbeat = HeartBeat(self._ppid, self._send_quit)
        heartbeat.start()

        import atexit
        import signal

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", wintypes.DWORD),
                ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p),
            ]

        KeyboardProc = ctypes.CFUNCTYPE(ctypes.c_int,
                                        ctypes.c_int,
                                        wintypes.WPARAM,
                                        ctypes.POINTER(KBDLLHOOKSTRUCT))

        # Ignore KeyboardInterrupt when attached to a console...
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        self._tid = windll.kernel32.GetCurrentThreadId()
        self._queue.put(self._tid)

        down_keys = set()
        passthrough_down_keys = set()

        def on_key(pressed, event):
            if (event.flags & 0x10):
                # Ignore simulated events (e.g. from KeyboardEmulation).
                return False
            if event.vkCode in self.PASSTHROUGH_KEYS:
                if pressed:
                    passthrough_down_keys.add(event.vkCode)
                else:
                    passthrough_down_keys.discard(event.vkCode)
            key = SCANCODE_TO_KEY.get(event.scanCode)
            if key is None:
                # Unhandled, ignore and don't suppress.
                return False
            suppressed = bool(self._suppressed_keys_bitmask[event.scanCode // 64] & (1 << (event.scanCode % 64)))
            if pressed:
                if passthrough_down_keys:
                    # Modifier(s) pressed, ignore.
                    return False
                down_keys.add(key)
            else:
                down_keys.discard(key)
            self._queue.put((key, pressed))
            return suppressed

        hook_id = None

        def low_level_handler(code, wparam, lparam):
            if code >= 0:
                pressed = wparam in (0x100, 0x104)
                if on_key(pressed, lparam[0]):
                    # Suppressed...
                    return 1
            return windll.user32.CallNextHookEx(hook_id, code, wparam, lparam)

        pointer = KeyboardProc(low_level_handler)
        hook_id = windll.user32.SetWindowsHookExA(0x00D, pointer, windll.kernel32.GetModuleHandleW(None), 0)
        atexit.register(windll.user32.UnhookWindowsHookEx, hook_id)
        msg = wintypes.MSG()
        while windll.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0):
            windll.user32.TranslateMessage(ctypes.byref(msg))
            windll.user32.DispatchMessageW(ctypes.byref(msg))

        heartbeat.stop()

    def _send_quit(self):
        windll.user32.PostThreadMessageW(self._tid,
                                         0x0012, # WM_QUIT
                                         0, 0)

    def start(self):
        self.daemon = True
        super(KeyboardCaptureProcess, self).start()
        self._tid = self._queue.get()

    def stop(self):
        if self.is_alive():
            self._send_quit()
            self.join()
        # Wake up capture thread, so it gets a chance to check if it must stop.
        self._queue.put((None, None))

    def suppress_keyboard(self, suppressed_keys):
        bitmask = [0] * len(self._suppressed_keys_bitmask)
        for key in suppressed_keys:
            code = KEY_TO_SCANCODE[key]
            bitmask[code // 64] |= (1 << (code % 64))
        self._suppressed_keys_bitmask[:] = bitmask

    def get(self):
        return self._queue.get()


class KeyboardCapture(threading.Thread):
    """Listen to all keyboard events."""

    def __init__(self):
        super(KeyboardCapture, self).__init__()
        self._suppressed_keys = set()
        self.key_down = lambda key: None
        self.key_up = lambda key: None
        self._proc = KeyboardCaptureProcess()
        self._finished = threading.Event()

    def start(self):
        self._proc.start()
        self._proc.suppress_keyboard(self._suppressed_keys)
        super(KeyboardCapture, self).start()

    def run(self):
        while True:
            key, pressed = self._proc.get()
            if self._finished.isSet():
                break
            (self.key_down if pressed else self.key_up)(key)

    def cancel(self):
        self._finished.set()
        self._proc.stop()
        if self.is_alive():
            self.join()

    def suppress_keyboard(self, suppressed_keys=()):
        self._suppressed_keys = set(suppressed_keys)
        self._proc.suppress_keyboard(self._suppressed_keys)


class KeyboardEmulation(object):

    def __init__(self):
        self.keyboard_layout = KeyboardLayout()

    # Sends input types to buffer
    @staticmethod
    def _send_input(*inputs):
        len_inputs = len(inputs)
        len_pinput = INPUT * len_inputs
        pinputs = len_pinput(*inputs)
        c_size = ctypes.c_int(ctypes.sizeof(INPUT))
        return SendInput(len_inputs, pinputs, c_size)

    # Input type (can be mouse, keyboard)
    @staticmethod
    def _input(structure):
        if isinstance(structure, MOUSEINPUT):
            return INPUT(INPUT_MOUSE, _INPUTunion(mi=structure))
        if isinstance(structure, KEYBDINPUT):
            return INPUT(INPUT_KEYBOARD, _INPUTunion(ki=structure))
        raise TypeError('Cannot create INPUT structure!')

    # Container to send mouse input
    # Not used, but maybe one day it will be useful
    @staticmethod
    def _mouse_input(flags, x, y, data):
        return MOUSEINPUT(x, y, data, flags, 0, None)

    # Keyboard input type to send key input
    @staticmethod
    def _keyboard_input(code, flags):
        if flags == KEYEVENTF_UNICODE:
            # special handling of Unicode characters
            return KEYBDINPUT(0, code, flags, 0, None)
        return KEYBDINPUT(code, 0, flags, 0, None)

    # Abstraction to set flags to 0 and create an input type
    def _keyboard(self, code, flags=0):
        return self._input(self._keyboard_input(code, flags))

    def _key_event(self, keycode, pressed):
        flags = 0 if pressed else KEYEVENTF_KEYUP
        if keycode in EXTENDED_KEYS:
            flags |= KEYEVENTF_EXTENDEDKEY
        self._send_input(self._keyboard(keycode, flags))

    # Press and release a key
    def _key_press(self, char):
        vk, ss = self.keyboard_layout.char_to_vk_ss[char]
        keycode_list = []
        keycode_list.extend(self.keyboard_layout.ss_to_vks[ss])
        keycode_list.append(vk)
        # Press all keys.
        for keycode in keycode_list:
            self._key_event(keycode, True)
        # Release all keys
        for keycode in keycode_list:
            self._key_event(keycode, False)

    def _refresh_keyboard_layout(self):
        layout_id = KeyboardLayout.current_layout_id()
        if layout_id != self.keyboard_layout.layout_id:
            self.keyboard_layout = KeyboardLayout(layout_id)

    def _key_unicode(self, char):
        inputs = [self._keyboard(ord(code), KEYEVENTF_UNICODE)
                  for code in char]
        self._send_input(*inputs)

    def send_backspaces(self, number_of_backspaces):
        for _ in range(number_of_backspaces):
            self._key_press('\x08')

    def send_string(self, s):
        self._refresh_keyboard_layout()
        for char in characters(s):
            if char in self.keyboard_layout.char_to_vk_ss:
                # We know how to simulate the character.
                self._key_press(char)
            else:
                # Otherwise, we send it as a Unicode string.
                self._key_unicode(char)

    def send_key_combination(self, combo_string):
        """Emulate a sequence of key combinations.
        Argument:
        combo_string -- A string representing a sequence of key
        combinations. Keys are represented by their names in the
        self.keyboard_layout.keyname_to_keycode above. For example, the
        left Alt key is represented by 'Alt_L'. Keys are either
        separated by a space or a left or right parenthesis.
        Parentheses must be properly formed in pairs and may be
        nested. A key immediately followed by a parenthetical
        indicates that the key is pressed down while all keys enclosed
        in the parenthetical are pressed and released in turn. For
        example, Alt_L(Tab) means to hold the left Alt key down, press
        and release the Tab key, and then release the left Alt key.
        """
        # Make sure keyboard layout is up-to-date.
        self._refresh_keyboard_layout()
        # Parse and validate combo.
        key_events = parse_key_combo(combo_string, self.keyboard_layout.keyname_to_vk.get)
        # Send events...
        for keycode, pressed in key_events:
            self._key_event(keycode, pressed)
