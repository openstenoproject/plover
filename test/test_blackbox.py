# -*- coding: utf-8 -*-

import ast
import functools
import operator
import re
import textwrap

import pytest

from plover import system
from plover.formatting import Formatter
from plover.steno import Stroke, normalize_steno
from plover.steno_dictionary import StenoDictionary
from plover.translation import Translator


class CaptureOutput(object):

    def __init__(self):
        self.instructions = []
        self.text = ''

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


def replay(blackbox, name, test):
    # Hide from traceback on assertions (reduce output size for failed tests).
    __tracebackhide__ = operator.methodcaller('errisinstance', AssertionError)
    definitions, instructions = test.strip().rsplit('\n\n', 1)
    for steno, translation in ast.literal_eval(
        '{' + definitions + '}'
    ).items():
        blackbox.dictionary.set(normalize_steno(steno), translation)
    # Track line number for a more user-friendly assertion message.
    lines = test.split('\n')
    lnum = len(lines)-3 - test.rstrip().rsplit('\n\n', 1)[1].count('\n')
    for step in re.split('(?<=[^\\\\])\n', instructions):
        # Mark current instruction's line.
        lnum += 1
        msg = name + '\n' + '\n'.join(('> ' if n == lnum else '  ') + l
                                      for n, l in enumerate(lines))
        step = step.strip()
        # Support for changing some settings on the fly.
        if step.startswith(':'):
            action = step[1:]
            if action == 'start_attached':
                blackbox.formatter.start_attached = True
            elif action == 'spaces_after':
                blackbox.formatter.set_space_placement('After Output')
            elif action == 'spaces_before':
                blackbox.formatter.set_space_placement('Before Output')
            else:
                raise ValueError('invalid action:\n%s' % msg)
            continue
        # Replay strokes.
        strokes, output = step.split(None, 1)
        for s in normalize_steno(strokes.strip()):
            blackbox.translator.translate(steno_to_stroke(s))
        # Check output.
        expected_output = ast.literal_eval(output.strip())
        assert blackbox.output.text == expected_output, msg

def replay_doc(f):
    name = f.__name__
    test = textwrap.dedent(f.__doc__)
    # Use a lamdbda to reduce output size for failed tests.
    new_f = lambda bb: (f(bb), replay(bb, name, test))
    return functools.wraps(f)(new_f)


