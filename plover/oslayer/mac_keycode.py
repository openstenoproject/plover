# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Author: Will Wade
# Code taken and modified from
# <https://github.com/willwade/PyUserInput/blob/master/pykeyboard/mac_keycode.py>
# http://stackoverflow.com/questions/1918841/how-to-convert-ascii-character-to-cgkeycode */

import ctypes
import ctypes.util
import struct
import unicodedata

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

def parselayout(buf, ktype):
    hf, dv, featureinfo, ktcount = struct.unpack_from('HHII', buf)
    offset = struct.calcsize('HHII')
    ktsize = struct.calcsize('IIIIIII')
    kts = [struct.unpack_from('IIIIIII', buf, offset+ktsize*i)
           for i in range(ktcount)]
    for i, kt in enumerate(kts):
        if kt[0] <= ktype <= kt[1]:
            kentry = i
            break
    else:
        kentry = 0
    ktf, ktl, modoff, charoff, sroff, stoff, seqoff = kts[kentry]
    #for i, kt in enumerate(kts):
    #    print('{:3}-{:3}{} mods {} char {} records {} term {} seq {}'.format(
    #        kt[0], kt[1],
    #        '*' if i == kentry else ' ',
    #        kt[2], kt[3], kt[4], kt[5], kt[6]))

    # Modifiers
    mf, deftable, mcount = struct.unpack_from('HHI', buf, modoff)
    modtableoff = modoff + struct.calcsize('HHI')
    modtables = struct.unpack_from('B'*mcount, buf, modtableoff)
    modmapping = {}
    for i, table in enumerate(modtables):
        modmapping.setdefault(table, i)
    #print(modmapping)

    # Sequences
    if not seqoff:
        sequences = []
    else:
        sf, scount = struct.unpack_from('HH', buf, seqoff)
        seqtableoff = seqoff + struct.calcsize('HH')
        lastsoff = -1
        for soff in struct.unpack_from('H'*scount, buf, seqtableoff):
            if lastsoff >= 0:
                sequences.append(buf[seqoff+lastoff:seqoff+soff].decode('utf-16'))
            lastsoff = soff
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
    #for dk in deadkeys:
    #    print(dk)
    if stoff:
        stf, stcount = struct.unpack_from('HH', buf, stoff)
        sttableoff = stoff + struct.calcsize('HH')
        dkterms = struct.unpack_from('H'*stcount, buf, sttableoff)
    else:
        dkterms = []
    #print(dkterms)

    def lookup_and_add(key, j, mod):
        ch = lookupseq(key)
        if ch is not None:
            mapping.setdefault(ch, (j, mod))
            revmapping[j, mod] = ch
        elif key == 0xFFFF:
            revmapping[j, mod] = u''
        else:
            revmapping[j, mod] = u'<{}>'.format(key)

    # Get char tables
    cf, csize, ccount = struct.unpack_from('HHI', buf, charoff)
    chartableoff = charoff + struct.calcsize('HHI')
    mapping = {}
    revmapping = {}
    deadstatemapping = {}
    deadrevmapping = {}
    for i, tableoff in enumerate(struct.unpack_from('I'*ccount, buf, chartableoff)):
        mod = modmapping[i]
        for j, key in enumerate(struct.unpack_from('H'*csize, buf, tableoff)):
            ch = None
            if key >= 0xFFFE:
                revmapping[j, mod] = u'<{}>'.format(key)
            elif key & 0x0C000 == 0x4000:
                dead = key & ~0xC000
                if dead < len(deadkeys):
                    cdata, nextstate, ecount, eformat, edata = deadkeys[dead]
                    if eformat == 0 and nextstate: # initial
                        deadstatemapping[nextstate] = (j, mod)
                        if nextstate-1 < len(dkterms):
                            basekey = lookupseq(dkterms[nextstate-1])
                            revmapping[j, mod] = u'<deadkey #{}: {}>'.format(nextstate, basekey)
                        else:
                            revmapping[j, mod] = u'<deadkey #{}>'.format(nextstate)
                    elif eformat == 1: # terminal
                        deadrevmapping[j, mod] = deadkeys[dead]
                        lookup_and_add(cdata, j, mod)
                    elif eformat == 2: # range
                        # TODO!
                        pass
            else:
                lookup_and_add(key, j, mod)

    for key, dead in deadrevmapping.items():
        j, mod = key
        cdata, nextstate, ecount, eformat, edata = dead
        entries = [struct.unpack_from('HH', edata, i*4) for i in range(ecount)]
        for state, key in entries:
            dj, dmod = deadstatemapping[state]
            ch = lookupseq(key)
            mapping.setdefault(ch, ((dj, dmod), (j, mod)))
            revmapping[(dj, dmod), (j, mod)] = ch

    return mapping, revmapping, modmapping

