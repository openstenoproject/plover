# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Functions that implement some English orthographic rules."""

import re

RULES = [
    # == +ly ==
    # artistic + ly = artistically
    (re.compile(r'^(.*[aeiou]c) \^ ly(\W.*)?$', re.I),
        r'\1ally\2'),

    # == +s ==
    # establish + s = establishes (sibilant pluralization)
    (re.compile(r'^(.*(?:s|sh|x|z|zh)) \^ s(\W.*)?$', re.I),
        r'\1es\2'),
    # speech + s = speeches (soft ch pluralization)
    (re.compile(r'^(.*(?:a|i|ee|oo|au|ou|n|r|t)ch) \^ s(\W.*)?$', re.I),
        r'\1es\2'),
    # cherry + s = cherries (consonant + y pluralization)
    (re.compile(r'^(.+[bcdfghjklmnpqrstvwxz])y \^ s(\W.*)?$', re.I),
        r'\1ies\2'),

    # == y ==
    # die+ing = dying
    (re.compile(r'^(.+)ie \^ ing(\W.*)?$', re.I),
        r'\1ying\2'),
    # metallurgy + ist = metallurgist
    (re.compile(r'^(.+[bcdfghjklmnpqrstvwxz])y \^ i(.*)$', re.I),
        r'\1i\2'),
    # beauty + ful = beautiful (y -> i)
    (re.compile(r'^(.+[bcdfghjklmnpqrstvwxz])y \^ ([bcdfghjklmnpqrtvwxz].*)$', re.I),
        r'\1i\2'),

    # == e ==
    # narrate + ing = narrating (silent e)
    (re.compile(r'^(.+[bcdfghjklmnpqrstuvwxz])e \^ ([aeiouy].*)$', re.I),
        r'\1\2'),
    
    # == misc ==
    # defer + ed = deferred (consonant doubling)   XXX monitor(stress not on last syllable)
    (re.compile(r'^(.*[bcdfghjklmnpqrstvwxyz][aeiou])([bcdfgklmnprtvz]) \^ ([aeiouy].*)$', re.I),
        r'\1\2\2\3'),
]

def add_suffix(word, suffix):
    """Add a suffix to a word by applying the rules above
    
    Arguments:
        
    word -- A word
    suffix -- The suffix to add
    
    """
    for r in RULES:
        m = r[0].match(word + " ^ " + suffix)
        if m:   
            expanded = m.expand(r[1])
            return expanded
    return word + suffix
