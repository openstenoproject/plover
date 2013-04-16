# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for translation.py."""

from collections import namedtuple
import copy
from mock import patch
from steno_dictionary import StenoDictionary
from translation import Translation, Translator, _State, _translate_stroke
import unittest

class Stroke(object):
    def __init__(self, rtfcre, is_correction=False):
        self.rtfcre = rtfcre
        self.is_correction = is_correction
        
    def __eq__(self, other):
        return isinstance(other, Stroke) and self.rtfcre == other.rtfcre
        
    def __ne__(self, other):
        return not not self.__eq__(other)

class TranslationTestCase(unittest.TestCase):
    def test_no_translation(self):
        d = StenoDictionary()
        t = Translation([Stroke('S'), Stroke('T')], d)
        self.assertEqual(t.strokes, [Stroke('S'), Stroke('T')])
        self.assertEqual(t.rtfcre, ('S', 'T'))
        self.assertIsNone(t.english)
        
    def test_translation(self):
        d = StenoDictionary()
        d[('S', 'T')] = 'translation'
        t = Translation([Stroke('S'), Stroke('T')], d)
        self.assertEqual(t.strokes, [Stroke('S'), Stroke('T')])
        self.assertEqual(t.rtfcre, ('S', 'T'))
        self.assertEqual(t.english, 'translation')

class TranslatorStateSizeTestCase(unittest.TestCase):
    class FakeState(_State):
        def __init__(self):
            super(type(self), self).__init__()
            self.restrict_calls = []
        def restrict_size(self, n):
            self.restrict_calls.append(n)

    def assert_size_call(self, size):
        self.assertEqual(self.s.restrict_calls[-1], size)

    def assert_no_size_call(self):
        self.assertEqual(self.s.restrict_calls, [])

    def clear(self):
        self.s.restrict_calls = []

    def setUp(self):
        self.t = Translator()
        self.s = type(self).FakeState()
        self.t._state = self.s
        self.d = StenoDictionary()
        self.t.set_dictionary(self.d)

    def test_dictionary_update_grows_size1(self):
        self.d[('S',)] = '1'
        self.assert_size_call(1)

    def test_dictionary_update_grows_size4(self):
        self.d[('S', 'PT', '-Z', 'TOP')] = 'hi'
        self.assert_size_call(4)

    def test_dictionary_update_no_grow(self):
        self.t.set_min_undo_length(4)
        self.assert_size_call(4)
        self.clear()
        self.d[('S', 'T')] = 'nothing'
        self.assert_size_call(4)

    def test_dictionary_update_shrink(self):
        self.d[('S', 'T', 'P', '-Z', '-D')] = '1'
        self.assert_size_call(5)
        self.clear()
        self.d[('A', 'P')] = '2'
        self.assert_no_size_call()
        del self.d[('S', 'T', 'P', '-Z', '-D')]
        self.assert_size_call(2)

    def test_dictionary_update_no_shrink(self):
        self.t.set_min_undo_length(7)
        self.d[('S', 'T', 'P', '-Z', '-D')] = '1'
        del self.d[('S', 'T', 'P', '-Z', '-D')]
        self.assert_size_call(7)

    def test_translation_calls_restrict(self):
        self.t.translate(Stroke('S'))
        self.assert_size_call(0)