class TestBlackboxReplays(object):

    @classmethod
    def setup_class(cls):
        for name in dir(cls):
            if name.startswith('test_'):
                setattr(cls, name, replay_doc(getattr(cls, name)))

    def setup_method(self):
        self.output = CaptureOutput()
        self.formatter = Formatter()
        self.formatter.set_output(self.output)
        self.translator = Translator()
        self.translator.set_min_undo_length(100)
        self.translator.add_listener(self.formatter.format)
        self.dictionary = self.translator.get_dictionary()
        self.dictionary.set_dicts([StenoDictionary()])

    def test_translator_state_handling(self):
        r'''
        # Check if the translator curtailing the list of last translations
        # according to its dictionary longest key does no affect things
        # like the restrospective repeate-last-stroke command.

        "TEFT": "test",
        "R*S": "{*+}",

        TEFT/R*S  " test test"
        '''

    def test_force_lowercase_title(self):
        r'''
        "T-LT": "{MODE:TITLE}",
        "TEFT": "{>}test",

        T-LT/TEFT  " test"
        '''

    def test_bug471(self):
        r'''
        # Repeat-last-stroke after typing two numbers outputs the numbers
        # reversed for some combos.

        "R*S": "{*+}",

        12/R*S  " 1212"
        '''

    def test_bug535(self):
        r'''
        # Currency formatting a number with a decimal fails by not erasing
        # the previous output.

        "P-P": "{^.^}",
        "KR*UR": "{*($c)}",

        1/P-P/2/KR*UR  " $1.20"
        '''

    def test_bug606(self):
        r'''
        "KWEGS": "question",
        "-S": "{^s}",
        "TP-PL": "{.}",

        :spaces_after
        KWEGS/-S/TP-PL  "questions. "
        '''

    def test_bug535_spaces_after(self):
        r'''
        # Currency formatting a number with a decimal fails by not erasing
        # the previous output.

        "P-P": "{^.^}",
        "KR*UR": "{*($c)}",

        :spaces_after
        1/P-P/2/KR*UR  "$1.20 "
        '''

    def test_bug557(self):
        r'''
        # Using the asterisk key to delete letters in fingerspelled words
        # occasionally causes problems when the space placement is set to
        # "After Output".

        "EU": "I",
        "HRAOEUBG": "like",
        "T*": "{>}{&t}",
        "A*": "{>}{&a}",
        "KR*": "{>}{&c}",
        "O*": "{>}{&o}",
        "S*": "{>}{&s}",

        :spaces_after
        EU/HRAOEUBG/T*/A*/KR*/O*/S*/*/*/*  "I like ta "
        '''

    def test_bug557_resumed(self):
        r'''
        # Using the asterisk key to delete letters in fingerspelled words
        # occasionally causes problems when the space placement is set to
        # "After Output".

        "EU": "I",
        "HRAOEUBG": "like",
        "T*": "{>}{&t}",
        "A*": "{>}{&a}",
        "KR*": "{>}{&c}",
        "O*": "{>}{&o}",
        "S*": "{>}{&s}",

        :spaces_after
        EU/HRAOEUBG/T*/A*/KR*/O*/S*/*/*/*/*/*/HRAOEUBG  "I like like "
        '''

    def test_bug557_capitalized(self):
        r'''
        # Using the asterisk key to delete letters in fingerspelled words
        # occasionally causes problems when the space placement is set to
        # "After Output".

        "EU": "I",
        "HRAOEUBG": "like",
        "T*": "{-|}{&t}",
        "A*": "{-|}{&a}",
        "KR*": "{-|}{&c}",
        "O*": "{-|}{&o}",
        "S*": "{-|}{&s}",

        :spaces_after
        EU/HRAOEUBG/T*/A*/KR*/O*/S*/*/*/*  "I like TA "
        '''

    def test_capitalized_fingerspelling_spaces_after(self):
        r'''
        "HRAOEUBG": "like",
        "T*": "{&T}",
        "A*": "{&A}",
        "KR*": "{&C}",
        "O*": "{&O}",
        "S*": "{&S}",

        :spaces_after
        HRAOEUBG/T*/A*/KR*/O*/S*  "like TACOS "
        '''

    def test_special_characters(self):
        r'''
        "R-R": "{^}\n{^}",
        "TAB": "\t",

        R-R/TAB  "\n\t"
        '''

    def test_automatic_suffix_keys_1(self):
        r'''
        "RAEUS": "race",
        "RAEUZ": "raise",
        "-S": "{^s}",
        "-Z": "{^s}",

        RAEUSZ  " races"
        '''

    def test_bug719(self):
        r'''
        # Glue (&) does not work with "Spaces After".

        "P*": "{&P}"

        :spaces_after
        P*/P*/P*/P*/P*/P*  'PPPPPP '
        '''

    @pytest.mark.xfail
    def test_bug741(self):
        r'''
        # Uppercase last word also uppercases next word's prefix.

        "KPA*TS": "{*<}",
        "TPAO": "foo",
        "KAUPB": "{con^}",

        TPAO/KPA*TS/KAUPB/TPAO  " FOO confoo"
        '''

    @pytest.mark.xfail
    def test_carry_capitalization_spacing1(self):
        r'''
        'S-P': '{^ ^}',
        'R-R': '{^~|\n^}',

        S-P/R-R  ' \n'
        '''

    @pytest.mark.xfail
    def test_carry_capitalization_spacing2(self):
        r'''
        'S-P': '{^ ^}',
        'R-R': '{^~|\n^}',

        :spaces_after
        S-P/R-R  ' \n'
        '''
