
KEYS = (
    '#',
    'S-', 'T-', 'K-', 'P-', 'W-', 'H-', 'R-',
    'A-', 'O-',
    '*',
    '-E', '-U',
    '-F', '-R', '-P', '-B', '-L', '-G', '-T', '-S', '-D', '-Z',
)

IMPLICIT_HYPHEN_KEYS = ('A-', 'O-', '5-', '0-', '-E', '-U', '*')

SUFFIX_KEYS = ('-Z', '-D', '-S', '-G')

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
    # == -ando, -iendo +te, +le, +la, etc.
    # == formando +se = formándose
    (r'^(.+)ando \^ (le|me|te|la|lo|se)$', r'\1ándo\2'),
    (r'^(.+)iendo \^ (le|me|te|la|lo|se)$', r'\1iéndo\2'),
    
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

    # == +en ==
    # write + en = written
    (r'^(.+)te \^ en$', r'\1tten'),
    # Minessota +en = Minessotan (*Minessotaen)
    (r'^(.+[ae]) \^ e(n|ns)$', r'\1\2'),

    # == +ial ==
    # ceremony +ial = ceremonial (*ceremonyial)
    (r'^(.+)y \^ (ial|ially)$', r'\1\2'),
    # edit +torial = editorial (*edittorial)
    (r'^(.+)tor \^ (ial|ials|ially|iality|ialities)$', r'\1tor\2'),

    # == +if ==
    # spaghetti +ify = spaghettification (*spaghettiification)
    (r'^(.+)i \^ if(y|ying|ied|ies|ication|ications)$', r'\1if\2'),

    # == +ist ==
    # radical +ist = radicalist (*radicallist)
    (r'^(.*[l]) \^ is(t|ts)$', r'\1is\2'),

    # == +ity ==
    # complementary +ity = complementarity (*complementaryity)
    (r'^(.*)ry \^ ity$', r'\1rity'),
    # disproportional +ity = disproportionality (*disproportionallity)
    (r'^(.*)l \^ ity$', r'\1rity'),
    
    # == +ive, +tive ==
    # perform +tive = performative (*performtive)
    (r'^(.+)rm \^ tiv(e|ity|ities)$', r'\1rmativ\2'),
    # restore +tive = restorative
    (r'^(.+)e \^ tiv(e|ity|ities)$', r'\1ativ\2'),
    
    # == +ize ==
    # token +ize = tokenize (*tokennize)
    # token +ise = tokenise (*tokennise)
    (r'^(.+)y \^ iz(e|es|ing|ed|er|ers|ation|ations|able|ability)$', r'\1iz\2'),
    (r'^(.+)y \^ is(e|es|ing|ed|er|ers|ation|ations|able|ability)$', r'\1is\2'),
    # conditional +ize = conditionalize (*conditionallize)
    (r'^(.+)al \^ iz(e|ed|es|ing|er|ers|ation|ations|m|ms|able|ability|abilities)$', r'\1aliz\2'),
    (r'^(.+)al \^ is(e|ed|es|ing|er|ers|ation|ations|m|ms|able|ability|abilities)$', r'\1alis\2'),
    # spectacular +ization = spectacularization (*spectacularrization)
    (r'^(.+)ar \^ iz(e|ed|es|ing|er|ers|ation|ations|m|ms)$', r'\1ariz\2'),
    (r'^(.+)ar \^ is(e|ed|es|ing|er|ers|ation|ations|m|ms)$', r'\1aris\2'),

    # category +ize/+ise = categorize/categorise (*categoryize/*categoryise)
    # custom +izable/+isable = customizable/customisable (*custommizable/*custommisable)
    # fantasy +ize
    (r'^(.*[lmnty]) \^ iz(e|es|ing|ed|er|ers|ation|ations|m|ms|able|ability|abilities)$', r'\1iz\2'),
    (r'^(.*[lmnty]) \^ is(e|es|ing|ed|er|ers|ation|ations|m|ms|able|ability|abilities)$', r'\1is\2'),
    
    # == +olog ==
    # criminal + ology = criminology
    # criminol + ologist = criminalologist (*criminallologist)
    (r'^(.+)al \^ olog(y|ist|ists|ical|ically)$', r'\1olog\2'),
    # dermatology +ist, +ists = dermatologist, dermatologists
    (r'^(.+)ology \^ (ist|ists)$', r'\1olog\2'),

    # == +ish ==
    # similar +ish = similarish (*similarrish)
    (r'^(.+)(ar|er|or) \^ ish$', r'\1\2ish'),

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
    'ably': 'ibly',
    'ability': 'ibility',
}

ORTHOGRAPHY_WORDLIST = 'american_english_words.txt'