class TranslatorTestCase(unittest.TestCase):

    def test_translate_calls_translate_stroke(self):
        t = Translator()
        s = Stroke('S')
        def check(stroke, state, dictionary, output):
            self.assertEqual(stroke, s)
            self.assertEqual(state, t._state)
            self.assertEqual(dictionary, t._dictionary)
            self.assertEqual(output, t._output)

        with patch('plover.translation._translate_stroke', check) as _translate_stroke:
            t.translate(s)

    def test_listeners(self):
        output1 = []
        def listener1(undo, do, prev):
            output1.append((undo, do, prev))
        
        output2 = []
        def listener2(undo, do, prev):
            output2.append((undo, do, prev))
        
        t = Translator()
        s = Stroke('S')
        tr = Translation([s], StenoDictionary())
        expected_output = [([], [tr], tr)]
        
        t.translate(s)
        
        t.add_listener(listener1)
        t.translate(s)
        self.assertEqual(output1, expected_output)
        
        del output1[:]
        t.add_listener(listener2)
        t.translate(s)
        self.assertEqual(output1, expected_output)
        self.assertEqual(output2, expected_output)

        del output1[:]
        del output2[:]
        t.add_listener(listener2)
        t.translate(s)
        self.assertEqual(output1, expected_output)
        self.assertEqual(output2, expected_output)

        del output1[:]
        del output2[:]
        t.remove_listener(listener1)
        t.translate(s)
        self.assertEqual(output1, [])
        self.assertEqual(output2, expected_output)

        del output1[:]
        del output2[:]
        t.remove_listener(listener2)
        t.translate(s)
        self.assertEqual(output1, [])
        self.assertEqual(output2, [])
        
    def test_changing_state(self):
        output = []
        def listener(undo, do, prev):
            output.append((undo, do, prev))

        d = StenoDictionary()
        d[('S', 'P')] = 'hi'
        t = Translator()
        t.set_dictionary(d)
        t.translate(Stroke('T'))
        t.translate(Stroke('S'))
        s = copy.deepcopy(t.get_state())
        
        t.add_listener(listener)
        
        expected = [([Translation([Stroke('S')], d)], 
                     [Translation([Stroke('S'), Stroke('P')], d)], 
                     Translation([Stroke('T')], d))]
        t.translate(Stroke('P'))
        self.assertEqual(output, expected)
        
        del output[:]
        t.set_state(s)
        t.translate(Stroke('P'))
        self.assertEqual(output, expected)
        
        del output[:]
        t.clear_state()
        t.translate(Stroke('P'))
        self.assertEqual(output, [([], [Translation([Stroke('P')], d)], None)])
        
        del output[:]
        t.set_state(s)
        t.translate(Stroke('P'))
        self.assertEqual(output, 
                         [([], 
                           [Translation([Stroke('P')], d)], 
                           Translation([Stroke('S'), Stroke('P')], d))])

    def test_translator(self):

        # It's not clear that this test is needed anymore. There are separate 
        # tests for _translate_stroke and test_translate_calls_translate_stroke 
        # makes sure that translate calls it properly. But since I already wrote
        # this test I'm going to keep it.

        class Output(object):
            def __init__(self):
                self._output = []
                
            def write(self, undo, do, prev):
                for t in undo:
                    self._output.pop()
                for t in do:
                    if t.english:
                        self._output.append(t.english)
                    else:
                        self._output.append('/'.join(t.rtfcre))
                        
            def get(self):
                return ' '.join(self._output)
                
            def clear(self):
                del self._output[:]
                
        d = StenoDictionary()        
        out = Output()        
        t = Translator()
        t.set_dictionary(d)
        t.add_listener(out.write)
        
        t.translate(Stroke('S'))
        self.assertEqual(out.get(), 'S')
        t.translate(Stroke('T'))
        self.assertEqual(out.get(), 'S T')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 'S')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 'S')  # Undo buffer ran out.
        
        t.set_min_undo_length(3)
        out.clear()
        t.translate(Stroke('S'))
        self.assertEqual(out.get(), 'S')
        t.translate(Stroke('T'))
        self.assertEqual(out.get(), 'S T')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 'S')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), '')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), '')  # Undo buffer ran out.
        
        out.clear()
        d[('S',)] = 't1'
        d[('T',)] = 't2'
        d[('S', 'T')] = 't3'
        
        t.translate(Stroke('S'))
        self.assertEqual(out.get(), 't1')
        t.translate(Stroke('T'))
        self.assertEqual(out.get(), 't3')
        t.translate(Stroke('T'))
        self.assertEqual(out.get(), 't3 t2')
        t.translate(Stroke('S'))
        self.assertEqual(out.get(), 't3 t2 t1')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 't3 t2')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 't3')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 't1')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), '')
        
        t.translate(Stroke('S'))
        self.assertEqual(out.get(), 't1')
        t.translate(Stroke('T'))
        self.assertEqual(out.get(), 't3')
        t.translate(Stroke('T'))
        self.assertEqual(out.get(), 't3 t2')

        d[('S', 'T', 'T')] = 't4'
        d[('S', 'T', 'T', 'S')] = 't5'
        
        t.translate(Stroke('S'))
        self.assertEqual(out.get(), 't5')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 't3 t2')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 't3')
        t.translate(Stroke('T'))
        self.assertEqual(out.get(), 't4')
        t.translate(Stroke('S'))
        self.assertEqual(out.get(), 't5')
        t.translate(Stroke('S'))
        self.assertEqual(out.get(), 't5 t1')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 't5')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 't4')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 't3')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 't1')
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), '')
        
        d.clear()

        t.translate(Stroke('S'))
        t.translate(Stroke('S'))
        t.translate(Stroke('S'))
        t.translate(Stroke('S'))
        t.translate(Stroke('*', True))
        t.translate(Stroke('*', True))
        t.translate(Stroke('*', True))
        t.translate(Stroke('*', True))
        self.assertEqual(out.get(), 'S')  # Not enough undo to clear output.
        
        out.clear()
        t.remove_listener(out.write)
        t.translate(Stroke('S'))
        self.assertEqual(out.get(), '')

