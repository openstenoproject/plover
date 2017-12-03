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
        # like the restrospective repeat-last-stroke command.

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

    def test_undo_not_defined(self):
        r'''
        'TEFT': 'test',

        TEFT  ' test'
        *     ''
        '''

    def test_undo_overriden(self):
        r'''
        'TEFT': 'test',
        '*': 'not undo',

        TEFT  ' test'
        *     ' test not undo'
        '''

    def test_undo_macro(self):
        r'''
        'TEFT': 'test',
        'TPH-D': '=undo',

        TEFT   ' test'
        TPH-D  ''
        '''

    def test_undo_fingerspelling_1(self):
        r'''
        'T*': '{>}{&t}',
        '*E': '{>}{&e}',
        'S*': '{>}{&s}',
        'T*': '{>}{&t}',

        T*/*E/S*/T*  ' test'
        */*          ' te'
        */*          ''
        '''

    def test_undo_fingerspelling_2(self):
        r'''
        'T*': '{>}{&t}',
        '*E': '{>}{&e}',
        'S*': '{>}{&s}',
        'T*': '{>}{&t}',

        :spaces_after
        T*/*E/S*/T*  'test '
        */*          'te '
        */*          ''
        '''

    def test_undo_replaced_1(self):
        r'''
        "TEFT": "test",
        "TEFT/TKPWOEFT": "{}",

        TEFT      ' test'
        TKPWOEFT  ''
        *         ' test'
        '''

    def test_undo_replaced_2(self):
        r'''
        "HROS": "loss",
        "HRO*S": "lost",
        "*P": "{*}",

        HROS   ' loss'
        *P     ' lost'
        *      ''
        '''

    def test_undo_replaced_3(self):
        r'''
        'PER': 'perfect',
        'SWAEUGS': 'situation',
        'PER/SWAEUGS': 'persuasion',
        'SP*': '{*?}',

        PER      ' perfect'
        SWAEUGS  ' persuasion'
        SP*      ' perfect situation'
        *        ' persuasion'
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

    def test_bug741(self):
        r'''
        # Uppercase last word also uppercases next word's prefix.

        "KPA*TS": "{*<}",
        "TPAO": "foo",
        "KAUPB": "{con^}",

        TPAO/KPA*TS/KAUPB/TPAO  " FOO confoo"
        '''

    def test_carry_capitalization_spacing1(self):
        r'''
        'S-P': '{^ ^}',
        'R-R': '{^~|\n^}',

        S-P/R-R  ' \n'
        '''

    def test_carry_capitalization_spacing2(self):
        r'''
        'S-P': '{^ ^}',
        'R-R': '{^~|\n^}',

        :spaces_after
        S-P/R-R  ' \n'
        '''

    def test_orthography1(self):
        r'''
        'TEFT': 'test',
        '-G': '{^ing}',

        TEFT/-G  ' testing'
        '''

    def test_orthography2(self):
        r'''
        'SKEL': 'cancel',
        '-G': '{^ing}',

        SKEL/-G  " canceling"
        '''

    def test_orthography3(self):
        r'''
        'PREPB': '{(^}',
        'SKEL': 'cancel',
        '-G': '{^ing}',

        PREPB/SKEL/-G  " (canceling"
        '''

    def test_orthography4(self):
        r'''
        'SKEL': '{&c}{&a}{&n}{&c}{&e}{&l}',
        '-G': '{^ing}',

        SKEL/-G  " canceling"
        '''

    def test_orthography5(self):
        r'''
        'TPAOEUPL': 'time',
        '-G': '{^ing}',

        TPAOEUPL/-G  ' timing'
        '''

    def test_orthography6(self):
        r'''
        'PRE': '{prefix-^}',
        'SKEL': 'cancel',
        '-G': '{^ing}',

        PRE/SKEL/-G  " prefix-canceling"
        '''

    def test_orthography7(self):
        r'''
        'PRE': '{prefix^}',
        'SKEL': 'cancel',
        '-G': '{^ing}',

        PRE/SKEL/-G  " prefixcanceling"
        '''

    def test_orthography8(self):
        r'''
        'PRE': '{&p}{&r}{&e}{&f}{&i}{&x}',
        "TK-LS": "{^}",
        'SKEL': 'cancel',
        '-G': '{^ing}',

        PRE/TK-LS/SKEL/-G  " prefixcanceling"
        '''

    def test_orthography9(self):
        r'''
        'PRE': '{prefix^}',
        'SKEL': '{&c}{&a}{&n}{&c}{&e}{&l}',
        '-G': '{^ing}',

        PRE/SKEL/-G  " prefixcanceling"
        '''

    def test_orthography10(self):
        r'''
        'PHO*D': "{MODE:CAMEL}",
        'PRE': '{prefix^}',
        'SKEL': 'cancel',
        '-G': '{^ing}',

        PHO*D/PRE/SKEL/-G  "prefixcanceling"
        '''

    def test_orthography11(self):
        r'''
        'PHO*D': "{MODE:SNAKE}",
        'TEFT': 'test',
        'SKEL': 'cancel',
        '-G': '{^ing}',

        PHO*D/TEFT  "_test"
        SKEL/-G     "_test_canceling"
        '''

    def test_orthography12(self):
        r'''
        'PHO*D': "{MODE:CAMEL}",
        'TEFT': 'test',
        'SKEL': 'cancel',
        '-G': '{^ing}',

        PHO*D/TEFT  "test"
        SKEL/-G     "testCanceling"
        '''

    def test_orthography13(self):
        r'''
        'PHO*D': "{MODE:SNAKE}",
        'PRE': '{prefix^}',
        'TEFT': 'test',
        'SKEL': 'cancel',
        '-G': '{^ing}',

        PHO*D/TEFT  "_test"
        PRE/SKEL/-G     "_test_prefixcanceling"
        '''

    def test_orthography14(self):
        r'''
        'PHO*D': "{MODE:CAMEL}",
        'PRE': '{prefix^}',
        'TEFT': 'test',
        'SKEL': 'cancel',
        '-G': '{^ing}',

        PHO*D/TEFT  "test"
        PRE/SKEL/-G     "testPrefixcanceling"
        '''

    def test_orthography15(self):
        r'''
        'PHO*D': "{MODE:CAPS}",
        'SKEL': 'cancel',
        '-G': '{^ing}',

        PHO*D/SKEL/-G  " CANCELING"
        '''

    def test_orthography16(self):
        r'''
        'SKEL': '{&C}{&A}{&N}{&C}{&E}{&L}',
        '-G': '{^ing}',

        SKEL/-G  " CANCELLing"
        '''

    def test_orthography17(self):
        r'''
        'SKEL': 'CANCEL',
        '-G': '{^ing}',

        SKEL/-G  " CANCELLing"
        '''

    def test_orthography18(self):
        r'''
        'TPAOEUPL': 'TIME',
        '-G': '{^ing}',

        TPAOEUPL/-G  ' TIMing'
        '''

    def test_orthography19(self):
        r'''
        'TPAOEUPL': '{&T}{&I}{&M}{&E}',
        '-G': '{^ing}',

        TPAOEUPL/-G  ' TIMing'
        '''

    def test_after_initial_being(self):
        r'''
        '-B': 'be',
        '-B/-G': 'being',

        :spaces_after
        -B/-G  'being '
        '''

    def test_after_period(self):
        r'''
        'TEFT': 'test',
        'P-P': '{.}',

        :spaces_after
        TEFT/P-P/TEFT  'test. Test '
        '''

    def test_spaces_after1(self):
        r'''
        'TEFT': 'test',
        'TEFTD': 'tested',
        '-G': '{^ing}',
        'P-P': '{.}',

        :spaces_after
        TEFT   'test '
        -G     'testing '
        P-P    'testing. '
        TEFTD  'testing. Tested '
        '''

    def test_start_attached1(self):
        r'''
        'TEFT': 'test',

        :start_attached
        TEFT  'test'
        '''

    def test_start_attached2(self):
        r'''
        'TEFT': 'test',

        :start_attached
        :spaces_after
        TEFT  'test '
        '''

    def test_space_placement_change1(self):
        r'''
        'TEFT': 'test',
        'TEFTD': 'tested',
        'TEFTS': 'tests',

        :spaces_before
        TEFT/TEFTD      ' test tested'
        :spaces_after
        TEFTS/TEFT      ' test tested tests test '
        '''

    def test_space_placement_change2(self):
        r'''
        'TEFT': 'test',
        'TEFTD': 'tested',
        'TEFTS': 'tests',

        :spaces_after
        TEFT/TEFTD      'test tested '
        :spaces_before
        TEFTS/TEFT      'test tested tests test'
        '''

    def test_undo_after_space_placement_change1(self):
        r'''
        'TEFT': 'test',
        'TEFTD': 'tested',

        :spaces_before
        TEFT/TEFTD      ' test tested'
        :spaces_after
        *               ' test '
        *               ''
        '''

    def test_undo_after_space_placement_change2(self):
        r'''
        'TEFT': 'test',
        'TEFTD': 'tested',

        :spaces_after
        TEFT/TEFTD      'test tested '
        :spaces_before
        *               'test'
        *               ''
        '''

    def test_undo_after_space_placement_change3(self):
        r'''
        'KPA': '{}{-|}',
        'TEFT': 'test',
        'TEFTD': 'tested',

        :spaces_before
        KPA/TEFT/TEFTD  ' Test tested'
        :spaces_after
        *               ' Test '
        *               ''
        '''

    def test_undo_after_space_placement_change4(self):
        r'''
        'KPA': '{}{-|}',
        'TEFT': 'test',
        'TEFTD': 'tested',

        :spaces_after
        KPA/TEFT/TEFTD  ' Test tested '
        :spaces_before
        *               ' Test'
        *               ''
        '''

    def test_undo_with_space_placement_changes(self):
        r'''
        'TEFT': 'test',

        TEFT/TEFT/TEFT  ' test test test'
        :spaces_after
        *               ' test test '
        :spaces_before
        *               ' test'
        :spaces_after
        *               ''
        '''

    def test_carry_capitalization1(self):
        r'''
        'KA*US': "{~|'^}cause",
        'TEFT': 'test',
        'P-P': '{.}',

        P-P/KA*US/TEFT  ". 'Cause test"
        '''

    def test_carry_capitalization2(self):
        r'''
        "KR-GS": "{^~|\"}",

        KR-GS  '"'
        '''

    def test_carry_capitalization3(self):
        r'''
        'TP*U': '{<}',
        "TK-LS": "{^}",
        'TEFT': 'test',
        'S-FBGS': '{^suffix}',

        TP*U/TEFT/S-FBGS/TK-LS/S-FBGS  ' TESTSUFFIXSUFFIX'
        '''

    def test_carry_capitalization4(self):
        r'''
        'TP*U': '{<}',
        "TK-LS": "{^}",
        'TEFT': 'test',
        "S-P": "{^ ^}"

        TP*U/TEFT/S-P/TEFT  ' TEST test'
        '''

    def test_carry_capitalization5(self):
        r'''
        'TP*U': '{<}',
        "TK-LS": "{^}",
        'TEFT': 'test',
        'S-FBGS': '{^suffix}',
        "S-P": "{^ ^}"

        TP*U/TEFT/S-FBGS/S-P/S-FBGS  ' TESTSUFFIX suffix'
        '''

    def test_capitalize1(self):
        r'''
        'KPA': '{}{-|}',
        'TEFT': 'test',

        KPA/TEFT  ' Test'
        '''

    def test_capitalize2(self):
        r'''
        'KPA': '{}{-|}',
        'TEFT': 'test',

        :start_attached
        KPA/TEFT  ' Test'
        '''

    def test_capitalize3(self):
        r'''
        'KPA': '{}{-|}',
        'TEFT': 'test',

        :spaces_after
        KPA/TEFT  ' Test '
        '''

    def test_capitalize4(self):
        r'''
        'KPA': '{}{-|}',
        'TEFT': 'test',

        :start_attached
        :spaces_after
        KPA/TEFT  ' Test '
        '''

    def test_retro_capitalize1(self):
        r'''
        'KWEUP': 'equip',
        'RUP': '{*-|}',

        KWEUP/RUP  ' Equip'
        '''

    def test_retro_capitalize2(self):
        r'''
        'KWEUP': 'equip',
        'RUP': '{*-|}',

        :spaces_after
        KWEUP/RUP  'Equip '
        '''

    def test_retro_capitalize3(self):
        r'''
        'TEFT': 'tèśtîñg',
        'RUP': '{*-|}',

        TEFT/RUP  ' Tèśtîñg'
        '''

    def test_retro_capitalize4(self):
        r'''
        'PRE': '{pre^}',
        'TPEUBG': 'fix',
        'RUP': '{*-|}',

        PRE/TPEUBG/RUP  ' Prefix'
        '''

    def test_retro_currency1(self):
        r'''
        'TPHAPB': 'notanumber',
        'R-BG': '{*($c)}',

        TPHAPB/R-BG  ' notanumber'
        '''

    def test_retro_currency2(self):
        r'''
        'TPHAPB': 'notanumber',
        'R-BG': '{*($c)}',

        :spaces_after
        TPHAPB/R-BG  'notanumber '
        '''

    def test_retro_currency3(self):
        r'''
        'R-BG': '{*($c)}',

        0/R-BG  ' $0'
        '''

    def test_retro_currency4(self):
        r'''
        'R-BG': '{*($c)}',

        :spaces_after
        0/R-BG  '$0 '
        '''

    def test_retro_upper1(self):
        r'''
        'TEFT': 'test',
        '-G': '{^ing}',
        'PRE': '{pre^}',
        'R*U': '{*<}',

        TEFT/-G/R*U/PRE  " TESTING pre"
        '''

    def test_retro_upper2(self):
        r'''
        'TEFT': 'test',
        '-G': '{^ing}',
        'PRE': '{pre^}',
        'R*U': '{*<}',

        TEFT/R*U/-G/PRE  " TESTING pre"
        '''

    def test_retro_upper3(self):
        r'''
        'PRE': '{prefix^}',
        'WORD': 'word',
        'R*U': '{*<}',

        PRE/WORD/R*U  " PREFIXWORD"
        '''

    def test_retro_upper4(self):
        r'''
        'S-G': 'something',
        'R*U': '{*<}',

        S-G/S-G/R*U/R*U  " something SOMETHING"
        '''

    def test_retro_upper5(self):
        r'''
        'TEFT': 'tèśtîñg',
        'RUP': '{*<}',

        TEFT/RUP  ' TÈŚTÎÑG'
        '''

    def test_retro_upper6(self):
        r'''
        'ST': 'it is',
        'RUP': '{*<}',

        ST/RUP  " it IS"
        '''

    def test_retro_upper7(self):
        r'''
        'TEFT': 'test',
        "W-G": "{^ing with}",
        'RUP': '{*<}',

        TEFT/RUP/W-G  " TESTING with"
        '''

    def test_retro_upper8(self):
        r'''
        'TEFT': 'test',
        "W-G": "{^ing with}",
        'RUP': '{*<}',

        TEFT/W-G/RUP  " testing WITH"
        '''

    def test_retro_upper9(self):
        r'''
        'TEFT': 'test',
        "W-G": "{^ing with}",
        'RUP': '{*<}',

        TEFT/RUP/W-G/W-G  " TESTING withing with"
        '''

    def test_retro_upper10(self):
        r'''
        'TEFT': 'test',
        "W": "with",
        'RUP': '{*<}',

        TEFT/RUP/W/W  " TEST with with"
        '''

    def test_upper1(self):
        r'''
        'TP*U': '{<}',
        'TEFT': 'test',
        '-G': '{^ing}',
        'PRE': '{pre^}',

        TP*U/TEFT/-G/PRE  " TESTING pre"
        '''

    def test_upper2(self):
        r'''
        'TP*U': '{<}',
        'TEFT': 'test',
        '-G': '{^ing}',

        TP*U/TEFT/-G/TEFT  " TESTING test"
        '''

    def test_upper3(self):
        r'''
        'TP*U': '{<}',
        'ST': 'it is',

        TP*U/ST  " IT is"
        '''

    def test_upper4(self):
        r'''
        'TP*U': '{<}',
        'ST': 'it{ }is',

        TP*U/ST  " IT is"
        '''

    def test_upper5(self):
        r'''
        'TP*U': '{<}',
        'TEFT': 'test',
        "W-G": "{^ing with}",

        TP*U/TEFT/W-G  " TESTING with"
        '''

    def test_upper6(self):
        r'''
        'TP*U': '{<}',
        'P-': '{foo^}',
        '-S': '{^bar}',

        TP*U/P-/-S  " FOOBAR"
        '''

    def test_upper7(self):
        r'''
        'TP*U': '{<}',
        'PRE': '{pre^}',
        'TEFT': 'test',
        '-G': '{^ing}',

        TP*U/PRE/TEFT/-G  " PRETESTING"
        '''

    def test_upper8(self):
        r'''
        'TP*U': '{<}',
        'TEFT': 'test',
        "W-G": "{^ing with}",

        TP*U/TEFT/W-G/W-G  " TESTING withing with"
        '''

    def test_upper9(self):
        r'''
        'TP*U': '{<}',
        'TEFT': 'test',
        "W": "with",

        TP*U/TEFT/W/W  " TEST with with"
        '''

    def test_attach_glue_and_carry_capitalize(self):
        r'''
        'PH*': '{&m}',
        'KW-GS': '{~|"}',

        PH*/KW-GS  ' m "'
        '''

    def test_fingerspelling_retro_meta1(self):
        r'''
        'K': '{&c}',
        'A': '{&a}',
        'T': '{&t}',
        'UP': '{*<}',

        K/A/T  ' cat'
        UP     ' CAT'
        *      ' cat'
        '''

    def test_fingerspelling_retro_meta2(self):
        r'''
        'TPH': '{>}{&n}',
        'O': '{>}{&o}',
        'UP': '{*<}',

        TPH/O/UP  ' NO'
        '''

    def test_fingerspelling_retro_meta3(self):
        r'''
        'TEFT': '{>}{&n}{>}{&o}{*<}',

        TEFT  ' NO'
        '''

    def test_word_1(self):
        r'''
        "KA*PS": "{MODE:CAPS}",
        "TEFT": "test",
        "-G": "{^ing}",
        'RUP': '{*-|}',

        KA*PS/TEFT/-G  ' TESTING'
        RUP            ' TESTING'
        '''

    def test_word_2(self):
        r'''
        "KA*PS": "{MODE:CAPS}",
        "R*FT": "{MODE:RESET}",
        "TEFT": "test",
        "-G": "{^ing}",
        'RUL': '{*>}',

        KA*PS/TEFT/-G  ' TESTING'
        R*FT/RUL       ' tESTING'
        '''

    def test_cat_burger_1(self):
        r'''
        "KAT": "cat",
        "O*PB":  "{^on}",
        "PWURG": "{*-|}{^burg}",
        "*ER": "{^er}",
        "PWURG/*ER": "burger",

        KAT/O*PB/PWURG  ' Cattonburg'
        *ER             ' catton burger'
        '''

    def test_cat_burger_2(self):
        r'''
        "KAT": "cat",
        "O*PB":  "{^on}",
        "PWURG": "{*-|}{^burg}",
        "*ER": "{^er}",

        KAT/O*PB/PWURG  ' Cattonburg'
        *ER             ' Cattonburger'
        '''

    def test_mirrored_capitalize(self):
        r'''
        'KPA': '{}{-|}',
        'TEFT': '{~|na^}{~|no^}{~|wri^}mo'

        KPA/TEFT  ' NaNoWriMo'
        '''

    def test_mode_1a(self):
        r'''
        "PHO*D": "{MODE:CAMEL}",
        "TEFT": "test",

        :spaces_after
        TEFT   'test '
        PHO*D  'test '
        TEFT   'testtest'
        TEFT   'testtestTest'
        '''

    def test_mode_1b(self):
        r'''
        "PHO*D": "{MODE:CAMEL}",
        "TEFT": "test",

        :spaces_before
        TEFT   ' test'
        PHO*D  ' test'
        TEFT   ' testtest'
        TEFT   ' testtestTest'
        '''

    def test_mode_2a(self):
        r'''
        "PHO*D": "{MODE:CAMEL}",
        "TEFT": "test",
        "TKPWHRAOU": "{&g}{&l}{&u}{&e}"

        :spaces_after
        PHO*D  ''
        TEFT       'test'
        TKPWHRAOU  'testGlue'
        '''

    def test_mode_2b(self):
        r'''
        "PHO*D": "{MODE:CAMEL}",
        "TEFT": "test",
        "TKPWHRAOU": "{&g}{&l}{&u}{&e}"

        :spaces_before
        PHO*D  ''
        TEFT       'test'
        TKPWHRAOU  'testGlue'
        '''

    def test_mode_3a(self):
        r'''
        "PHO*D": "{MODE:CAMEL}",
        "TEFT": "test",
        "TKPWHRAOU": "{&g}{&l}{&u}{&e}"

        :spaces_after
        PHO*D  ''
        TKPWHRAOU  'glue'
        TEFT       'glueTest'
        '''

    def test_mode_3b(self):
        r'''
        "PHO*D": "{MODE:CAMEL}",
        "TEFT": "test",
        "TKPWHRAOU": "{&g}{&l}{&u}{&e}"

        :spaces_before
        PHO*D  ''
        TKPWHRAOU  'glue'
        TEFT       'glueTest'
        '''

    def test_fingerspelling_1a(self):
        r'''
        'K': '{&c}',
        'A': '{&a}',
        'T': '{&t}',

        :spaces_after
        K/A/T  'cat '
        '''
    def test_fingerspelling_1b(self):
        r'''
        'K': '{&c}',
        'A': '{&a}',
        'T': '{&t}',

        K/A/T  ' cat'
        '''

    def test_fingerspelling_2a(self):
        r'''
        'K': '{-|}{&c}',
        'A': '{-|}{&a}',
        'T': '{-|}{&t}',

        :spaces_after
        K/A/T  'CAT '
        '''

    def test_fingerspelling_2b(self):
        r'''
        'K': '{-|}{&c}',
        'A': '{-|}{&a}',
        'T': '{-|}{&t}',

        K/A/T  ' CAT'
        '''

    def test_numbers_1a(self):
        r'''
        '': ''

        :spaces_after
        1-9  '19 '
        -79  '1979 '
        *    '19 '
        *    ''
        '''

    def test_numbers_1b(self):
        r'''
        '': ''

        1-9  ' 19'
        -79  ' 1979'
        *    ' 19'
        *    ''
        '''

    def test_raw_1a(self):
        r'''
        '': ''

        :spaces_after
        RAU   'RAU '
        TEGT  'RAU TEGT '
        *     'RAU '
        *     ''
        '''

    def test_raw_1b(self):
        r'''
        '': ''

        RAU   ' RAU'
        TEGT  ' RAU TEGT'
        *     ' RAU'
        *     ''
        '''

    def test_bug287(self):
        r'''
        "*6": "a",
        "R*S": "{*+}",

        *6   ' a'
        R*S  ' a a'
        '''

    def test_bug470(self):
        r'''
        "0EU8": "80",
        "R*S": "{*+}",

        0EU8  ' 80'
        R*S   ' 8080'
        '''

    def test_bug851(self):
        r'''
        "KUPBTS": "countries",
        "R-R": "{^}{#Return}{^}{-|}",

        :spaces_after
        KUPBTS "countries "
        R-R "countries"
        '''

    def test_bug849_1(self):
        r'''
        "-P": ".",
        "*P": "{*}",
        "TKAOU": "due",
        "TKAO*U": "dew",

        TKAOU  ' due'
        -P      ' due .'
        *P     ' dew'
        '''

    def test_bug849_2(self):
        r'''
        "KPA*": "{^}{-|}",
        "*P": "{*}",
        "TKAOU": "due",
        "TKAO*U": "dew",

        KPA*   ''
        TKAOU  'Due'
        *P     'Dew'
        '''
