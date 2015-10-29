from Quartz import (
    CFMachPortCreateRunLoopSource,
    CFRunLoopAddSource,
    CFRunLoopGetCurrent,
    CFRunLoopRun,
    CFRunLoopStop,
    CGEventCreateKeyboardEvent,
    CGEventGetFlags,
    CGEventGetIntegerValueField,
    CGEventMaskBit,
    CGEventPost,
    CGEventSetFlags,
    CGEventSourceCreate,
    CGEventSourceGetSourceStateID,
    CGEventTapCreate,
    CGEventTapEnable,
    kCFRunLoopCommonModes,
    kCGEventFlagMaskAlternate,
    kCGEventFlagMaskCommand,
    kCGEventFlagMaskControl,
    kCGEventFlagMaskNonCoalesced,
    kCGEventFlagMaskShift,
    kCGEventKeyDown,
    kCGEventKeyUp,
    kCGEventSourceStateID,
    kCGEventTapOptionDefault,
    kCGHeadInsertEventTap,
    kCGKeyboardEventKeycode,
    kCGSessionEventTap,
)
import threading
import collections
import ctypes
import ctypes.util
import objc
import sys


# This mapping only works on keyboards using the ANSI standard layout. Each
# entry represents a sequence of keystrokes that are needed to achieve the
# given symbol. First, all keydown events are sent, in order, and then all
# keyup events are send in reverse order.
KEYNAME_TO_KEYCODE = collections.defaultdict(list, {
    # The order follows that of the plover guide.
    # Keycodes from http://forums.macrumors.com/showthread.php?t=780577
    '0': [29], '1': [18], '2': [19], '3': [20], '4': [21], '5': [23],
    '6': [22], '7': [26], '8': [28], '9': [25],

    'a': [0], 'b': [11], 'c': [8], 'd': [2], 'e': [14], 'f': [3], 'g': [5],
    'h': [4], 'i': [34], 'j': [38], 'k': [40], 'l': [37], 'm': [46], 'n': [45],
    'o': [31], 'p': [35], 'q': [12], 'r': [15], 's': [1], 't': [17], 'u': [32],
    'v': [9], 'w': [13], 'x': [7], 'y': [16], 'z': [6],

    'A': [56, 0], 'B': [56, 11], 'C': [56, 8], 'D': [56, 2], 'E': [56, 14],
    'F': [56, 3], 'G': [56, 5], 'H': [56, 4], 'I': [56, 34], 'J': [56, 38],
    'K': [56, 40], 'L': [56, 37], 'M': [56, 46], 'N': [56, 45], 'O': [56, 31],
    'P': [56, 35], 'Q': [56, 12], 'R': [56, 15], 'S': [56, 1], 'T': [56, 17],
    'U': [56, 32], 'V': [56, 9], 'W': [56, 13], 'X': [56, 7], 'Y': [56, 16],
    'Z': [56, 6],

    'Alt_L': [58], 'Alt_R': [61], 'Control_L': [59], 'Control_R': [62],
    'Hyper_L': [], 'Hyper_R': [], 'Meta_L': [], 'Meta_R': [],
    'Shift_L': [56], 'Shift_R': [60], 'Super_L': [55], 'Super_R': [55],

    'Caps_Lock': [57], 'Num_Lock': [], 'Scroll_Lock': [], 'Shift_Lock': [],

    'Return': [36], 'Tab': [48], 'BackSpace': [51], 'Delete': [117],
    'Escape': [53], 'Break': [], 'Insert': [], 'Pause': [], 'Print': [],
    'Sys_Req': [],

    'Up': [126], 'Down': [125], 'Left': [123], 'Right': [124],
    'Page_Up': [116],
    'Page_Down': [121], 'Home': [115], 'End': [119],

    'F1': [122], 'F2': [120], 'F3': [99], 'F4': [118], 'F5': [96], 'F6': [97],
    'F7': [98], 'F8': [100], 'F9': [101], 'F10': [109], 'F11': [103],
    'F12': [111], 'F13': [105], 'F14': [107], 'F15': [113], 'F16': [106],
    'F17': [64], 'F18': [79], 'F19': [80], 'F20': [90], 'F21': [], 'F22': [],
    'F23': [], 'F24': [], 'F25': [], 'F26': [], 'F27': [], 'F28': [],
    'F29': [], 'F30': [], 'F31': [], 'F32': [], 'F33': [], 'F34': [],
    'F35': [],

    'L1': [], 'L2': [], 'L3': [], 'L4': [], 'L5': [], 'L6': [],
    'L7': [], 'L8': [], 'L9': [], 'L10': [],

    'R1': [], 'R2': [], 'R3': [], 'R4': [], 'R5': [], 'R6': [],
    'R7': [], 'R8': [], 'R9': [], 'R10': [], 'R11': [], 'R12': [],
    'R13': [], 'R14': [], 'R15': [],

    'KP_0': [82], 'KP_1': [83], 'KP_2': [84], 'KP_3': [85], 'KP_4': [86],
    'KP_5': [87], 'KP_6': [88], 'KP_7': [89], 'KP_8': [91], 'KP_9': [92],
    'KP_Add': [69], 'KP_Begin': [], 'KP_Decimal': [65], 'KP_Delete': [71],
    'KP_Divide': [75], 'KP_Down': [], 'KP_End': [], 'KP_Enter': [76],
    'KP_Equal': [81], 'KP_F1': [], 'KP_F2': [], 'KP_F3': [], 'KP_F4': [],
    'KP_Home': [], 'KP_Insert': [], 'KP_Left': [], 'KP_Multiply': [67],
    'KP_Next': [], 'KP_Page_Down': [], 'KP_Page_Up': [], 'KP_Prior': [],
    'KP_Right': [], 'KP_Separator': [], 'KP_Space': [], 'KP_Subtract': [78],
    'KP_Tab': [], 'KP_Up': [],

    'ampersand': [56, 26], 'apostrophe': [39], 'asciitilde': [56, 50],
    'asterisk': [56, 28], 'at': [56, 19], 'backslash': [42],
    'braceleft': [56, 33], 'braceright': [56, 30], 'bracketleft': [33],
    'bracketright': [30], 'colon': [56, 41], 'comma': [43], 'division': [],
    'dollar': [56, 21], 'equal': [24], 'exclam': [56, 18], 'greater': [56, 47],
    'hyphen': [], 'less': [56, 43], 'minus': [27], 'multiply': [],
    'numbersign': [56, 20], 'parenleft': [56, 25], 'parenright': [56, 29],
    'percent': [56, 23], 'period': [47], 'plus': [56, 24],
    'question': [56, 44], 'quotedbl': [56, 39], 'quoteleft': [],
    'quoteright': [], 'semicolon': [41], 'slash': [44], 'space': [49],
    'underscore': [56, 27],

    # Many of these are possible but I haven't filled them in because it's a
    # pain to do so. Others are only possible with multiple keypresses and
    # releases making it impossible to do as a keycombo.

    'AE': [], 'Aacute': [], 'Acircumflex': [], 'Adiaeresis': [],
    'Agrave': [], 'Aring': [], 'Atilde': [], 'Ccedilla': [], 'Eacute': [],
    'Ecircumflex': [], 'Ediaeresis': [], 'Egrave': [], 'Eth': [],
    'ETH': [], 'Iacute': [], 'Icircumflex': [], 'Idiaeresis': [],
    'Igrave': [], 'Ntilde': [], 'Oacute': [], 'Ocircumflex': [],
    'Odiaeresis': [], 'Ograve': [], 'Ooblique': [], 'Otilde': [],
    'THORN': [], 'Thorn': [], 'Uacute': [], 'Ucircumflex': [],
    'Udiaeresis': [], 'Ugrave': [], 'Yacute': [],

    'ae': [], 'aacute': [], 'acircumflex': [], 'acute': [],
    'adiaeresis': [], 'agrave': [], 'aring': [], 'atilde': [],
    'ccedilla': [], 'eacute': [], 'ecircumflex': [], 'ediaeresis': [],
    'egrave': [], 'eth': [], 'iacute': [], 'icircumflex': [],
    'idiaeresis': [], 'igrave': [], 'ntilde': [], 'oacute': [],
    'ocircumflex': [], 'odiaeresis': [], 'ograve': [], 'oslash': [],
    'otilde': [], 'thorn': [], 'uacute': [], 'ucircumflex': [],
    'udiaeresis': [], 'ugrave': [], 'yacute': [], 'ydiaeresis': [],

    'cedilla': [], 'diaeresis': [], 'grave': [50], 'asciicircum': [56, 22],
    'bar': [56, 42], 'brokenbar': [], 'cent': [], 'copyright': [],
    'currency': [], 'degree': [], 'exclamdown': [], 'guillemotleft': [],
    'guillemotright': [], 'macron': [], 'masculine': [], 'mu': [],
    'nobreakspace': [], 'notsign': [], 'onehalf': [], 'onequarter': [],
    'onesuperior': [], 'ordfeminine': [], 'paragraph': [],
    'periodcentered': [], 'plusminus': [], 'questiondown': [],
    'registered': [], 'script_switch': [], 'section': [], 'ssharp': [],
    'sterling': [], 'threequarters': [], 'threesuperior': [],
    'twosuperior': [], 'yen': [],

    'Begin': [], 'Cancel': [], 'Clear': [], 'Execute': [], 'Find': [],
    'Help': [114], 'Linefeed': [], 'Menu': [], 'Mode_switch': [58],
    'Multi_key': [], 'MultipleCandidate': [], 'Next': [],
    'PreviousCandidate': [], 'Prior': [], 'Redo': [], 'Select': [],
    'SingleCandidate': [], 'Undo': [],

    'Eisu_Shift': [], 'Eisu_toggle': [], 'Hankaku': [], 'Henkan': [],
    'Henkan_Mode': [], 'Hiragana': [], 'Hiragana_Katakana': [],
    'Kana_Lock': [], 'Kana_Shift': [], 'Kanji': [], 'Katakana': [],
    'Mae_Koho': [], 'Massyo': [], 'Muhenkan': [], 'Romaji': [],
    'Touroku': [], 'Zen_Koho': [], 'Zenkaku': [], 'Zenkaku_Hankaku': [],
})