class StateTestCase(unittest.TestCase):
    
    def setUp(self):
        d = StenoDictionary()
        self.a = Translation([Stroke('S')], d)
        self.b = Translation([Stroke('T'), Stroke('-D')], d)
        self.c = Translation([Stroke('-Z'), Stroke('P'), Stroke('T*')], d)
    
    def test_last_list0(self):
        s = _State()
        self.assertIsNone(s.last())    
    
    def test_last_list1(self):
        s = _State()
        s.translations = [self.a]
        self.assertEqual(s.last(), self.a)

    def test_last_list2(self):
        s = _State()
        s.translations = [self.a, self.b]
        self.assertEqual(s.last(), self.b)        

    def test_last_tail1(self):
        s = _State()
        s.translations = [self.a]
        s.tail = self.b
        self.assertEqual(s.last(), self.a)

    def test_last_tail0(self):
        s = _State()
        s.tail = self.b
        self.assertEqual(s.last(), self.b)
        
    def test_restrict_size_zero_on_empty(self):
        s = _State()
        s.restrict_size(0)
        self.assertEquals(s.translations, [])
        self.assertIsNone(s.tail)

    def test_restrict_size_zero_on_one_stroke(self):
        s = _State()
        s.translations = [self.a]
        s.restrict_size(0)
        self.assertEquals(s.translations, [self.a])
        self.assertIsNone(s.tail)

    def test_restrict_size_to_exactly_one_stroke(self):
        s = _State()
        s.translations = [self.a]
        s.restrict_size(1)
        self.assertEquals(s.translations, [self.a])
        self.assertIsNone(s.tail)
        
    def test_restrict_size_to_one_on_two_strokes(self):
        s = _State()
        s.translations = [self.b]
        s.restrict_size(1)
        self.assertEquals(s.translations, [self.b])
        self.assertIsNone(s.tail)

    def test_restrict_size_to_one_on_two_translations(self):
        s = _State()
        s.translations = [self.b, self.a]
        s.restrict_size(1)
        self.assertEquals(s.translations, [self.a])
        self.assertEqual(s.tail, self.b)

    def test_restrict_size_to_one_on_two_translations_too_big(self):
        s = _State()
        s.translations = [self.a, self.b]
        s.restrict_size(1)
        self.assertEquals(s.translations, [self.b])
        self.assertEqual(s.tail, self.a)

    def test_restrict_size_lose_translations(self):
        s = _State()
        s.translations = [self.a, self.b, self.c]
        s.restrict_size(2)
        self.assertEquals(s.translations, [self.c])
        self.assertEqual(s.tail, self.b)

    def test_restrict_size_multiple_translations(self):
        s = _State()
        s.translations = [self.a, self.b, self.c]
        s.restrict_size(5)
        self.assertEquals(s.translations, [self.b, self.c])
        self.assertEqual(s.tail, self.a)

