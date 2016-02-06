# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Functions that implement some English orthographic rules."""

from io import open
import os.path
import re
from plover.config import ASSETS_DIR

word_list_file_name = os.path.join(ASSETS_DIR, 'american_english_words.txt')
WORDS = dict()
try:
    with open(word_list_file_name, encoding='utf-8') as f:
        pairs = [word.strip().rsplit(' ', 1) for word in f]
        pairs.sort(reverse=True, key=lambda x: int(x[1]))
        WORDS = {p[0].lower(): int(p[1]) for p in pairs}
except IOError as e:
    print e

RULES = [
    # == +ly ==
    # artistic + ly = artistically
    (re.compile(r'^(.*[aeiou]c) \^ ly$', re.I),
        r'\1ally'),
        
    # == +ry ==      
    # statute + ry = statutory
    (re.compile(r'^(.*t)e \^ ry$', re.I),
        r'\1ory'),
        
    # == t +cy ==      
    # frequent + cy = frequency (tcy/tecy removal)
    (re.compile(r'^(.*[naeiou])te? \^ cy$', re.I),
        r'\1cy'),

    # == +s ==
    # establish + s = establishes (sibilant pluralization)
    (re.compile(r'^(.*(?:s|sh|x|z|zh)) \^ s$', re.I),
        r'\1es'),
    # speech + s = speeches (soft ch pluralization)
    (re.compile(r'^(.*(?:oa|ea|i|ee|oo|au|ou|l|n|(?<![gin]a)r|t)ch) \^ s$', re.I),
        r'\1es'),
    # cherry + s = cherries (consonant + y pluralization)
    (re.compile(r'^(.+[bcdfghjklmnpqrstvwxz])y \^ s$', re.I),
        r'\1ies'),

    # == y ==
    # die+ing = dying
    (re.compile(r'^(.+)ie \^ ing$', re.I),
        r'\1ying'),
    # metallurgy + ist = metallurgist
    (re.compile(r'^(.+[cdfghlmnpr])y \^ ist$', re.I),
        r'\1ist'),
    # beauty + ful = beautiful (y -> i)
    (re.compile(r'^(.+[bcdfghjklmnpqrstvwxz])y \^ ([a-hj-xz].*)$', re.I),
        r'\1i\2'),

    # == e ==
    # write + en = written
    (re.compile(r'^(.+)te \^ en$', re.I),
        r'\1tten'),
    # free + ed = freed 
    (re.compile(r'^(.+e)e \^ (e.+)$', re.I),
        r'\1\2'),
    # narrate + ing = narrating (silent e)
    (re.compile(r'^(.+[bcdfghjklmnpqrstuvwxz])e \^ ([aeiouy].*)$', re.I),
        r'\1\2'),

    # == misc ==
    # defer + ed = deferred (consonant doubling)   XXX monitor(stress not on last syllable)
    (re.compile(r'^(.*(?:[bcdfghjklmnprstvwxyz]|qu)[aeiou])([bcdfgklmnprtvz]) \^ ([aeiouy].*)$', re.I),
        r'\1\2\2\3'),
]


def make_candidates_from_rules(word, suffix, check=lambda x: True):
    candidates = []
    for r in RULES:
        m = r[0].match(word + " ^ " + suffix)
        if m:   
            expanded = m.expand(r[1])
            if check(expanded):
                candidates.append(expanded)
    return candidates

def _add_suffix(word, suffix):
    in_dict_f = lambda x: x in WORDS

    candidates = []
    
    # Try 'ible' and see if it's in the dictionary.
    if suffix == 'able':
        candidates.extend(make_candidates_from_rules(word, 'ible', in_dict_f))
    
    # Try a simple join if it is in the dictionary.
    simple = word + suffix
    if in_dict_f(simple):
        candidates.append(simple)
    
    # Try rules with dict lookup.
    candidates.extend(make_candidates_from_rules(word, suffix, in_dict_f))

    # For all candidates sort by prominence in dictionary and, since sort is
    # stable, also by the order added to candidates list.
    if candidates:
        candidates.sort(key=lambda x: WORDS[x])
        return candidates[0]
    
    # Try rules without dict lookup.
    candidates = make_candidates_from_rules(word, suffix)
    if candidates:
        return candidates[0]
    
    # If all else fails then just do a simple join.
    return simple

def add_suffix(word, suffix):
    """Add a suffix to a word by applying the rules above
    
    Arguments:
        
    word -- A word
    suffix -- The suffix to add
    
    """
    suffix, sep, rest = suffix.partition(' ')
    expanded = _add_suffix(word, suffix)
    return expanded + sep + rest
