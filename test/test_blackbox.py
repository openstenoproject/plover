
import unittest

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
    stroke = Stroke(())
    stroke.rtfcre = steno
    stroke.is_correction = steno == '*'
    return stroke


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

    def test_translator_state_handling(self):
        # Check if the translator curtailing the list of last translations
        # according to its dictionary longest key does no affect things
        # like the restrospective repeate-last-stroke command.
        self.dictionary.set(('TEFT',), 'test')
        self.dictionary.set(('R*S',), '{*+}')
        # Note: the implementation of repeat-last-stroke looks at the last
        # stroke keys, so we can't use the same trick as for other tests.
        for keys in (
            ('T-', '-E', '-F', '-T'),
            ('R-', '*', '-S'),
        ):
            stroke = Stroke(keys)
            self.translator.translate(stroke)
        self.assertEqual(self.output.text, u' test test')

    def test_bug471(self):
        # Repeat-last-stroke after typing two numbers outputs the numbers
        # reversed for some combos.
        self.dictionary.set(('R*S',), '{*+}')
        # Note: the implementation of repeat-last-stroke looks at the last
        # stroke keys, so we can't use the same trick as for other tests.
        for keys in (
            ('#', 'S-', 'T-'), # 12
            ('R-', '*', '-S'),
        ):
            stroke = Stroke(keys)
            self.translator.translate(stroke)
        self.assertEqual(self.output.text, u' 1212')

    def test_bug535(self):
        # Currency formatting a number with a decimal fails by not erasing
        # the previous output.
        self.dictionary.set(('P-P',), '{^.^}')
        self.dictionary.set(('KR*UR',), '{*($c)}')
        for steno in (
            '1',
            'P-P',
            '2',
            'KR*UR',
        ):
            stroke = steno_to_stroke(steno)
            self.translator.translate(stroke)
        self.assertEqual(self.output.text, u' $1.20')

    @unittest.expectedFailure
    def test_bug557(self):
        # Using the asterisk key to delete letters in fingerspelled words
        # occasionally causes problems when the space placement is set to
        # "After Output".
        for steno, translation in (
            ('EU'      , 'I'      ),
            ('HRAOEUBG', 'like'   ),
            ('T*'      , '{>}{&t}'),
            ('A*'      , '{>}{&a}'),
            ('KR*'     , '{>}{&c}'),
            ('O*'      , '{>}{&o}'),
            ('S*'      , '{>}{&s}'),
        ):
            self.dictionary.set(normalize_steno(steno), translation)
        self.formatter.set_space_placement('After Output')
        for steno in (
            'EU',
            'HRAOEUBG',
            'T*', 'A*', 'KR*', 'O*', 'S*',
                          '*',  '*',  '*',
        ):
            stroke = steno_to_stroke(steno)
            self.translator.translate(stroke)
        self.assertEqual(self.output.text, u'I like ta ')

    def test_special_characters(self):
        self.dictionary.set(('R-R',), '{^}\n{^}')
        self.dictionary.set(('TAB',), '\t')
        for steno in (
            'R-R',
            'TAB',
        ):
            stroke = steno_to_stroke(steno)
            self.translator.translate(stroke)
        self.assertEqual(self.output.text, u'\n\t')
