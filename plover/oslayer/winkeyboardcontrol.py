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
import functools
import threading
import types
import win32api
import pyHook

SendInput = ctypes.windll.user32.SendInput
MapVirtualKey = ctypes.windll.user32.MapVirtualKeyW
GetKeyboardLayout = ctypes.windll.user32.GetKeyboardLayout
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

# Global state used by KeyboardCapture to support multiple instances.

class HookManager(object):

    def __init__(self):
        self._lock = threading.Lock()
        self._hm = pyHook.HookManager()
        self._key_down_callbacks = []
        self._key_up_callbacks = []
        self._nb_callbacks = 0

        def _on_key_event(callback_list, event):
            if event.Injected:
                return True
            with self._lock:
                callback_list = list(callback_list)
            allow = True
            for callback in callback_list:
                allow = callback(event) and allow
            return allow

        self._hm.KeyUp = functools.partial(_on_key_event, self._key_up_callbacks)
        self._hm.KeyDown = functools.partial(_on_key_event, self._key_down_callbacks)

        def _set_key_callback(callback_list, enable, callback):
            with self._lock:
                if enable:
                    assert callback not in callback_list
                    callback_list.append(callback)
                    self._nb_callbacks += 1
                    if 1 == self._nb_callbacks:
                        self._hm.HookKeyboard()
                else:
                    assert callback in callback_list
                    callback_list.remove(callback)
                    self._nb_callbacks -= 1
                    if 0 == self._nb_callbacks:
                        self._hm.UnhookKeyboard()

        self.register_key_up = functools.partial(_set_key_callback,
                                                 self._key_up_callbacks,
                                                 True)
        self.unregister_key_up = functools.partial(_set_key_callback,
                                                   self._key_up_callbacks,
                                                   False)
        self.register_key_down = functools.partial(_set_key_callback,
                                                   self._key_down_callbacks,
                                                   True)
        self.unregister_key_down = functools.partial(_set_key_callback,
                                                     self._key_down_callbacks,
                                                     False)

