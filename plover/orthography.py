# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Functions that implement some English orthographic rules."""

CONSONANTS = 'bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ'
VOWELS = 'aeiouAEIOU'
W = 'wW'
Y = 'yY'
PLURAL_SPECIAL = 'sxzSXZ'

def pluralize_with_s(word):
    """Form the plural of a word by adding an s.

    Argument:

    word -- A singular noun or noun phrase.

    """
    if len(word) < 2:
        return word + 's'
    a = word[-2]
    b = word[-1]
    if b in PLURAL_SPECIAL:
        return word + 'es'
    elif b in Y and a in CONSONANTS:
        return word[:-1] + 'ies'
    return word + 's'

def add_ed_suffix(word):
    """Form the past tense of a verb by adding 'ed'.

    Argument:

    word -- The infinitive form of a verb.

    """
    return _prep_for_simple_suffix(word) + 'ed'

def add_er_suffix(word):
    """Add an -er suffix to the end of a word.

    Argument:

    word -- An adjective or verb.

    """
    return _prep_for_simple_suffix(word) + 'er'

def add_ing_suffix(word):
    """Add an -ing suffix to the end of a word.

    Argument:

    word -- The infinitive form of a verb.

    """
    if word and word[-1] in Y: # See _prep_for_simple_suffix special case.
        return word + 'ing'
    return _prep_for_simple_suffix(word) + 'ing'

def _prep_for_simple_suffix(word):
    num_chars = len(word)
    if num_chars < 2:
        return word
    if num_chars >= 3:
        third_to_last = word[-3]
    else:
        third_to_last = ''
    second_to_last = word[-2]
    last = word[-1]
    if second_to_last in VOWELS or second_to_last in CONSONANTS:
        if last in VOWELS:
            if third_to_last and (third_to_last in VOWELS or
                                  third_to_last in CONSONANTS):
                return word[:-1]
        elif (last in CONSONANTS and
              last not in W and
              second_to_last in VOWELS and
              third_to_last and
              third_to_last not in VOWELS):
            return word + last
        elif last in Y and second_to_last in CONSONANTS:
            return word[:-1] + 'i' # Special case doesn't work for 'ing' suffix.
    return word
