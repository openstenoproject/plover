# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Author: @abarnert, @willwade, and @morinted
# Code taken and modified from
# <https://github.com/willwade/PyUserInput/blob/master/pykeyboard/mac_keycode.py>
# <https://stackoverflow.com/questions/1918841/how-to-convert-ascii-character-to-cgkeycode>

import ctypes
import ctypes.util
import struct
import unicodedata
import re
from threading import Thread
from collections import OrderedDict
import AppKit
import Foundation
from PyObjCTools import AppHelper
from plover.key_combo import CHAR_TO_KEYNAME
from plover.misc import popcount32

try:
    unichr
except NameError:
    unichr = chr

carbon_path = ctypes.util.find_library('Carbon')
carbon = ctypes.cdll.LoadLibrary(carbon_path)

CFIndex = ctypes.c_int64


class CFRange(ctypes.Structure):
    _fields_ = [('loc', CFIndex),
                ('len', CFIndex)]

carbon.TISCopyCurrentKeyboardInputSource.argtypes = []
carbon.TISCopyCurrentKeyboardInputSource.restype = ctypes.c_void_p
carbon.TISGetInputSourceProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
carbon.TISGetInputSourceProperty.restype = ctypes.c_void_p
carbon.LMGetKbdType.argtypes = []
carbon.LMGetKbdType.restype = ctypes.c_uint32
carbon.CFDataGetLength.argtypes = [ctypes.c_void_p]
carbon.CFDataGetLength.restype = ctypes.c_uint64
carbon.CFDataGetBytes.argtypes = [ctypes.c_void_p, CFRange, ctypes.c_void_p]
carbon.CFDataGetBytes.restype = None
carbon.CFRelease.argtypes = [ctypes.c_void_p]
carbon.CFRelease.restype = None

kTISPropertyUnicodeKeyLayoutData = ctypes.c_void_p.in_dll(
    carbon, 'kTISPropertyUnicodeKeyLayoutData')
kTISPropertyInputSourceID = ctypes.c_void_p.in_dll(
    carbon, 'kTISPropertyInputSourceID')
COMMAND   = u'⌘'
SHIFT     = u'⇧'
OPTION    = u'⌥'
CONTROL   = u'⌃'
CAPS      = u'⇪'
UNKNOWN   = u'?'
UNKNOWN_L = u'?_L'

KEY_CODE_VISUALIZATION = """
┌───────────────────Layout of Apple Extended Keyboard II───────────────────────┐
│ 53  122 120 99 118  96 97 98 100  101 109 103 111   105 107 113              │
│                                                                              │
│ 50─── 18 19 20 21 23 22 26 28 25 29 27 24 ─────51   114 115 116  71 81 75 67 │
│ 48──── 12 13 14 15 17 16 32 34 31 35 33 30 ────42   117 119 121  89 91 92 78 │
│ 57───── 0  1  2  3  5  4  38 40 37 41 39 ──────36                86 87 88 69 │
│ 56────── 6  7  8  9  11 45 46  43 47 44 ───────56       126      83 84 85 76 │
│ 59── 58─ 55─ ──────────49───────── ─55 ──58 ───59   123 125 124  82─── 65 76 │
└──────────────────────────────────────────────────────────────────────────────┘
Valid keycodes not visible on layout:
  10, 52, 54, 60-64, 66, 68, 70, 72-74, 77, 79, 80,
  90, 93-95, 102, 104, 106, 108, 110, 112, 127
"""

SPECIAL_KEY_NAMES = {
    u'\x1b': u'Esc',   # Will map both Esc and Clear (key codes 53 and 71)
    u'\xa0': u'nbsp',
    u'\x08': u'Bksp',
    u'\x05': u'Help',
    u'\x01': u'Home',
    u'\x7f': u'Del',
    u'\x04': u'End',
    u'\x0c': u'PgDn',
    u'\x0b': u'PgUp',  # \x0b is also the clear character signal
}