class TranslateStrokeTestCase(unittest.TestCase):

    class CaptureOutput(object):
        output = namedtuple('output', 'undo do prev')
        
        def __init__(self):
            self.output = []

        def __call__(self, undo, new, prev):
            self.output = type(self).output(undo, new, prev)

    def t(self, strokes):
        """A quick way to make a translation."""
        return Translation([Stroke(x) for x in strokes.split('/')], self.d)

    def lt(self, translations):
        """A quick qay to make a list of translations."""
        return [self.t(x) for x in translations.split()]

    def define(self, key, value):
        self.d[tuple(key.split('/'))] = value

    def translate(self, stroke):
        _translate_stroke(stroke, self.s, self.d, self.o)

    def assertTranslations(self, expected):
        self.assertEqual(self.s.translations, expected)

    def assertOutput(self, undo, do, prev):
        self.assertEqual(self.o.output, (undo, do, prev))

    def setUp(self):
        self.d = StenoDictionary()
        self.s = _State()
        self.o = type(self).CaptureOutput()

    def test_first_stroke(self):
        self.translate(Stroke('-B'))
        self.assertTranslations(self.lt('-B'))
        self.assertOutput([], self.lt('-B'), None)

    def test_second_stroke(self):
        self.define('S/P', 'spiders')
        self.s.translations = self.lt('S')
        self.translate(Stroke('-T'))
        self.assertTranslations(self.lt('S -T'))
        self.assertOutput([], self.lt('-T'), self.t('S'))

    def test_second_stroke_tail(self):
        self.s.tail = self.t('T/A/I/L')
        self.translate(Stroke('E'))
        self.assertTranslations(self.lt('E'))
        self.assertOutput([], self.lt('E'), self.t('T/A/I/L'))

    def test_with_translation(self):
        self.define('S', 'is')
        self.define('-T', 'that')
        self.s.translations = self.lt('S')
        self.translate(Stroke('-T'))
        self.assertTranslations(self.lt('S -T'))
        self.assertOutput([], self.lt('-T'), self.t('S'))
        self.assertEqual(self.o.output.do[0].english, 'that')

    def test_finish_two_translation(self):
        self.define('S/T', 'hello')
        self.s.translations = self.lt('S')
        self.translate(Stroke('T'))
        self.assertTranslations(self.lt('S/T'))
        self.assertOutput(self.lt('S'), self.lt('S/T'), None)
        self.assertEqual(self.o.output.do[0].english, 'hello')
        self.assertEqual(self.o.output.do[0].replaced, self.lt('S'))

    def test_finish_three_translation(self):
        self.define('S/T/-B', 'bye')
        self.s.translations = self.lt('S T')
        self.translate(Stroke('-B'))
        self.assertTranslations(self.lt('S/T/-B'))
        self.assertOutput(self.lt('S T'), self.lt('S/T/-B'), None)
        self.assertEqual(self.o.output.do[0].english, 'bye')
        self.assertEqual(self.o.output.do[0].replaced, self.lt('S T'))

    def test_replace_translation(self):
        self.define('S/T/-B', 'longer')
        self.s.translations = self.lt('S/T')
        self.translate(Stroke('-B'))
        self.assertTranslations(self.lt('S/T/-B'))
        self.assertOutput(self.lt('S/T'), self.lt('S/T/-B'), None)
        self.assertEqual(self.o.output.do[0].english, 'longer')
        self.assertEqual(self.o.output.do[0].replaced, self.lt('S/T'))

    def test_undo(self):
        self.s.translations = self.lt('POP')
        self.translate(Stroke('*', True))
        self.assertTranslations([])
        self.assertOutput(self.lt('POP'), [], None)

    def test_empty_undo(self):
        self.translate(Stroke('*', True))
        self.assertTranslations([])
        self.assertOutput([], [], None)

    def test_undo_translation(self):
        self.define('P/P', 'pop')
        self.translate(Stroke('P'))
        self.translate(Stroke('P'))
        self.translate(Stroke('*', True))
        self.assertTranslations(self.lt('P'))
        self.assertOutput(self.lt('P/P'), self.lt('P'), None)

    def test_undo_longer_translation(self):
        self.define('P/P/-D', 'popped')
        self.translate(Stroke('P'))
        self.translate(Stroke('P'))
        self.translate(Stroke('-D'))
        self.translate(Stroke('*', True))
        self.assertTranslations(self.lt('P P'))
        self.assertOutput(self.lt('P/P/-D'), self.lt('P P'), None)

    def test_undo_tail(self):
        self.s.tail = self.t('T/A/I/L')
        self.translate(Stroke('*', True))
        self.assertTranslations([])
        self.assertOutput([], [], self.t('T/A/I/L'))

if __name__ == '__main__':
    unittest.main()
