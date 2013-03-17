# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Functions that implement some English orthographic rules."""

import re

RULES = [
    # == +ly ==
    # artistic + ly = artistically
    (re.compile(r'^(.*[aeiou]c) \^ ly$', re.I),
        r'\1ally'),

    # == +s ==
    # establish + s = establishes (sibilant pluralization)
    (re.compile(r'^(.*[aeiou](?:s|x|z|ms|rs|sh|ss|tz|zz|lys|rsh|tch)|.*y(?:x|ss)) \^ s$', re.I),
        r'\1es'),
    # speech + s = speeches (soft ch pluralization)
    (re.compile(r'^(.*(?:a|ee|i|oo|au|ou|r)ch) \^ s$', re.I),
        r'\1es'),
    # cherry + s = cherries (consonant + y pluralization)
    (re.compile(r'^(.+[bcdfghjklmnpqrstvwxz])y \^ s$', re.I),
        r'\1ies'),

    # == y ==
    # die+ing = dying
    (re.compile(r'^(.+)ie \^ ing$', re.I),
        r'\1ying'),
    # metallurgy + ist = metallurgist
    (re.compile(r'^(.+[bcdfghjklmnpqrstvwxz])y \^ i(.*)$', re.I),
        r'\1i\2'),
    # beauty + ful = beautiful (y -> i)
    (re.compile(r'^(.+[bcdfghjklmnpqrstvwxz])y \^ ([bcdfghjklmnpqrtvwxz].*)$', re.I),
        r'\1i\2'),

    # == e ==
    # narrate + ing = narrating (silent e)
    (re.compile(r'^(.+[bcdfghjklmnpqrstvwxz])e \^ ([aeiouy].*)$', re.I),
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
