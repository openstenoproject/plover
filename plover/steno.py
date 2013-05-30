# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Generic stenography data models.

This module contains the following class:

Stroke -- A data model class that encapsulates a sequence of steno keys.

"""

import re

STROKE_DELIMITER = '/'

HYPHEN_CHARS = set(('-', 'A', 'E', 'O', 'U', '*'))

def normalize_steno(strokes_string):
    """Convert steno strings to one common form.

    Plover currently supports two encodings for steno strokes in its dictionary:
    dcat and eclipse. This function converts both to one common form.

    """
    strokes = strokes_string.split(STROKE_DELIMITER)
    normalized_strokes = []
    for stroke in strokes:
        if '#' in stroke and re.search('[0-9]', stroke):
            stroke = stroke.replace('#', '')
    
        seen_dash = False
        normalized_stroke = []
        for c in stroke:
            if c == '-':
                if seen_dash:
                    continue
            if c in HYPHEN_CHARS:
                seen_dash = True
            normalized_stroke.append(c)
        normalized_strokes.append(''.join(normalized_stroke))
    return tuple(normalized_strokes)

STENO_KEY_NUMBERS = {'S-': '1-',
                     'T-': '2-',
                     'P-': '3-',
                     'H-': '4-',
                     'A-': '5-',
                     'O-': '0-',
                     '-F': '-6',
                     '-P': '-7',
                     '-L': '-8',
                     '-T': '-9'}

STENO_KEY_ORDER = {"#": -1,
                   "S-": 0,
                   "T-": 1,
                   "K-": 2,
                   "P-": 3,
                   "W-": 4,
                   "H-": 5,
                   "R-": 6,
                   "A-": 7,
                   "O-": 8,
                   "*": 9,  # Also 10, 11, and 12 for some machines.
                   "-E": 13,
                   "-U": 14,
                   "-F": 15,
                   "-R": 16,
                   "-P": 17,
                   "-B": 18,
                   "-L": 19,
                   "-G": 20,
                   "-T": 21,
                   "-S": 22,
                   "-D": 23,
                   "-Z": 24,

                   "{calc}": 25, # Calculator button (sidewinder-specific)
}

IMPLICIT_HYPHEN = set(('A-', 'O-', '5-', '0-', '-E', '-U', '*'))

class Stroke:
    """A standardized data model for stenotype machine strokes.

    This class standardizes the representation of a stenotype chord. A stenotype
    chord can be any sequence of stenotype keys that can be simultaneously
    pressed. Nearly all stenotype machines offer the same set of keys that can
    be combined into a chord, though some variation exists due to duplicate
    keys. This class accounts for such duplication, imposes the standard
    stenographic ordering on the keys, and combines the keys into a single
    string (called RTFCRE for historical reasons).

    """

    def __init__(self, steno_keys) :
        """Create a steno stroke by formatting steno keys.

        Arguments:

        steno_keys -- A sequence of pressed keys.

        """
        # Remove duplicate keys and save local versions of the input 
        # parameters.
        steno_keys_set = set(steno_keys)
        steno_keys = list(steno_keys_set)

        # Order the steno keys so comparisons can be made.
        steno_keys.sort(key=lambda x: STENO_KEY_ORDER[x])
         
        # Convert strokes involving the number bar to numbers.
        if '#' in steno_keys:
            numeral = False
            for i, e in enumerate(steno_keys):
                if e in STENO_KEY_NUMBERS:
                    steno_keys[i] = STENO_KEY_NUMBERS[e]
                    numeral = True
            if numeral:
                steno_keys.remove('#')
        
        if steno_keys_set & IMPLICIT_HYPHEN:
            self.rtfcre = ''.join(key.strip('-') for key in steno_keys)
        else:
            pre = ''.join(k.strip('-') for k in steno_keys if k[-1] == '-' or
                          k == '#' or "{" in k) # special keys
            post = ''.join(k.strip('-') for k in steno_keys if k[0] == '-')
            self.rtfcre = '-'.join([pre, post]) if post else pre

        self.steno_keys = steno_keys

        # Determine if this stroke is a correction stroke.
        self.is_correction = (self.rtfcre == '*')

    def __str__(self):
        if self.is_correction:
            prefix = '*'
        else:
            prefix = ''
        return '%sStroke(%s : %s)' % (prefix, self.rtfcre, self.steno_keys)

    def __eq__(self, other):
        return (isinstance(other, Stroke)
                and self.steno_keys == other.steno_keys)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return str(self)

