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
    suffix, sep, rest = suffix.partition(' ')
    for r in RULES:
        m = r[0].match(word + " ^ " + suffix)
        if m:   
            expanded = m.expand(r[1])
            return expanded + sep + rest
    return word + suffix + sep + rest

def _tests():
    # c+ly->cally
    assert add_suffix('artistic', 'ly') == 'artistically'
    
    # sibilant+s->es
    assert add_suffix('establish', 's') == 'establishes'
    assert add_suffix('speech', 's') == 'speeches'
    assert add_suffix('approach', 's') == 'approaches'
    assert add_suffix('beach', 's') == 'beaches'
    assert add_suffix('arch', 's') == 'arches'
    assert add_suffix('larch', 's') == 'larches'
    assert add_suffix('march', 's') == 'marches'
    assert add_suffix('search', 's') == 'searches'
    assert add_suffix('starch', 's') == 'starches'
    # hard ch+s->s
    assert add_suffix('stomach', 's') == 'stomachs'
    assert add_suffix('monarch', 's') == 'monarchs'
    assert add_suffix('patriarch', 's') == 'patriarchs'
    assert add_suffix('oligarch', 's') == 'oligarchs'
   
    # y+s->ies
    assert add_suffix('cherry', 's') == 'cherries'
    assert add_suffix('day', 's') == 'days'
   
    # y+ist->ist
    assert add_suffix('pharmacy', 'ist') == 'pharmacist'
    assert add_suffix('melody', 'ist') == 'melodist'
    assert add_suffix('pacify', 'ist') == 'pacifist'
    assert add_suffix('geology', 'ist') == 'geologist'
    assert add_suffix('metallurgy', 'ist') == 'metallurgist'
    assert add_suffix('anarchy', 'ist') == 'anarchist'
    assert add_suffix('monopoly', 'ist') == 'monopolist'
    assert add_suffix('alchemy', 'ist') == 'alchemist'
    assert add_suffix('botany', 'ist') == 'botanist'
    assert add_suffix('therapy', 'ist') == 'therapist'
    assert add_suffix('theory', 'ist') == 'theorist'
    assert add_suffix('psychiatry', 'ist') == 'psychiatrist'
    # y+ist->i exceptions
    assert add_suffix('lobby', 'ist') == 'lobbyist'
    assert add_suffix('hobby', 'ist') == 'hobbyist'
    assert add_suffix('copy', 'ist') != 'copyist'  # TODO
    
    # y+!i->i
    assert add_suffix('beauty', 'ful') == 'beautiful'
    assert add_suffix('weary', 'ness') == 'weariness'
    assert add_suffix('weary', 'some') == 'wearisome'
    
    # e+vowel->vowel
    assert add_suffix('narrate', 'ing') == 'narrating'
    assert add_suffix('narrate', 'or') == 'narrator'
    
    # consonant doubling
    assert add_suffix('defer', 'ed') == 'deferred'
    assert add_suffix('defer', 'er') == 'deferrer'
    assert add_suffix('defer', 'ing') == 'deferring'
    assert add_suffix('pigment', 'ed') == 'pigmented'
    assert add_suffix('refer', 'ed') == 'referred'
    assert add_suffix('fix', 'ed') == 'fixed'
    assert add_suffix('alter', 'ed') != 'altered'  # TODO
    assert add_suffix('interpret', 'ing') != 'interpreting'  # TODO
    assert add_suffix('wonder', 'ing') != 'wondering'  # TODO
    assert add_suffix('target', 'ing') != 'targeting'  # TODO
    assert add_suffix('limit', 'er') != 'limiter'  # TODO
    assert add_suffix('maneuver', 'ing') != 'maneuvering'  # TODO
    assert add_suffix('monitor', 'ing') != 'monitoring'  # TODO
    assert add_suffix('color', 'ing') != 'coloring'  # TODO
    assert add_suffix('inhibit', 'ing') != 'inhibiting'  # TODO
    assert add_suffix('master', 'ed') != 'mastered'  # TODO

if __name__ == '__main__':
    _tests()
