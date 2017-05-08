
import ast
import functools
import unittest

from plover import system
from plover.steno import Stroke
from plover.formatting import Formatter
from plover.translation import Translator
from plover.steno import normalize_steno
from plover.steno_dictionary import StenoDictionary


class CaptureOutput(object):

    def __init__(self):
        self.instructions = []
        self.text = u''

    def send_backspaces(self, n):
        assert n <= len(self.text)
        self.text = self.text[:-n]
        self.instructions.append(('b', n))

    def send_string(self, s):
        self.text += s
        self.instructions.append(('s', s))

    def send_key_combination(self, c):
        self.instructions.append(('c', c))

    def send_engine_command(self, c):
        self.instructions.append(('e', c))


def steno_to_stroke(steno):
    if steno_to_stroke.system != system.NAME:
        keys = []
        letters = ''
        has_hyphen = False
        for k in system.KEYS:
            if not has_hyphen and k.startswith('-'):
                has_hyphen = True
                keys.append(None)
                letters += '-'
            keys.append(k)
            letters += k.strip('-')
        steno_to_stroke.keys = keys
        steno_to_stroke.letters = letters
        steno_to_stroke.system = system.NAME
        steno_to_stroke.numbers = {
            v.strip('-'): k.strip('-')
            for k, v in system.NUMBERS.items()
        }
    n = -1
    keys = set()
    for l in steno:
        rl = steno_to_stroke.numbers.get(l)
        if rl is not None:
            keys.add('#')
            l = rl
        n = steno_to_stroke.letters.find(l, n + 1)
        assert n >= 0, (steno_to_stroke.letters, l, n)
        k = steno_to_stroke.keys[n]
        if k is not None:
            keys.add(k)
    return Stroke(keys)

steno_to_stroke.system = None


def simple_replay(f):
    @functools.wraps(f)
    def wrapper(self):
        f(self)
        definitions, strokes, output = f.__doc__.strip().split('\n\n')
        for steno, translation in ast.literal_eval(
            '{' + definitions + '}'
        ).items():
            self.dictionary.set(normalize_steno(steno), translation)
        for s in normalize_steno(strokes.strip()):
            self.translator.translate(steno_to_stroke(s))
        self.assertEqual(self.output.text, ast.literal_eval(output.strip()), msg=f.__doc__)
    return wrapper

def spaces_after(f):
    @functools.wraps(f)
    def wrapper(self):
        self.formatter.set_space_placement('After Output')
        f(self)
    return wrapper


class BlackboxTest(unittest.TestCase):

    def setUp(self):
        self.output = CaptureOutput()
        self.formatter = Formatter()
        self.formatter.set_output(self.output)
        self.translator = Translator()
        self.translator.set_min_undo_length(100)
        self.translator.add_listener(self.formatter.format)
        self.dictionary = self.translator.get_dictionary()
        self.dictionary.set_dicts([StenoDictionary()])

    @simple_replay
    def test_translator_state_handling(self):
        # Check if the translator curtailing the list of last translations
        # according to its dictionary longest key does no affect things
        # like the restrospective repeate-last-stroke command.
        r'''
        "TEFT": "test",
        "R*S": "{*+}",

        TEFT/R*S

        " test test"
        '''

    @simple_replay
    def test_force_lowercase_title(self):
        r'''
        "T-LT": "{MODE:TITLE}",
        "TEFT": "{>}test",

        T-LT/TEFT

        " test"
        '''

    @simple_replay
    def test_bug471(self):
        # Repeat-last-stroke after typing two numbers outputs the numbers
        # reversed for some combos.
        r'''
        "R*S": "{*+}",

        12/R*S

        " 1212"
        '''

    @simple_replay
    def test_bug535(self):
        # Currency formatting a number with a decimal fails by not erasing
        # the previous output.
        r'''
        "P-P": "{^.^}",
        "KR*UR": "{*($c)}",

        1/P-P/2/KR*UR

        " $1.20"
        '''

    @simple_replay
    @spaces_after
    def test_bug606(self):
        r'''
        "KWEGS": "question",
        "-S": "{^s}",
        "TP-PL": "{.}",

        KWEGS/-S/TP-PL

        "questions. "
        '''

    @simple_replay
    @spaces_after
    def test_bug535_spaces_after(self):
        # Currency formatting a number with a decimal fails by not erasing
        # the previous output.
        r'''
        "P-P": "{^.^}",
        "KR*UR": "{*($c)}",

        1/P-P/2/KR*UR

        "$1.20 "
        '''

    @simple_replay
    @spaces_after
    def test_bug557(self):
        # Using the asterisk key to delete letters in fingerspelled words
        # occasionally causes problems when the space placement is set to
        # "After Output".
        r'''
        "EU": "I",
        "HRAOEUBG": "like",
        "T*": "{>}{&t}",
        "A*": "{>}{&a}",
        "KR*": "{>}{&c}",
        "O*": "{>}{&o}",
        "S*": "{>}{&s}",

        EU/HRAOEUBG/T*/A*/KR*/O*/S*/*/*/*

        "I like ta "
        '''

    @simple_replay
    @spaces_after
    def test_bug557_resumed(self):
        # Using the asterisk key to delete letters in fingerspelled words
        # occasionally causes problems when the space placement is set to
        # "After Output".
        r'''
        "EU": "I",
        "HRAOEUBG": "like",
        "T*": "{>}{&t}",
        "A*": "{>}{&a}",
        "KR*": "{>}{&c}",
        "O*": "{>}{&o}",
        "S*": "{>}{&s}",

        EU/HRAOEUBG/T*/A*/KR*/O*/S*/*/*/*/*/*/HRAOEUBG

        "I like like "
        '''

    @simple_replay
    @spaces_after
    def test_bug557_capitalized(self):
        # Using the asterisk key to delete letters in fingerspelled words
        # occasionally causes problems when the space placement is set to
        # "After Output".
        r'''
        "EU": "I",
        "HRAOEUBG": "like",
        "T*": "{-|}{&t}",
        "A*": "{-|}{&a}",
        "KR*": "{-|}{&c}",
        "O*": "{-|}{&o}",
        "S*": "{-|}{&s}",

        EU/HRAOEUBG/T*/A*/KR*/O*/S*/*/*/*

        "I like TA "
        '''

    @simple_replay
    @spaces_after
    def test_capitalized_fingerspelling_spaces_after(self):
        # Using the asterisk key to delete letters in fingerspelled words
        # occasionally causes problems when the space placement is set to
        # "After Output".
        r'''
        "HRAOEUBG": "like",
        "T*": "{&T}",
        "A*": "{&A}",
        "KR*": "{&C}",
        "O*": "{&O}",
        "S*": "{&S}",

        HRAOEUBG/T*/A*/KR*/O*/S*

        "like TACOS "
        '''

    @simple_replay
    def test_special_characters(self):
        r'''
        "R-R": "{^}\n{^}",
        "TAB": "\t",

        R-R/TAB

        "\n\t"
        '''

    @simple_replay
    def test_automatic_suffix_keys_1(self):
        r'''
        "RAEUS": "race",
        "RAEUZ": "raise",
        "-S": "{^s}",
        "-Z": "{^s}",

        RAEUSZ

        " races"
        '''