_hook_manager = HookManager()

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
    keyname_to_keycode = collections.defaultdict(list, {
        # Adding media controls for windows
        'Vol_Mute': [0xAD], 'Vol_Down': [0xAE], 'Vol_Up': [0xAF],
        'Media_Next': [0xB0], 'Media_Prev': [0xB1], 'Media_Stop': [0xB2],
        'Media_Play_Pause': [0xB3], 'Sleep': [0x5F],

        'Alt_L': [0xA4], 'Alt_R': [0xA5], 'Control_L': [0xA2], 'Control_R': [0xA3],
        'Hyper_L': [], 'Hyper_R': [], 'Meta_L': [], 'Meta_R': [],
        'Shift_L': [0xA0], 'Shift_R': [0xA1], 'Super_L': [0x5B], 'Super_R': [0x5C],

        'Caps_Lock': [0x14], 'Num_Lock': [0x90], 'Scroll_Lock': [0x91],
        'Shift_Lock': [],

        'Return': [0x0D], 'Tab': [0x09], 'BackSpace': [0x08], 'Delete': [0x2E],
        'Escape': [0x1B], 'Break': [0x03], 'Insert': [0x2D], 'Pause': [0x13],
        'Print': [0x2C], 'Sys_Req': [],

        'Up': [0x26], 'Down': [0x28], 'Left': [0x25], 'Right': [0x27],
        'Page_Up': [0x21], 'Page_Down': [0x22], 'Home': [0x24], 'End': [0x23],

        'F1': [0x70], 'F2': [0x71], 'F3': [0x72], 'F4': [0x73], 'F5': [0x74],
        'F6': [0x75], 'F7': [0x76], 'F8': [0x77], 'F9': [0x78], 'F10': [0x79],
        'F11': [0x7A], 'F12': [0x7B], 'F13': [0x7C], 'F14': [0x7D], 'F15': [0x7E],
        'F16': [0x7F], 'F17': [0x80], 'F18': [0x81], 'F19': [0x82], 'F20': [0x83],
        'F21': [0x84], 'F22': [0x85], 'F23': [0x86], 'F24': [0x87], 'F25': [],
        'F26': [], 'F27': [], 'F28': [], 'F29': [], 'F30': [], 'F31': [],
        'F32': [], 'F33': [], 'F34': [], 'F35': [],

        'L1': [], 'L2': [], 'L3': [], 'L4': [], 'L5': [], 'L6': [],
        'L7': [], 'L8': [], 'L9': [], 'L10': [],

        'R1': [], 'R2': [], 'R3': [], 'R4': [], 'R5': [], 'R6': [],
        'R7': [], 'R8': [], 'R9': [], 'R10': [], 'R11': [], 'R12': [],
        'R13': [], 'R14': [], 'R15': [],

        'KP_0': [0x60], 'KP_1': [0x61], 'KP_2': [0x62], 'KP_3': [0x63],
        'KP_4': [0x64], 'KP_5': [0x65], 'KP_6': [0x66], 'KP_7': [0x67],
        'KP_8': [0x68], 'KP_9': [0x69], 'KP_Add': [0xA1, 0xBB], 'KP_Begin': [],
        'KP_Decimal': [0x6E], 'KP_Delete': [0x2E], 'KP_Divide': [0x6F],
        'KP_Down': [], 'KP_End': [], 'KP_Enter': [0x0D], 'KP_Equal': [0xBB],
        'KP_F1': [], 'KP_F2': [], 'KP_F3': [], 'KP_F4': [], 'KP_Home': [],
        'KP_Insert': [], 'KP_Left': [], 'KP_Multiply': [0x6A], 'KP_Next': [],
        'KP_Page_Down': [], 'KP_Page_Up': [], 'KP_Prior': [], 'KP_Right': [],
        'KP_Separator': [], 'KP_Space': [], 'KP_Subtract': [0x6D], 'KP_Tab': [],
        'KP_Up': [],

        'Help': [0x2F], 'Mode_switch': [0x1F], 'Menu': [0x5D],

        'Begin': [], 'Cancel': [0x03], 'Clear': [0x0C], 'Execute': [0x2B],
        'Find': [], 'Linefeed': [],
        'Multi_key': [], 'MultipleCandidate': [], 'Next': [0x22],
        'PreviousCandidate': [], 'Prior': [0x21], 'Redo': [], 'Select': [0x29],
        'SingleCandidate': [], 'Undo': [],

        'Eisu_Shift': [], 'Eisu_toggle': [], 'Hankaku': [], 'Henkan': [],
        'Henkan_Mode': [], 'Hiragana': [], 'Hiragana_Katakana': [],
        'Kana_Lock': [], 'Kana_Shift': [], 'Kanji': [], 'Katakana': [],
        'Mae_Koho': [], 'Massyo': [], 'Muhenkan': [], 'Romaji': [],
        'Touroku': [], 'Zen_Koho': [], 'Zenkaku': [], 'Zenkaku_Hankaku': []
    })

    # Handle Plover's key names by mapping them to Unicode.
    keyname_to_unicode = {
        # Values of Unicode chars
        'plusminus': 177, 'aring': 229, 'yen': 165, 'ograve': 242,
        'adiaeresis': 228, 'Ntilde': 209, 'questiondown': 191, 'Yacute': 221,
        'Atilde': 195, 'ccedilla': 231, 'copyright': 169, 'ntilde': 241,
        'otilde': 245, 'masculine': 9794, 'Eacute': 201, 'ocircumflex': 244,
        'guillemotright': 187, 'ecircumflex': 234, 'uacute': 250, 'cedilla': 184,
        'oslash': 248, 'acute': 237, 'ssharp': 223, 'Igrave': 204,
        'twosuperior': 178, 'udiaeresis': 252, 'notsign': 172, 'exclamdown': 161,
        'ordfeminine': 9792, 'Otilde': 213, 'agrave': 224, 'ection': 167,
        'egrave': 232, 'macron': 175, 'Icircumflex': 206, 'diaeresis': 168,
        'ucircumflex': 251, 'atilde': 227, 'Acircumflex': 194, 'degree': 176,
        'THORN': 222, 'acircumflex': 226, 'Aring': 197, 'Ooblique': 216,
        'Ugrave': 217, 'Agrave': 192, 'ydiaeresis': 255, 'threesuperior': 179,
        'Egrave': 200, 'Idiaeresis': 207, 'igrave': 236, 'ETH': 208,
        'Ecircumflex': 202, 'Aacute': 193, 'cent': 162, 'registered': 174,
        'Oacute': 211, 'Adiaeresis': 228, 'guillemotleft': 171, 'ediaeresis': 235,
        'Ograve': 210, 'mu': 956, 'paragraph': 182, 'Ccedilla': 199, 'thorn': 254,
        'threequarters': 190, 'ae': 230, 'brokenbar': 166, 'nobreakspace': 32,
        'currency': 164, 'ugrave': 249, 'Ucircumflex': 219, 'odiaeresis': 246,
        'periodcentered': 183, 'Uacute': 218, 'idiaeresis': 239, 'yacute': 253,
        'sterling': 163, 'AE': 198, 'Ediaeresis': 203, 'onequarter': 188,
        'onehalf': 189, 'Thorn': 222, 'aacute': 225, 'icircumflex': 238,
        'Udiaeresis': 220, 'eacute': 233, 'Eth': 240, 'eth': 240, 'Iacute': 205,
        'onesuperior': 185, 'Ocircumflex': 212, 'Odiaeresis': 214, 'oacute': 243
    }

    # Maps from literal characters to their key names.
    literals = collections.defaultdict(str, {
        '~': 'asciitilde', '!': 'exclam', '@': 'at',
        '#': 'numbersign', '$': 'dollar', '%': 'percent',
        '&': 'ampersand', '*': 'asterisk', '(': 'parenleft', ')': 'parenright',
        '-': 'minus', '_': 'underscore', '=': 'equal', '+': 'plus',
        '[': 'bracketleft', ']': 'bracketright', '{': 'braceleft',
        '}': 'braceright', '\\': 'backslash', '|': 'bar', ';': 'semicolon',
        ':': 'colon', '\'': 'apostrophe', '"': 'quotedbl', ',': 'comma',
        '<': 'less', '.': 'period', '>': 'greater', '/': 'slash',
        '?': 'question', '\t': 'Tab', ' ': 'space'
    })

    def __init__(self):
        # Get active layout
        layout_id = GetKeyboardLayout(0)

        # Converts a character into a key sequence based on current layout
        # Returns a list of key codes to send *or* False to represent key not found
        def _kc(character):
            sequence = []

            # Doesn't support unicode
            if len(character) > 1:
                return []

            vk = win32api.VkKeyScanEx(character, layout_id)

            # Low bit is keycode
            kc = vk & 0xFF
            mods = vk >> 8

            # Keyboard layout does not have this key
            if kc < 0 or mods < 0:
                return []

            # High bit is modifiers
            if (mods & 1):  # Shift
                sequence.append(0xA1)
            if (mods & 2):  # Control
                sequence.append(0xA3)
            if (mods & 4):  # Alt
                sequence.append(0xA5)
            sequence.append(kc)
            return sequence

        # Add a list of keys, knowing that some keys are name-value pairs.
        def _add_keys(keycodes, characters):
            for c in characters:
                if isinstance(c, types.StringTypes):
                    _add_key(keycodes, c)
                else:
                    # Named keys (c[character, keyname])
                    _add_key(keycodes, c[1], c[0])

        # Add a single key to the be correct list.
        def _add_key(keycodes, character, keyname=False):
            if not keyname:
                keyname = character

            codes = _kc(character)
            if len(codes) > 0:
                keycodes[keyname] = codes
            elif len(character) is 1:
                self.keyname_to_unicode[keyname] = ord(character)

        # Here we add the main letters and special characters found on a standard layout.
        _add_keys(
            self.keyname_to_keycode,
            ['0', '1', '2', '3', '4', '5', '6', '7', '8',
             '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
             'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q',
             'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
             'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
             'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q',
             'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
             ['exclam', '!'], ['at', '@'],
             ['numbersign', '#'], ['dollar', '$'],
             ['percent', '%'],
             ['asciitilde', '~'], ['ampersand', '&'],
             ['asterisk', '*'], ['parenleft', '('],
             ['parenright', ')'], ['minus', '-'],
             ['underscore', '_'], ['equal', '='],
             ['plus', '+'], ['bracketleft', '['],
             ['bracketright', ']'], ['backslash', '\\'],
             ['bar', '|'], ['semicolon', ';'],
             ['colon', ':'], ['apostrophe', '\''],
             ['quotedbl', '"'], ['comma', ','],
             ['less', '<'], ['period', '.'],
             ['greater', '>'], ['slash', '/'],
             ['question', '?'], ['space', ' '],
             ['grave', '`'], ['asciicircum', '^'],
             ['braceleft', '{'], ['braceright', '}']])

        for symbol, name in self.literals.items():
            '''
            If any of the keys in the _add_keys wasn't registered, then we want to
            treat it as unicode.
            In order to do that, we will remove it from literals.
            '''
            if name not in self.keyname_to_keycode:
                del self.literals[symbol]