KEYMAPS = {
    'Gemini PR': {
        '#': ('#1', '#2', '#3', '#4', '#5', '#6', '#7', '#8', '#9', '#A', '#B', '#C'),
        'S-': ('S1-', 'S2-'),
        'T-': 'T-',
        'K-': 'K-',
        'P-': 'P-',
        'W-': 'W-',
        'H-': 'H-',
        'R-': 'R-',
        'A-': 'A-',
        'O-': 'O-',
        '*': ('*1', '*2', '*3', '*4'),
        '-E': '-E',
        '-U': '-U',
        '-F': '-F',
        '-R': '-R',
        '-P': '-P',
        '-B': '-B',
        '-L': '-L',
        '-G': '-G',
        '-T': '-T',
        '-S': '-S',
        '-D': '-D',
        '-Z': '-Z',
        'no-op': ('Fn', 'pwr', 'res1', 'res2'),
    },
    'Keyboard': {
        '#': ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='),
        'S-': ('a', 'q'),
        'T-': 'w',
        'K-': 's',
        'P-': 'e',
        'W-': 'd',
        'H-': 'r',
        'R-': 'f',
        'A-': 'c',
        'O-': 'v',
        '*': ('t', 'g', 'y', 'h'),
        '-E': 'n',
        '-U': 'm',
        '-F': 'u',
        '-R': 'j',
        '-P': 'i',
        '-B': 'k',
        '-L': 'o',
        '-G': 'l',
        '-T': 'p',
        '-S': ';',
        '-D': '[',
        '-Z': '\'',
        'arpeggiate': 'space',
        # Suppress adjacent keys to prevent miss-strokes.
        'no-op': ('z', 'x', 'b', ',', '.', '/', ']', '\\'),
    },
    'Passport': {
        '#': '#',
        'S-': ('S', 'C'),
        'T-': 'T',
        'K-': 'K',
        'P-': 'P',
        'W-': 'W',
        'H-': 'H',
        'R-': 'R',
        'A-': 'A',
        'O-': 'O',
        '*': ('~', '*'),
        '-E': 'E',
        '-U': 'U',
        '-F': 'F',
        '-R': 'Q',
        '-P': 'N',
        '-B': 'B',
        '-L': 'L',
        '-G': 'G',
        '-T': 'Y',
        '-S': 'X',
        '-D': 'D',
        '-Z': 'Z',
        'no-op': ('!', '^', '+'),
    },
    'Stentura': {
        '#': '#',
        'S-': 'S-',
        'T-': 'T-',
        'K-': 'K-',
        'P-': 'P-',
        'W-': 'W-',
        'H-': 'H-',
        'R-': 'R-',
        'A-': 'A-',
        'O-': 'O-',
        '*': '*',
        '-E': '-E',
        '-U': '-U',
        '-F': '-F',
        '-R': '-R',
        '-P': '-P',
        '-B': '-B',
        '-L': '-L',
        '-G': '-G',
        '-T': '-T',
        '-S': '-S',
        '-D': '-D',
        '-Z': '-Z',
        'no-op': '^',
    },
    'TX Bolt': {
        '#': '#',
        'S-': 'S-',
        'T-': 'T-',
        'K-': 'K-',
        'P-': 'P-',
        'W-': 'W-',
        'H-': 'H-',
        'R-': 'R-',
        'A-': 'A-',
        'O-': 'O-',
        '*': '*',
        '-E': '-E',
        '-U': '-U',
        '-F': '-F',
        '-R': '-R',
        '-P': '-P',
        '-B': '-B',
        '-L': '-L',
        '-G': '-G',
        '-T': '-T',
        '-S': '-S',
        '-D': '-D',
        '-Z': '-Z',
    },
    'Treal': {
        '#': ('#1', '#2', '#3', '#4', '#5', '#6', '#7', '#8', '#9', '#A', '#B'),
        'S-': ('S1-', 'S2-'),
        'T-': 'T-',
        'K-': 'K-',
        'P-': 'P-',
        'W-': 'W-',
        'H-': 'H-',
        'R-': 'R-',
        'A-': 'A-',
        'O-': 'O-',
        '*': ('*1', '*2'),
        '-E': '-E',
        '-U': '-U',
        '-F': '-F',
        '-R': '-R',
        '-P': '-P',
        '-B': '-B',
        '-L': '-L',
        '-G': '-G',
        '-T': '-T',
        '-S': '-S',
        '-D': '-D',
        '-Z': '-Z',
        'no-op': ('X1-', 'X2-', 'X3'),
    },
}

DICTIONARIES_ROOT = 'asset:plover:assets'
DEFAULT_DICTIONARIES = ('user.json', 'commands.json', 'main.json')
