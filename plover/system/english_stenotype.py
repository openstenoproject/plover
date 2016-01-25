
KEYS = (
    '#',
    'S-', 'T-', 'K-', 'P-', 'W-', 'H-', 'R-',
    'A-', 'O-',
    '*',
    '-E', '-U',
    '-F', '-R', '-P', '-B', '-L', '-G', '-T', '-S', '-D', '-Z',
)

IMPLICIT_HYPHEN_KEYS = ('A-', 'O-', '5-', '0-', '-E', '-U', '*')

SUFFIX_KEYS = ('-S', '-G', '-Z', '-D')

NUMBER_KEY = '#'

NUMBERS = {
    'S-': '1-',
    'T-': '2-',
    'P-': '3-',
    'H-': '4-',
    'A-': '5-',
    'O-': '0-',
    '-F': '-6',
    '-P': '-7',
    '-L': '-8',
    '-T': '-9',
}

UNDO_STROKE_STENO = '*'

ORTHOGRAPHY_RULES = [
    # == +ly ==
    # artistic + ly = artistically
    (r'^(.*[aeiou]c) \^ ly$', r'\1ally'),
        
    # == +ry ==      
    # statute + ry = statutory
    (r'^(.*t)e \^ ry$', r'\1ory'),
        
    # == t +cy ==      
    # frequent + cy = frequency (tcy/tecy removal)
    (r'^(.*[naeiou])te? \^ cy$', r'\1cy'),

    # == +s ==
    # establish + s = establishes (sibilant pluralization)
    (r'^(.*(?:s|sh|x|z|zh)) \^ s$', r'\1es'),
    # speech + s = speeches (soft ch pluralization)
    (r'^(.*(?:oa|ea|i|ee|oo|au|ou|l|n|(?<![gin]a)r|t)ch) \^ s$', r'\1es'),
    # cherry + s = cherries (consonant + y pluralization)
    (r'^(.+[bcdfghjklmnpqrstvwxz])y \^ s$', r'\1ies'),

    # == y ==
    # die+ing = dying
    (r'^(.+)ie \^ ing$', r'\1ying'),
    # metallurgy + ist = metallurgist
    (r'^(.+[cdfghlmnpr])y \^ ist$', r'\1ist'),
    # beauty + ful = beautiful (y -> i)
    (r'^(.+[bcdfghjklmnpqrstvwxz])y \^ ([a-hj-xz].*)$', r'\1i\2'),

    # == e ==
    # write + en = written
    (r'^(.+)te \^ en$', r'\1tten'),
    # free + ed = freed 
    (r'^(.+e)e \^ (e.+)$', r'\1\2'),
    # narrate + ing = narrating (silent e)
    (r'^(.+[bcdfghjklmnpqrstuvwxz])e \^ ([aeiouy].*)$', r'\1\2'),

    # == misc ==
    # defer + ed = deferred (consonant doubling)   XXX monitor(stress not on last syllable)
    (r'^(.*(?:[bcdfghjklmnprstvwxyz]|qu)[aeiou])([bcdfgklmnprtvz]) \^ ([aeiouy].*)$', r'\1\2\2\3'),
]

ORTHOGRAPHY_RULES_ALIASES = {
    'able': 'ible',
}

ORTHOGRAPHY_WORDLIST = 'american_english_words.txt'

KEYBOARD_KEYMAP = (
    ('S-'        , ('a', 'q')),
    ('T-'        , 'w'),
    ('K-'        , 's'),
    ('P-'        , 'e'),
    ('W-'        , 'd'),
    ('H-'        , 'r'),
    ('R-'        , 'f'),
    ('A-'        , 'c'),
    ('O-'        , 'v'),
    ('*'         , ('t', 'g', 'y', 'h')),
    ('-E'        , 'n'),
    ('-U'        , 'm'),
    ('-F'        , 'u'),
    ('-R'        , 'j'),
    ('-P'        , 'i'),
    ('-B'        , 'k'),
    ('-L'        , 'o'),
    ('-G'        , 'l'),
    ('-T'        , 'p'),
    ('-S'        , ';'),
    ('-D'        , '['),
    ('-Z'        , '\''),
    ('#'         , ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=')),
    ('no-op'     , ('z', 'x', 'b', ',', '.', '/', '\\')),
    ('arpeggiate', 'space'),
)

