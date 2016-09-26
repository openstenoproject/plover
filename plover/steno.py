# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: unit test this file

"""Generic stenography data models.

This module contains the following class:

Stroke -- A data model class that encapsulates a sequence of steno keys.

"""

import re

from plover import system


STROKE_DELIMITER = '/'

_NUMBERS = set('0123456789')
_IMPLICIT_NUMBER_RX = re.compile('(^|[1-4])([6-9])')

normalized_steno_indexes = {}
normalized_stroke_indexes = {}

def normalized_steno_to_indexes(steno):
    return (
        normalized_steno_indexes[steno]
        if steno in normalized_steno_indexes
        else normalized_steno_indexes.setdefault(
            steno,
            tuple(normalized_stroke_to_indexes(stroke) for stroke in steno)
        )
    )

def normalized_stroke_to_indexes(stroke):
    if stroke not in normalized_stroke_indexes:
        side = -1
        indexes = []
        for key in stroke:
            if side == 1:  # Right side, easiest case.
                key_index = system.KEY_ORDER.get('-%s' % key)
            elif key == '-':  # Center delimiter
                side = 1
                continue
            elif key == system.NUMBER_KEY:
                key_index = system.KEY_ORDER.get(key)
            elif key in system.IMPLICIT_HYPHENS:  # Detect center keys
                key_index = (
                    system.KEY_ORDER.get(key) or
                    system.KEY_ORDER.get('%s-' % key) or
                    system.KEY_ORDER.get('-%s' % key)
                )
                assert key_index is not None, 'Invalid implicit key found: %s' % key
                side = 0
            elif side == 0:
                # Case where we last found a center key, but now can't.
                # It implies our first right side key.
                key_index = system.KEY_ORDER.get('-%s' % key)
                side = 1
            else: # Must be a left-side key.
                key_index = system.KEY_ORDER.get('%s-' % key)
            if key_index is not None:
                indexes.append(key_index)
    return (
        normalized_stroke_indexes[stroke]
        if stroke in normalized_stroke_indexes
        else normalized_stroke_indexes.setdefault(
            stroke,
            tuple(indexes)
        )
    )

def normalize_stroke(stroke):
    letters = set(stroke)
    if letters & _NUMBERS:
        if system.NUMBER_KEY in letters:
            stroke = stroke.replace(system.NUMBER_KEY, '')
        # Insert dash when dealing with 'explicit' numbers
        m = _IMPLICIT_NUMBER_RX.search(stroke)
        if m is not None:
            start = m.start(2)
            return stroke[:start] + '-' + stroke[start:]
    if '-' in letters:
        if stroke.endswith('-'):
            stroke = stroke[:-1]
        elif letters & system.IMPLICIT_HYPHENS:
            stroke = stroke.replace('-', '')
    return stroke

def normalize_steno(strokes_string):
    """Convert steno strings to one common form."""
    return tuple(normalize_stroke(stroke) for stroke
                 in strokes_string.split(STROKE_DELIMITER))

def sort_steno_keys(steno_keys):
    return sorted(steno_keys, key=lambda x: system.KEY_ORDER.get(x, -1))


def filter_entry(strokes, translation, strokes_filter=None,
                 translation_filter=None, case_sensitive=False, regex=None):
    joined_strokes = '/'.join(strokes)
    # Two cases:
    #   Looking for 'STPH' and get 'STPH/BA'
    #   Looking for 'BA' and get 'STPH/BA'
    if strokes_filter is not None and \
       not joined_strokes.startswith(strokes_filter) and \
            not '/' + strokes_filter in joined_strokes:
        return False
    if regex is not None:
        if not regex.search(translation):
            return False
    elif translation_filter is not None:
        translation_filter = translation_filter if case_sensitive\
            else translation_filter.lower()
        translation_text = translation if case_sensitive\
            else translation.lower()
        if translation_filter not in translation_text:
            return False
    return True


class Stroke(object):
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
        # Order the steno keys so comparisons can be made.
        steno_keys = list(sort_steno_keys(steno_keys_set))

        # Convert strokes involving the number bar to numbers.
        if system.NUMBER_KEY in steno_keys:
            numeral = False
            for i, e in enumerate(steno_keys):
                if e in system.NUMBERS:
                    steno_keys[i] = system.NUMBERS[e]
                    numeral = True
            if numeral:
                steno_keys.remove(system.NUMBER_KEY)

        if steno_keys_set & system.IMPLICIT_HYPHEN_KEYS:
            self.rtfcre = ''.join(key.strip('-') for key in steno_keys)
        else:
            pre = ''.join(k.strip('-') for k in steno_keys if k[-1] == '-' or
                          k == system.NUMBER_KEY)
            post = ''.join(k.strip('-') for k in steno_keys if k[0] == '-')
            self.rtfcre = '-'.join([pre, post]) if post else pre

        self.steno_keys = steno_keys

        # Determine if this stroke is a correction stroke.
        self.is_correction = (self.rtfcre == system.UNDO_STROKE_STENO)

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