def getlayout():
    keyboard_p = carbon.TISCopyCurrentKeyboardInputSource()
    layout_p = carbon.TISGetInputSourceProperty(keyboard_p,
                                                kTISPropertyUnicodeKeyLayoutData)
    layout_size = carbon.CFDataGetLength(layout_p)
    layout_buf = ctypes.create_string_buffer(b'\000'*layout_size)
    carbon.CFDataGetBytes(layout_p, CFRange(0, layout_size), ctypes.byref(layout_buf))
    ktype = carbon.LMGetKbdType()
    ret = parselayout(layout_buf, ktype)
    carbon.CFRelease(keyboard_p)
    return ret

mapping, revmapping, modmapping = getlayout()

def modstr(mod):
    """ Small helper function to provide a string of the mods set"""
    s = ''
    modifiers = mods(mod)
    for key in modifiers:
        if modifiers[key]:
            s = s+ key + '-'
    return s.rstrip('-')

def mods(mod):
    """ Small helper function to provide a list of Modifier keys from a Mod """
    modifiers = {'Shift':False,'Command':False,'Control':False,'Alternate':False,
                 'Caps':False,'Unknown':False, 'LUnknown':False}

    if mod & 16:
        modifiers['Control'] = True
    if mod & 8:
        # correct
        modifiers['Alternate'] = True
    if mod & 4:
        # ?? maybe not right
        modifiers['Caps'] = True
    if mod & 2:
        # correct
        modifiers['Shift'] = True
    if mod & 1:
        # ?? maybe not right
        modifiers['Command'] = True
    return modifiers


def isprintable(s):
    # Unicode defines all but the following as printable. This is the
    # same rule Python 3.x uses for str.isprintable, and also for which
    # characters need to be hexlified when repr()ed. (Would it be simpler
    # to just repr and strip off the quotes...?)
    for c in s:
        cat = unicodedata.category(c)
        if cat[0] in 'C':
            return False
        elif cat == 'Zs' and c != ' ':
            return False
        elif cat in ('Zl, Zp'):
            return False

def printify(s):
    return s if isprintable(s) else s.encode('unicode_escape').decode('utf-8')

def CharForKeycode(keycode, modifier=0):
    """ Provide a keycode and a modifier and it provides the Character"""
    return printify(revmapping[keycode, modifier])

def KeyCodeForChar(character):
    """ Finds the Keycode and Modifier for the character """
    result = mapping.get(character, (None, 0))
    if result is None or result[0] is None:
        return [(None, 0)]
        #print(u"{}: not found".format(printify(ch)))
    else:
        if not isinstance(result[0], tuple):
            result = result,
        return result

def printcode(keycode):
    """ Prints all the variations of the Keycode with modifiers """
    keys = ('{}:{}'.format(modstr(mod).rstrip('-'),
                           printify(revmapping[keycode, mod]))
            for mod in sorted(modmapping.values()))
    print(u"{:3} {}".format(keycode, ' '.join(keys)))

if __name__ == '__main__':
    import sys
    for arg in sys.argv[1:]:
        try:
            arg = arg.decode(sys.stdin.encoding)
        except AttributeError:
            pass
        try:
            keycode = int(arg)
        except ValueError:
            for ch in arg:
                result = mapping.get(ch, (None, 0))
                if result is None or result[0] is None:
                    print(u"{}: not found".format(printify(ch)))
                else:
                    if not isinstance(result[0], tuple):
                        result = result,
                    print(u"{}: {}".format(printify(ch),
                                           ', '.join('{}{}'.format(modstr(mod), keycode)
                                                     for keycode, mod in result)))
        else:
            printcode(keycode)
    if len(sys.argv) < 2:
        for keycode in range(127):
            printcode(keycode)