def down(seq):
    return [(x, True) for x in seq]


def up(seq):
    return [(x, False) for x in reversed(seq)]


def down_up(seq):
    return down(seq) + up(seq)

# Maps from literal characters to their key names.
LITERALS = collections.defaultdict(str, {
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
    '7': '7', '8': '8', '9': '9',

    'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e', 'f': 'f', 'g': 'g',
    'h': 'h', 'i': 'i', 'j': 'j', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n',
    'o': 'o', 'p': 'p', 'q': 'q', 'r': 'r', 's': 's', 't': 't', 'u': 'u',
    'v': 'v', 'w': 'w', 'x': 'x', 'y': 'y', 'z': 'z',

    'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G',
    'H': 'H', 'I': 'I', 'J': 'J', 'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N',
    'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R', 'S': 'S', 'T': 'T', 'U': 'U',
    'V': 'V', 'W': 'W', 'X': 'X', 'Y': 'Y', 'Z': 'Z',

    '`': 'grave', '~': 'asciitilde', '!': 'exclam', '@': 'at',
    '#': 'numbersign', '$': 'dollar', '%': 'percent', '^': 'asciicircum',
    '&': 'ampersand', '*': 'asterisk', '(': 'parenleft', ')': 'parenright',
    '-': 'minus', '_': 'underscore', '=': 'equal', '+': 'plus',
    '[': 'bracketleft', ']': 'bracketright', '{': 'braceleft',
    '}': 'braceright', '\\': 'backslash', '|': 'bar', ';': 'semicolon',
    ':': 'colon', '\'': 'apostrophe', '"': 'quotedbl', ',': 'comma',
    '<': 'less', '.': 'period', '>': 'greater', '/': 'slash',
    '?': 'question', '\t': 'Tab', ' ': 'space'
})

