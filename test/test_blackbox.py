
import unittest

from plover.steno import Stroke
from plover.formatting import Formatter
from plover.translation import Translator
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
    return stroke


class BlackboxTest(unittest.TestCase):

    def setUp(self):
        self.output = CaptureOutput()
        self.formatter = Formatter()
        self.formatter.set_output(self.output)
        self.translator = Translator()
        self.translator.add_listener(self.formatter.format)
        self.dictionary = self.translator.get_dictionary()
        self.dictionary.set_dicts([StenoDictionary()])

    def test_bug535(self):
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
