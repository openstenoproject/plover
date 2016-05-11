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

import collections
import ctypes
import multiprocessing
import os
import threading
import time
import types
import _winreg as winreg

from ctypes import windll, wintypes

import win32api
import win32gui

from plover.key_combo import add_modifiers_aliases, parse_key_combo
from plover import log


SendInput = windll.user32.SendInput
MapVirtualKey = windll.user32.MapVirtualKeyW
GetKeyboardLayout = windll.user32.GetKeyboardLayout
GetWindowThreadProcessId = windll.user32.GetWindowThreadProcessId
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


class WindowsKeyboardLayout:
    """
    Create a set of objects that are customized to the user's current keyboard layout.
    This class allows us to send key codes that are correct, regardless of the users
    layout, and letting us fall back to sending Unicode even if they don't have Latin
    letters on their keyboard.
    """

    # This mapping only works on keyboards using the ANSI standard layout.
    # No letters yet, those are customized per-layout.
    KEYNAME_TO_KEYCODE = {
        # Adding media controls for windows
        'standby': [0x5f],
        'back': [0xa6], 'forward': [0xa7], 'refresh': [0xa8], 'stop': [0xa9],
        'search': [0xaa], 'favorites': [0xab], 'homepage': [0xac], 'www': [0xac],
        'audiomute': [0xad], 'audiolowervolume': [0xae], 'audioraisevolume': [0xaf],
        'audionext': [0xb0], 'audioprev': [0xb1], 'audiostop': [0xb2],
        'audioplay': [0xb3], 'audiopause': [0xb3], 'audiomedia': [0xb5],
        'mycomputer': [0xb6], 'calculator': [0xb7],

        'mail': [0xb4],

        'alt_l': [0xa4], 'alt_r': [0xa5], 'control_l': [0xa2], 'control_r': [0xa3],
        'shift_l': [0xa0], 'shift_r': [0xa1], 'super_l': [0x5b], 'super_r': [0x5c],

        'caps_lock': [0x14], 'num_lock': [0x90], 'scroll_lock': [0x91],

        'return': [0x0d], 'tab': [0x09], 'backspace': [0x08], 'delete': [0x2e],
        'escape': [0x1b], 'break': [0x03], 'insert': [0x2d], 'pause': [0x13],
        'print': [0x2c],

        'up': [0x26], 'down': [0x28], 'left': [0x25], 'right': [0x27],
        'page_up': [0x21], 'page_down': [0x22], 'home': [0x24], 'end': [0x23],

        'f1': [0x70], 'f2': [0x71], 'f3': [0x72], 'f4': [0x73], 'f5': [0x74],
        'f6': [0x75], 'f7': [0x76], 'f8': [0x77], 'f9': [0x78], 'f10': [0x79],
        'f11': [0x7a], 'f12': [0x7b], 'f13': [0x7c], 'f14': [0x7d], 'f15': [0x7e],
        'f16': [0x7f], 'f17': [0x80], 'f18': [0x81], 'f19': [0x82], 'f20': [0x83],
        'f21': [0x84], 'f22': [0x85], 'f23': [0x86], 'f24': [0x87],

        'kp_0': [0x60], 'kp_1': [0x61], 'kp_2': [0x62], 'kp_3': [0x63],
        'kp_4': [0x64], 'kp_5': [0x65], 'kp_6': [0x66], 'kp_7': [0x67],
        'kp_8': [0x68], 'kp_9': [0x69], 'kp_add': [0xa1, 0xbb],
        'kp_decimal': [0x6e], 'kp_delete': [0x2e], 'kp_divide': [0x6f],
        'kp_enter': [0x0d], 'kp_equal': [0xbb], 'kp_multiply': [0x6a],
        'kp_subtract': [0x6d],

        'help': [0x2f], 'mode_switch': [0x1f], 'menu': [0x5d],

        'cancel': [0x03], 'clear': [0x0c], 'execute': [0x2b],

        'next': [0x22],
        'prior': [0x21], 'select': [0x29],
    }
    add_modifiers_aliases(KEYNAME_TO_KEYCODE)

    # Handle Plover's key names by mapping them to Unicode.
    KEYNAME_TO_UNICODE = {
        # Values of Unicode chars
        'plusminus': 177, 'aring': 229, 'yen': 165, 'ograve': 242,
        'adiaeresis': 228, 'ntilde': 209, 'questiondown': 191, 'yacute': 221,
        'atilde': 195, 'ccedilla': 231, 'copyright': 169, 'ntilde': 241,
        'otilde': 245, 'masculine': 9794, 'eacute': 201, 'ocircumflex': 244,
        'guillemotright': 187, 'ecircumflex': 234, 'uacute': 250, 'cedilla': 184,
        'oslash': 248, 'acute': 237, 'ssharp': 223, 'igrave': 204,
        'twosuperior': 178, 'udiaeresis': 252, 'notsign': 172, 'exclamdown': 161,
        'ordfeminine': 9792, 'otilde': 213, 'agrave': 224, 'ection': 167,
        'egrave': 232, 'macron': 175, 'icircumflex': 206, 'diaeresis': 168,
        'ucircumflex': 251, 'atilde': 227, 'acircumflex': 194, 'degree': 176,
        'thorn': 222, 'acircumflex': 226, 'aring': 197, 'ooblique': 216,
        'ugrave': 217, 'agrave': 192, 'ydiaeresis': 255, 'threesuperior': 179,
        'egrave': 200, 'idiaeresis': 207, 'igrave': 236, 'eth': 208,
        'ecircumflex': 202, 'aacute': 193, 'cent': 162, 'registered': 174,
        'oacute': 211, 'adiaeresis': 228, 'guillemotleft': 171, 'ediaeresis': 235,
        'ograve': 210, 'mu': 956, 'paragraph': 182, 'ccedilla': 199, 'thorn': 254,
        'threequarters': 190, 'ae': 230, 'brokenbar': 166, 'nobreakspace': 32,
        'currency': 164, 'ugrave': 249, 'ucircumflex': 219, 'odiaeresis': 246,
        'periodcentered': 183, 'uacute': 218, 'idiaeresis': 239, 'yacute': 253,
        'sterling': 163, 'ae': 198, 'ediaeresis': 203, 'onequarter': 188,
        'onehalf': 189, 'thorn': 222, 'aacute': 225, 'icircumflex': 238,
        'udiaeresis': 220, 'eacute': 233, 'eth': 240, 'eth': 240, 'iacute': 205,
        'onesuperior': 185, 'ocircumflex': 212, 'odiaeresis': 214, 'oacute': 243
    }

    # Maps from literal characters to their key names.
    LITERALS = {
        '~': 'asciitilde', '!': 'exclam', '@': 'at',
        '#': 'numbersign', '$': 'dollar', '%': 'percent', '^': 'asciicircum',
        '&': 'ampersand', '*': 'asterisk', '(': 'parenleft', ')': 'parenright',
        '-': 'minus', '_': 'underscore', '=': 'equal', '+': 'plus',
        '[': 'bracketleft', ']': 'bracketright', '{': 'braceleft',
        '}': 'braceright', '\\': 'backslash', '|': 'bar', ';': 'semicolon',
        ':': 'colon', '\'': 'apostrophe', '"': 'quotedbl', ',': 'comma',
        '<': 'less', '.': 'period', '>': 'greater', '/': 'slash',
        '?': 'question', '\t': 'tab', ' ': 'space', '\n': 'return', '\r': 'return',
    }

    def __init__(self, layout_id=None):
        # Get active layout
        self.layout_id = WindowsKeyboardLayout.current_layout_id() if layout_id is None else layout_id
        self.keyname_to_keycode = dict(self.KEYNAME_TO_KEYCODE)
        self.keyname_to_unicode = dict(self.KEYNAME_TO_UNICODE)

        # Here we add the main letters and special characters found on a standard layout.
        for character in (
            '0123456789'
            'abcdefghijklmnopqrstuvwxyz'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        ):
            self._add_char(character, character)
        for character, keyname in self.LITERALS.items():
            self._add_char(character, keyname)

        self.literals = {
            symbol: name
            for symbol, name in self.LITERALS.items()
            if name in self.keyname_to_keycode
        }

    def _add_char(self, character, keyname):
        codes = self._kc(character)
        if len(codes) > 0:
            self.keyname_to_keycode[keyname] = codes
        elif len(character) is 1:
            self.keyname_to_unicode[keyname] = ord(character)

    # Converts a character into a key sequence based on current layout
    # Returns a list of key codes to send *or* False to represent key not found
    def _kc(self, character):
        sequence = []

        # Doesn't support unicode
        if len(character) > 1:
            return []

        vk = win32api.VkKeyScanEx(character, self.layout_id)

        # Low bit is keycode
        kc = vk & 0xFF
        mods = vk >> 8

        # Keyboard layout does not have this key
        if kc < 0 or mods < 0:
            return []

        # High bit is modifiers
        if (mods & 1):
            sequence.append(0xA1) # Shift_R
        if (mods & 2):
            sequence.append(0xA3) # Control_R
        if (mods & 4):
            sequence.append(0xA5) # Alt_R
        sequence.append(kc)
        return sequence

    @staticmethod
    def current_layout_id():
        return GetKeyboardLayout(
            GetWindowThreadProcessId(
                win32gui.GetForegroundWindow(), 0
            )
        )

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

    def run(self):
        while pid_exists(self._ppid):
            time.sleep(1)
        self._atexit()


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
            except WindowsError as e:
                log.warning('could not update registry key: %s, see documentation',
                            REG_LLHOOK_KEY_FULL_NAME)
            else:
                log.warning('the following registry key has been updated, '
                            'you should reboot: %s', REG_LLHOOK_KEY_FULL_NAME)

    def run(self):

        heartbeat = HeartBeat(self._ppid, self.stop)
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

        self._tid = win32api.GetCurrentThreadId()
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
            if passthrough_down_keys:
                # Modifier(s) pressed, ignore.
                return False
            key = SCANCODE_TO_KEY.get(event.scanCode)
            if key is None:
                # Unhandled, ignore and don't suppress.
                return False
            suppressed = bool(self._suppressed_keys_bitmask[event.scanCode // 64] & (1 << (event.scanCode % 64)))
            if pressed:
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

    def start(self):
        self.daemon = True
        super(KeyboardCaptureProcess, self).start()
        self._tid = self._queue.get()

    def stop(self):
        if self.is_alive():
            windll.user32.PostThreadMessageW(self._tid,
                                             0x0012, # WM_QUIT
                                             0, 0)
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
        self._proc.stop()
        if self.is_alive():
            self._finished.set()
            self.join()

    def suppress_keyboard(self, suppressed_keys=()):
        self._suppressed_keys = set(suppressed_keys)
        self._proc.suppress_keyboard(self._suppressed_keys)


class KeyboardEmulation:
    keyboard_layout = WindowsKeyboardLayout()

    def __init__(self):
        pass

    # Sends input types to buffer
    @staticmethod
    def _send_input(*inputs):
        len_inputs = len(inputs)
        len_pinput = INPUT * len_inputs
        pinputs = len_pinput(*inputs)
        c_size = ctypes.c_int(ctypes.sizeof(INPUT))
        return SendInput(len_inputs, pinputs, c_size)

    # "Narrow python" unicode objects store characters in UTF-16 so we
    # can't iterate over characters in the standard way. This workaround
    # lets us iterate over full characters in the string.
    @staticmethod
    def _characters(s):
        encoded = s.encode('utf-32-be')
        characters = []
        for i in xrange(len(encoded)/4):
            start = i * 4
            end = start + 4
            character = encoded[start:end].decode('utf-32-be')
            yield character

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
        return KEYBDINPUT(code, MapVirtualKey(code, 0), flags, 0, None)

    # Abstraction to set flags to 0 and create an input type
    def _keyboard(self, code, flags=0):
        return self._input(self._keyboard_input(code, flags))

    def _key_event(self, keycode, pressed):
        flags = 0 if pressed else KEYEVENTF_KEYUP
        if keycode in EXTENDED_KEYS:
            flags |= KEYEVENTF_EXTENDEDKEY
        self._send_input(self._keyboard(keycode, flags))

    # Press and release a key
    def _key_press(self, keyname):
        keycode_list = self.keyboard_layout.keyname_to_keycode[keyname]
        # Press all keys.
        for keycode in keycode_list:
            self._key_event(keycode, True)
        # Release all keys
        for keycode in keycode_list:
            self._key_event(keycode, False)

    def _refresh_keyboard_layout(self):
        layout_id = WindowsKeyboardLayout.current_layout_id()
        if layout_id != self.keyboard_layout.layout_id:
            self.keyboard_layout = WindowsKeyboardLayout(layout_id)

    # Send a Unicode character to application from code
    def _key_unicode(self, code):
        self._send_input(self._keyboard(code, KEYEVENTF_UNICODE))

    # Take an array of Unicode characters
    def _key_unicode_string(self, codes):
        # This is used for anything larger
        # than UTF-16 character.
        # For example, emoji.
        # Logic is to send each input
        # and the OS should handle it.
        inputs = []
        for code in codes:
            inputs.append(self._keyboard(ord(code), KEYEVENTF_UNICODE))
        self._send_input(*inputs)

    def send_backspaces(self, number_of_backspaces):
        for _ in xrange(number_of_backspaces):
            self._key_press('backspace')

    def send_string(self, s):
        self._refresh_keyboard_layout()
        for c in self._characters(s):

            # We normalize characters
            # Like . to period, * to asterisk
            c = self.keyboard_layout.literals.get(c, c)

            # We check if we know the character
            # If we do we can do a manual keycode
            if c in self.keyboard_layout.keyname_to_keycode:
                self._key_press(c)

            # Otherwise, we send it as a Unicode character
            else:
                self._key_unicode_string(c)

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
        # Make sure keyboard layout if up-to-date.
        self._refresh_keyboard_layout()
        def name_to_code(name):
            codes = self.keyboard_layout.keyname_to_keycode.get(name, (None,))
            return codes[-1]
        # Parse and validate combo.
        key_events = parse_key_combo(combo_string, name_to_code)
        # Send events...
        for keycode, pressed in key_events:
            self._key_event(keycode, pressed)