# Maps from keycodes to corresponding event masks.
MODIFIER_KEYS_TO_MASKS = {
    58: kCGEventFlagMaskAlternate,
    61: kCGEventFlagMaskAlternate,
    59: kCGEventFlagMaskControl,
    62: kCGEventFlagMaskControl,
    56: kCGEventFlagMaskShift,
    60: kCGEventFlagMaskShift,
    55: kCGEventFlagMaskCommand
}

# kCGEventSourceStatePrivate is -1 but when -1 is passed in here it is
# unmarshalled incorrectly as 10379842816535691263.
MY_EVENT_SOURCE = CGEventSourceCreate(0xFFFFFFFF)  # 32 bit -1
MY_EVENT_SOURCE_ID = CGEventSourceGetSourceStateID(MY_EVENT_SOURCE)

# For the purposes of this class, we're only watching these keys.
KEYCODE_TO_KEY = {
    122: 'F1', 120: 'F2', 99: 'F3', 118: 'F4', 96: 'F5', 97: 'F6', 98: 'F7', 100: 'F8', 101: 'F9', 109: 'F10', 103: 'F11', 111: 'F12',
    50: '`', 29: '0', 18: '1', 19: '2', 20: '3', 21: '4', 23: '5', 22: '6', 26: '7', 28: '8', 25: '9', 27: '-', 24: '=',
    12: 'q', 13: 'w', 14: 'e', 15: 'r', 17: 't', 16: 'y', 32: 'u', 34: 'i', 31: 'o',  35: 'p', 33: '[', 30: ']', 42: '\\',
    0: 'a', 1: 's', 2: 'd', 3: 'f', 5: 'g', 4: 'h', 38: 'j', 40: 'k', 37: 'l', 41: ';', 39: '\'',
    6: 'z', 7: 'x', 8: 'c', 9: 'v', 11: 'b', 45: 'n', 46: 'm', 43: ',', 47: '.', 44: '/',
    49: ' ',
}