class KeyboardCapture(object):
    """Listen to all keyboard events."""

    CONTROL_KEYS = set(('Lcontrol', 'Rcontrol'))
    SHIFT_KEYS = set(('Lshift', 'Rshift'))
    ALT_KEYS = set(('Lmenu', 'Rmenu'))
    WIN_KEYS = set(('Lwin', 'Rwin'))
    PASSTHROUGH_KEYS = CONTROL_KEYS | SHIFT_KEYS | ALT_KEYS | WIN_KEYS

    def __init__(self):
        self._passthrough_down_keys = set()
        self._alive = False
        self._suppressed_keys = set()
        self.key_down = lambda key: None
        self.key_up = lambda key: None

        # NOTE(hesky): Does this need to be more efficient and less
        # general if it will be called for every keystroke?
        def on_key_event(func_name, event):
            if event.Key in self.PASSTHROUGH_KEYS:
                if func_name == 'key_down':
                    self._passthrough_down_keys.add(event.Key)
                elif func_name == 'key_up':
                    self._passthrough_down_keys.discard(event.Key)
            key = SCANCODE_TO_KEY.get(event.ScanCode)
            if key is not None and not self._passthrough_down_keys:
                getattr(self, func_name)(key)
                return key not in self._suppressed_keys
            return True

        self._on_key_up = functools.partial(on_key_event, 'key_up')
        self._on_key_down = functools.partial(on_key_event, 'key_down')

    def start(self):
        _hook_manager.register_key_up(self._on_key_up)
        _hook_manager.register_key_down(self._on_key_down)
        self._alive = True

    def cancel(self):
        if not self._alive:
            return
        _hook_manager.unregister_key_up(self._on_key_up)
        _hook_manager.unregister_key_down(self._on_key_down)
        # Guard against active passthrough key depressions on capture cancel.
        self._passthrough_down_keys.clear()
        self._alive = False

    def suppress_keyboard(self, suppressed_keys=()):
        self._suppressed_keys = set(suppressed_keys)


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

    # Presses a key down
    def _key_down(self, keyname):
        # Press all keys
        for keycode in self.keyboard_layout.keyname_to_keycode[keyname]:
            if keycode in EXTENDED_KEYS:
                self._send_input(self._keyboard(keycode, KEYEVENTF_EXTENDEDKEY))
            else:
                self._send_input(self._keyboard(keycode))

    # Releases a key
    def _key_up(self, keyname):
        # Release all keys
        for keycode in self.keyboard_layout.keyname_to_keycode[keyname]:
            if keycode in EXTENDED_KEYS:
                self._send_input(self._keyboard(
                    keycode, (KEYEVENTF_KEYUP | KEYEVENTF_EXTENDEDKEY)))
            else:
                self._send_input(self._keyboard(keycode, KEYEVENTF_KEYUP))

    # Press and release a key
    def _key_press(self, keyname):
        self._key_down(keyname)
        self._key_up(keyname)

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
            self._key_press("BackSpace")

    def send_string(self, s):
        for c in self._characters(s):

            # We normalize characters
            # Like . to period, * to asterisk
            if c in self.keyboard_layout.literals:
                c = self.keyboard_layout.literals[c]

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

        # We will go through and press down keys
        # When encountering (, we will add to the held stack
        # ) will release these from the stack

        # There is a problem. If the user defines something like:
        #   Shift_L(ampersand x)
        # Shift_L( will press the shift key, but ampersand will release it
        # too early. x output will be lowercase.
        # In order to combat this, ampersand and other shifted characters
        # use Shift_R as most entries seem to use Shift_L.
        # That being said, we can consider a shifted-shifted character to be
        # undefined behavior...

        key_down_stack = []
        current_command = []
        for c in combo_string:
            if c in (' ', '(', ')'):
                # Keystring is the variable (l, b, Alt_L, etc.)
                keystring = ''.join(current_command)
                # Clear out current command
                current_command = []
                is_keycode = keystring in self.keyboard_layout.keyname_to_keycode

                # Handle unicode characters by pressing them
                if keystring in self.keyboard_layout.keyname_to_unicode:
                    self._key_unicode(self.keyboard_layout.keyname_to_unicode[keystring])
                elif len(keystring) == 1 and not is_keycode:
                    self._key_unicode_string(keystring)

                if not is_keycode:
                    keystring = ''

                if c == ' ':
                    # Record press and release for command's keys.
                    if is_keycode:
                        self._key_press(keystring)
                elif c == '(':
                    # Record press for command's key.
                    if is_keycode:
                        self._key_down(keystring)
                    # We always add to the stack
                    # Even if not a valid KEYCODE or is a UNICODE
                    # Because if the user accidentally
                    # used a non-existent command,
                    # say `Shift_L(dogma(q) a)`, we still want
                    # the parenthesis count to match
                    # and output `QA`
                    key_down_stack.append(keystring)
                elif c == ')':
                    # Record press and release for command's key and
                    # release previously held keys.
                    if is_keycode:
                        self._key_press(keystring)
                    if key_down_stack:
                        # We check that the key pressed down is
                        # an actual key.
                        down_key = key_down_stack.pop()
                        if down_key in self.keyboard_layout.keyname_to_keycode:
                            self._key_up(down_key)
            else:
                current_command.append(c)

        # Record final command key.
        keystring = ''.join(current_command)
        if keystring in self.keyboard_layout.keyname_to_unicode:
            self._key_unicode(self.keyboard_layout.keyname_to_unicode[keystring])
            # Reset keystring to nothing to prevent further presses
        elif keystring in self.keyboard_layout.keyname_to_keycode:
            self._key_press(keystring)
        elif len(keystring) == 1:
            self._key_unicode_string(keystring)

        # Release all keys.
        # Should this be legal in the dict (lack of closing parens)?
        for key_name in key_down_stack:
            if key_name in self.keyboard_layout.keyname_to_keycode:
                self._key_up(key_name)