def is_printable(string):
    for character in string:
        category = unicodedata.category(character)
        if category[0] in 'C':
            # Exception: the "Apple" character that most Mac layouts have
            return False if string != u"" else True
        elif category == 'Zs' and character != ' ':
            return False
        elif category in 'Zl, Zp':
            return False
    return True


def get_printable_string(s):
    return s if is_printable(s) else SPECIAL_KEY_NAMES.setdefault(
        s, s.encode('unicode_escape').decode("utf-8")
    )


class KeyboardLayout(object):
    def __init__(self, watch_layout=True):
        self._char_to_key_sequence = None
        self._key_sequence_to_char = None
        self._modifier_masks = None

        # Spawn a thread that responds to system keyboard layout changes.
        if watch_layout:
            self._watcher = Thread(
                target=self._layout_watcher,
                name="LayoutWatcher")
            self._watcher.start()

        self.update_layout()

    def _layout_watcher(self):
        layout = self

        class LayoutWatchingCallback(AppKit.NSObject):
            def layoutChanged_(self, event):
                layout.update_layout()

        center = Foundation.NSDistributedNotificationCenter.defaultCenter()
        LayoutWatchingCallback = LayoutWatchingCallback.new()
        center.addObserver_selector_name_object_(
            LayoutWatchingCallback,
            'layoutChanged:',
            'AppleSelectedInputSourcesChangedNotification',
            None
        )
        AppHelper.runConsoleEventLoop(installInterrupt=True)

    def update_layout(self):
        char_to_key_sequence, key_sequence_to_char, modifier_masks = KeyboardLayout.get_layout()
        self._char_to_key_sequence = char_to_key_sequence
        self._key_sequence_to_char = key_sequence_to_char
        self._modifier_masks = modifier_masks

    def key_code_to_char(self, key_code, modifier=0):
        """Provide a key code and a modifier and it provides the character"""
        return get_printable_string(self._key_sequence_to_char[key_code, modifier])

    def char_to_key_sequence(self, char):
        """Finds the key code and modifier sequence for the character"""
        key_sequence = self._char_to_key_sequence.get(char, (None, 0))
        if key_sequence is None or key_sequence[0] is None:
            return [(None, 0)]
        else:
            if not isinstance(key_sequence[0], tuple):
                key_sequence = key_sequence,
            return key_sequence

    def format_modifier_header(self):
        modifiers = (u'| {}\t'.format(KeyboardLayout.modifier_string(mod)).expandtabs(8)
                     for mod in sorted(self._modifier_masks.values()))
        header = u'Keycode\t{}'.format(''.join(modifiers))
        return '%s\n%s' % (header, re.sub(r'[^|]', '-', header))

    def format_keycode_keys(self, keycode):
        """Prints all the variations of the keycode with modifiers"""
        keys = (u'| {}\t'.format(get_printable_string(self._key_sequence_to_char[keycode, mod])).expandtabs(8)
                for mod in sorted(self._modifier_masks.values()))

        return u'{}\t{}'.format(keycode, ''.join(keys)).expandtabs(8)

    @staticmethod
    def mods(mod):
        """Provide a dictionary of active modifier keys from mod mask"""
        modifiers = {
            SHIFT: False,
            COMMAND: False,
            CONTROL: False,
            OPTION:False,
            CAPS: False,
            UNKNOWN: False,
            UNKNOWN_L: False
        }
        if mod & 16:
            modifiers[CONTROL] = True
        if mod & 8:
            modifiers[OPTION] = True
        if mod & 4:
            modifiers[CAPS] = True
        if mod & 2:
            modifiers[SHIFT] = True
        if mod & 1:
            modifiers[COMMAND] = True
        return modifiers

    @staticmethod
    def modifier_string(modifier_mask):
        """Turn modifier mask into string representing modifiers"""
        s = ''
        modifiers = KeyboardLayout.mods(modifier_mask)
        for key in modifiers:
            s += key if modifiers[key] else ''
        return s

    @staticmethod
    def get_layout():
        keyboard_input_source = carbon.TISCopyCurrentKeyboardInputSource()
        layout_source = carbon.TISGetInputSourceProperty(
            keyboard_input_source, kTISPropertyUnicodeKeyLayoutData
        )
        layout_size = carbon.CFDataGetLength(layout_source)
        layout_buffer = ctypes.create_string_buffer(b'\000' * layout_size)
        carbon.CFDataGetBytes(
            layout_source, CFRange(0, layout_size), ctypes.byref(layout_buffer)
        )
        keyboard_type = carbon.LMGetKbdType()
        parsed_layout = KeyboardLayout.parse_layout(
            layout_buffer, keyboard_type
        )
        carbon.CFRelease(keyboard_input_source)
        return parsed_layout

    @staticmethod
    def parse_layout(buf, ktype):
        hf, dv, featureinfo, ktcount = struct.unpack_from('HHII', buf)
        offset = struct.calcsize('HHII')
        ktsize = struct.calcsize('IIIIIII')
        kts = [struct.unpack_from('IIIIIII', buf, offset + ktsize * i)
               for i in range(ktcount)]
        for i, kt in enumerate(kts):
            if kt[0] <= ktype <= kt[1]:
                kentry = i
                break
        else:
            kentry = 0
        ktf, ktl, modoff, charoff, sroff, stoff, seqoff = kts[kentry]

        # Modifiers
        mf, deftable, mcount = struct.unpack_from('HHI', buf, modoff)
        modtableoff = modoff + struct.calcsize('HHI')
        modtables = struct.unpack_from('B'*mcount, buf, modtableoff)
        modifier_masks = {}
        for i, table in enumerate(modtables):
            modifier_masks.setdefault(table, i)

        # Sequences
        sequences = []
        if seqoff:
            sf, scount = struct.unpack_from('HH', buf, seqoff)
            seqtableoff = seqoff + struct.calcsize('HH')
            lastoff = -1
            for soff in struct.unpack_from('H'*scount, buf, seqtableoff):
                if lastoff >= 0:
                    sequences.append(buf[seqoff+lastoff:seqoff+soff].decode('utf-16'))
                lastoff = soff

        def lookupseq(key):
            if key >= 0xFFFE:
                return None
            if key & 0xC000:
                seq = key & ~0xC000
                if seq < len(sequences):
                    return sequences[seq]
            return unichr(key)

        # Dead keys
        deadkeys = []
        if sroff:
            srf, srcount = struct.unpack_from('HH', buf, sroff)
            srtableoff = sroff + struct.calcsize('HH')
            for recoff in struct.unpack_from('I'*srcount, buf, srtableoff):
                cdata, nextstate, ecount, eformat = struct.unpack_from('HHHH', buf, recoff)
                recdataoff = recoff + struct.calcsize('HHHH')
                edata = buf[recdataoff:recdataoff+4*ecount]
                deadkeys.append((cdata, nextstate, ecount, eformat, edata))

        if stoff:
            stf, stcount = struct.unpack_from('HH', buf, stoff)
            sttableoff = stoff + struct.calcsize('HH')
            dkterms = struct.unpack_from('H'*stcount, buf, sttableoff)
        else:
            dkterms = []

        # Get char tables
        char_to_key_sequence = {}
        key_sequence_to_char = {}

        deadkey_state_to_key_sequence = {}
        key_sequence_to_deadkey_state = {}

        def save_shortest_key_sequence(character, new_sequence):
            current_sequence = char_to_key_sequence.setdefault(character, new_sequence)
            if current_sequence != new_sequence:
                # Convert responses to tuples...
                if not isinstance(current_sequence[0], tuple):
                    current_sequence = current_sequence,
                if not isinstance(new_sequence[0], tuple):
                    new_sequence = new_sequence,

                # Favor shortest sequence (fewer separate key presses)
                if len(current_sequence) < len(new_sequence):
                    return
                elif len(new_sequence) < len(current_sequence):
                    char_to_key_sequence[character] = new_sequence[0]
                # Favor fewer modifiers on last item
                elif popcount32(new_sequence[-1][1]) < popcount32(current_sequence[-1][1]):
                    char_to_key_sequence[character] = new_sequence
                # Favor lower modifiers on first item if last item is the same
                elif (popcount32(new_sequence[-1][1]) == popcount32(current_sequence[-1][1]) and
                      popcount32(new_sequence[0][1]) < popcount32(current_sequence[0][1])):
                    char_to_key_sequence[character] = new_sequence

        def lookup_and_add(key, j, mod):
            ch = lookupseq(key)
            save_shortest_key_sequence(ch, (j, mod))
            key_sequence_to_char[j, mod] = ch

        cf, csize, ccount = struct.unpack_from('HHI', buf, charoff)
        chartableoff = charoff + struct.calcsize('HHI')

        for i, table_offset in enumerate(struct.unpack_from('I' * ccount, buf, chartableoff)):
            mod = modifier_masks[i]
            for j, key in enumerate(struct.unpack_from('H'*csize, buf, table_offset)):
                if key == 65535:
                    key_sequence_to_char[j, mod] = u'mod'
                elif key >= 0xFFFE:
                    key_sequence_to_char[j, mod] = u'<{}>'.format(key)
                elif key & 0x0C000 == 0x4000:
                    dead = key & ~0xC000
                    if dead < len(deadkeys):
                        cdata, nextstate, ecount, eformat, edata = deadkeys[dead]
                        if eformat == 0 and nextstate: # initial
                            deadkey_state_to_key_sequence[nextstate] = (j, mod)
                            if nextstate-1 < len(dkterms):
                                basekey = lookupseq(dkterms[nextstate-1])
                                key_sequence_to_char[j, mod] = u'dk {}'.format(basekey)
                            else:
                                key_sequence_to_char[j, mod] = u'DK#{}'.format(nextstate)
                        elif eformat == 1:  # terminal
                            key_sequence_to_deadkey_state[j, mod] = deadkeys[dead]
                            lookup_and_add(cdata, j, mod)
                        elif eformat == 2:  # range
                            # TODO!
                            pass
                else:
                    lookup_and_add(key, j, mod)

        for key, dead in key_sequence_to_deadkey_state.items():
            j, mod = key
            cdata, nextstate, ecount, eformat, edata = dead
            entries = [struct.unpack_from('HH', edata, i*4) for i in range(ecount)]
            for state, key in entries:
                dj, dmod = deadkey_state_to_key_sequence[state]
                ch = lookupseq(key)
                save_shortest_key_sequence(ch, ((dj, dmod), (j, mod)))
                key_sequence_to_char[(dj, dmod), (j, mod)] = ch

        char_to_key_sequence[u'\n'] = (36, 0)
        char_to_key_sequence[u'\r'] = (36, 0)
        char_to_key_sequence[u'\t'] = (48, 0)

        return char_to_key_sequence, key_sequence_to_char, modifier_masks

if __name__ == '__main__':
    layout = KeyboardLayout(watch_layout=False)
    print KEY_CODE_VISUALIZATION
    print
    print layout.format_modifier_header()
    for keycode in range(127):
        print layout.format_keycode_keys(keycode)
    print
    unmapped_characters = []
    for char, keyname in sorted(CHAR_TO_KEYNAME.iteritems()):
        sequence = OrderedDict()
        for code, mod in layout.char_to_key_sequence(char):
            if code is not None:
                sequence[str(code)] = u'{}{}'.format(
                    layout.modifier_string(mod),
                    layout.key_code_to_char(code, 0)
                )
            else:
                unmapped_characters.append(char)
        if sequence:
            print u'Name:\t\t{}\nCharacter:\t{}\nSequence:\t‘{}’\nBase codes:\t‘{}’\n'.format(
                keyname, char, u'’, ‘'.join(sequence.values()), u'’, ‘'.join(sequence.keys())
            )
    print u'No mapping on this layout for characters: ‘{}’'.format(u'’, ‘'.join(unmapped_characters))