class KeyboardCapture(threading.Thread):
    """Implementation of KeyboardCapture for OSX."""

    _KEYBOARD_EVENTS = set([kCGEventKeyDown, kCGEventKeyUp])

    def __init__(self):
        threading.Thread.__init__(self)
        self._running_thread = None
        self.suppress_keyboard(True)

        # Returning the event means that it is passed on for further processing by others. 
        # Returning None means that the event is intercepted.
        def callback(proxy, event_type, event, reference):
            # Don't pass on meta events meant for this event tap.
            if event_type not in self._KEYBOARD_EVENTS:
                return None
            # Don't intercept events from this module.
            if (CGEventGetIntegerValueField(event, kCGEventSourceStateID) ==
                MY_EVENT_SOURCE_ID):
                return event
            # Don't intercept the event if it has modifiers.
            if CGEventGetFlags(event) & ~kCGEventFlagMaskNonCoalesced:
                return event
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            key = KEYCODE_TO_KEY.get(keycode, None)
            if key is not None:
                handler_name = 'key_up' if event_type == kCGEventKeyUp else 'key_down'
                handler = getattr(self, handler_name, lambda event: None)
                handler(key)
                if self.is_keyboard_suppressed():
                    # Supress event.
                    event = None
            return event

        self._tap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionDefault,
            CGEventMaskBit(kCGEventKeyDown) | CGEventMaskBit(kCGEventKeyUp),
            callback, None)
        if self._tap is None:
            # Todo(hesky): See if there is a nice way to show the user what's
            # needed (or do it for them).
            raise Exception("Enable access for assistive devices.")
        self._source = CFMachPortCreateRunLoopSource(None, self._tap, 0)
        CGEventTapEnable(self._tap, False)

    def run(self):
        self._running_thread = CFRunLoopGetCurrent()
        CFRunLoopAddSource(self._running_thread, self._source,
            kCFRunLoopCommonModes)
        CGEventTapEnable(self._tap, True)
        CFRunLoopRun()

    def cancel(self):
        CGEventTapEnable(self._tap, False)
        CFRunLoopStop(self._running_thread)

    def can_suppress_keyboard(self):
        return True

    def suppress_keyboard(self, suppress):
        self._suppress_keyboard = suppress

    def is_keyboard_suppressed(self):
        return self._suppress_keyboard


# "Narrow python" unicode objects store chracters in UTF-16 so we 
# can't iterate over characters in the standard way. This workaround 
# let's us iterate over full characters in the string.
def characters(s):
    encoded = s.encode('utf-32-be')
    characters = []
    for i in xrange(len(encoded)/4):
        start = i * 4
        end = start + 4
        character = encoded[start:end].decode('utf-32-be')
        yield character

CGEventKeyboardSetUnicodeString = ctypes.cdll.LoadLibrary(ctypes.util.find_library('ApplicationServices')).CGEventKeyboardSetUnicodeString
CGEventKeyboardSetUnicodeString.restype = None
native_utf16 = 'utf-16-le' if sys.byteorder == 'little' else 'utf-16-be'

def set_string(event, s):
    buf = s.encode(native_utf16)
    CGEventKeyboardSetUnicodeString(objc.pyobjc_id(event), len(buf) / 2, buf)

class KeyboardEmulation(object):

    def __init__(self):
        pass

    def send_backspaces(self, number_of_backspaces):
        for _ in xrange(number_of_backspaces):
            CGEventPost(kCGSessionEventTap,
                CGEventCreateKeyboardEvent(MY_EVENT_SOURCE, 51, True))
            CGEventPost(kCGSessionEventTap,
                CGEventCreateKeyboardEvent(MY_EVENT_SOURCE, 51, False))

    def send_string(self, s):
        for c in characters(s):
            event = CGEventCreateKeyboardEvent(MY_EVENT_SOURCE, 0, True)
            set_string(event, c)
            CGEventPost(kCGSessionEventTap, event)
            event = CGEventCreateKeyboardEvent(MY_EVENT_SOURCE, 0, False)
            set_string(event, c)
            CGEventPost(kCGSessionEventTap, event)

    def send_key_combination(self, combo_string):
        """Emulate a sequence of key combinations.

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
        # that, if executed in order, would emulate the key combination
        # represented by the argument.
        keycode_events = []
        key_down_stack = []
        current_command = []
        for c in combo_string:
            if c in (' ', '(', ')'):
                keystring = ''.join(current_command)
                current_command = []
                seq = KEYNAME_TO_KEYCODE[keystring]
                if c == ' ':
                    # Record press and release for command's keys.
                    keycode_events.extend(down_up(seq))
                elif c == '(':
                    # Record press for command's key.
                    keycode_events.extend(down(seq))
                    key_down_stack.append(seq)
                elif c == ')':
                    # Record press and release for command's key and
                    # release previously held keys.
                    keycode_events.extend(down_up(seq))
                    if key_down_stack:
                        keycode_events.extend(up(key_down_stack.pop()))
            else:
                current_command.append(c)
        # Record final command key.
        keystring = ''.join(current_command)
        seq = KEYNAME_TO_KEYCODE[keystring]
        keycode_events.extend(down_up(seq))
        # Release all keys.
        # Should this be legal in the dict (lack of closing parens)?
        for seq in key_down_stack:
            keycode_events.extend(up(seq))

        # Emulate the key combination by sending key events.
        self._send_sequence(keycode_events)

    def _send_sequence(self, sequence):
        # There is a bug in the event system that seems to cause inconsistent
        # modifiers on key events:
        # http://stackoverflow.com/questions/2008126/cgeventpost-possible-bug-when-simulating-keyboard-events
        # My solution is to manage the state myself.
        # I'm not sure how to deal with caps lock.
        # If event_mask is not zero at the end then bad things might happen.
        event_mask = 0
        for keycode, key_down in sequence:
            if not key_down and keycode in MODIFIER_KEYS_TO_MASKS:
                event_mask &= ~MODIFIER_KEYS_TO_MASKS[keycode]
            event = CGEventCreateKeyboardEvent(
                MY_EVENT_SOURCE, keycode, key_down)
            CGEventSetFlags(event, event_mask)
            CGEventPost(kCGSessionEventTap, event)
            if key_down and keycode in MODIFIER_KEYS_TO_MASKS:
                event_mask |= MODIFIER_KEYS_TO_MASKS[keycode]

