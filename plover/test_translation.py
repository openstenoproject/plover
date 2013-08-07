# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for translation.py."""

from collections import namedtuple
import copy
from mock import patch
from steno_dictionary import StenoDictionary, StenoDictionaryCollection
from translation import Translation, Translator, _State, _translate_stroke, _lookup
import unittest
from plover.steno import Stroke, normalize_steno

def stroke(s):
    keys = []
    on_left = True
    for k in s:
        if k in 'EU*-':
            on_left = False
        if k == '-': 
            continue
        elif k == '*': 
            keys.append(k)
        elif on_left: 
            keys.append(k + '-')
        else:
            keys.append('-' + k)
    return Stroke(keys)

class TranslationTestCase(unittest.TestCase):
    def test_no_translation(self):
        t = Translation([stroke('S'), stroke('T')], None)
        self.assertEqual(t.strokes, [stroke('S'), stroke('T')])
        self.assertEqual(t.rtfcre, ('S', 'T'))
        self.assertIsNone(t.english)
        
    def test_translation(self):
        t = Translation([stroke('S'), stroke('T')], 'translation')
        self.assertEqual(t.strokes, [stroke('S'), stroke('T')])
        self.assertEqual(t.rtfcre, ('S', 'T'))
        self.assertEqual(t.english, 'translation')

class TranslatorStateSizeTestCase(unittest.TestCase):
    class FakeState(_State):
        def __init__(self):
            _State.__init__(self)
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
        self.dc = StenoDictionaryCollection()
        self.dc.set_dicts([self.d])
        self.t.set_dictionary(self.dc)

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
        self.t.translate(stroke('S'))
        self.assert_size_call(0)

class TranslatorTestCase(unittest.TestCase):

    def test_translate_calls_translate_stroke(self):
        t = Translator()
        s = stroke('S')
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
        s = stroke('S')
        tr = Translation([s], None)
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
        dc = StenoDictionaryCollection()
        dc.set_dicts([d])
        t = Translator()
        t.set_dictionary(dc)
        t.translate(stroke('T'))
        t.translate(stroke('S'))
        s = copy.deepcopy(t.get_state())
        
        t.add_listener(listener)
        
        expected = [([Translation([stroke('S')], None)], 
                     [Translation([stroke('S'), stroke('P')], 'hi')], 
                     Translation([stroke('T')], None))]
        t.translate(stroke('P'))
        self.assertEqual(output, expected)
        
        del output[:]
        t.set_state(s)
        t.translate(stroke('P'))
        self.assertEqual(output, expected)
        
        del output[:]
        t.clear_state()
        t.translate(stroke('P'))
        self.assertEqual(output, [([], [Translation([stroke('P')], None)], None)])
        
        del output[:]
        t.set_state(s)
        t.translate(stroke('P'))
        self.assertEqual(output, 
                         [([], 
                           [Translation([stroke('P')], None)], 
                           Translation([stroke('S'), stroke('P')], 'hi'))])

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
        dc = StenoDictionaryCollection()
        dc.set_dicts([d])
        t.set_dictionary(dc)
        t.add_listener(out.write)
        
        t.translate(stroke('S'))
        self.assertEqual(out.get(), 'S')
        t.translate(stroke('T'))
        self.assertEqual(out.get(), 'S T')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 'S')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 'S')  # Undo buffer ran out.
        
        t.set_min_undo_length(3)
        out.clear()
        t.translate(stroke('S'))
        self.assertEqual(out.get(), 'S')
        t.translate(stroke('T'))
        self.assertEqual(out.get(), 'S T')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 'S')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), '')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), '')  # Undo buffer ran out.
        
        out.clear()
        d[('S',)] = 't1'
        d[('T',)] = 't2'
        d[('S', 'T')] = 't3'
        
        t.translate(stroke('S'))
        self.assertEqual(out.get(), 't1')
        t.translate(stroke('T'))
        self.assertEqual(out.get(), 't3')
        t.translate(stroke('T'))
        self.assertEqual(out.get(), 't3 t2')
        t.translate(stroke('S'))
        self.assertEqual(out.get(), 't3 t2 t1')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 't3 t2')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 't3')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 't1')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), '')
        
        t.translate(stroke('S'))
        self.assertEqual(out.get(), 't1')
        t.translate(stroke('T'))
        self.assertEqual(out.get(), 't3')
        t.translate(stroke('T'))
        self.assertEqual(out.get(), 't3 t2')

        d[('S', 'T', 'T')] = 't4'
        d[('S', 'T', 'T', 'S')] = 't5'
        
        t.translate(stroke('S'))
        self.assertEqual(out.get(), 't5')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 't3 t2')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 't3')
        t.translate(stroke('T'))
        self.assertEqual(out.get(), 't4')
        t.translate(stroke('S'))
        self.assertEqual(out.get(), 't5')
        t.translate(stroke('S'))
        self.assertEqual(out.get(), 't5 t1')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 't5')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 't4')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 't3')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), 't1')
        t.translate(stroke('*'))
        self.assertEqual(out.get(), '')
        
        d.clear()

        s = stroke('S')
        t.translate(s)
        t.translate(s)
        t.translate(s)
        t.translate(s)
        s = stroke('*')
        t.translate(s)
        t.translate(s)
        t.translate(s)
        t.translate(s)
        self.assertEqual(out.get(), 'S')  # Not enough undo to clear output.
        
        out.clear()
        t.remove_listener(out.write)
        t.translate(stroke('S'))
        self.assertEqual(out.get(), '')

class StateTestCase(unittest.TestCase):
    
    def setUp(self):
        self.a = Translation([stroke('S')], None)
        self.b = Translation([stroke('T'), stroke('-D')], None)
        self.c = Translation([stroke('-Z'), stroke('P'), stroke('T*')], None)
    
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
        strokes = [stroke(x) for x in strokes.split('/')]
        return Translation(strokes, _lookup(strokes, self.dc, []))

    def lt(self, translations):
        """A quick way to make a list of translations."""
        return [self.t(x) for x in translations.split()]

    def define(self, key, value):
        key = normalize_steno(key)
        self.d[key] = value

    def translate(self, stroke):
        _translate_stroke(stroke, self.s, self.dc, self.o)

    def assertTranslations(self, expected):
        self.assertEqual(self.s.translations, expected)

    def assertOutput(self, undo, do, prev):
        self.assertEqual(self.o.output, (undo, do, prev))

    def setUp(self):
        self.d = StenoDictionary()
        self.dc = StenoDictionaryCollection()
        self.dc.set_dicts([self.d])
        self.s = _State()
        self.o = type(self).CaptureOutput()

    def test_first_stroke(self):
        self.translate(stroke('-B'))
        self.assertTranslations(self.lt('-B'))
        self.assertOutput([], self.lt('-B'), None)

    def test_second_stroke(self):
        self.define('S/P', 'spiders')
        self.s.translations = self.lt('S')
        self.translate(stroke('-T'))
        self.assertTranslations(self.lt('S -T'))
        self.assertOutput([], self.lt('-T'), self.t('S'))

    def test_second_stroke_tail(self):
        self.s.tail = self.t('T/A/I/L')
        self.translate(stroke('-E'))
        self.assertTranslations(self.lt('E'))
        self.assertOutput([], self.lt('E'), self.t('T/A/I/L'))

    def test_with_translation(self):
        self.define('S', 'is')
        self.define('-T', 'that')
        self.s.translations = self.lt('S')
        self.translate(stroke('-T'))
        self.assertTranslations(self.lt('S -T'))
        self.assertOutput([], self.lt('-T'), self.t('S'))
        self.assertEqual(self.o.output.do[0].english, 'that')

    def test_finish_two_translation(self):
        self.define('S/T', 'hello')
        self.s.translations = self.lt('S')
        self.translate(stroke('T'))
        self.assertTranslations(self.lt('S/T'))
        self.assertOutput(self.lt('S'), self.lt('S/T'), None)
        self.assertEqual(self.o.output.do[0].english, 'hello')
        self.assertEqual(self.o.output.do[0].replaced, self.lt('S'))

    def test_finish_three_translation(self):
        self.define('S/T/-B', 'bye')
        self.s.translations = self.lt('S T')
        self.translate(stroke('-B'))
        self.assertTranslations(self.lt('S/T/-B'))
        self.assertOutput(self.lt('S T'), self.lt('S/T/-B'), None)
        self.assertEqual(self.o.output.do[0].english, 'bye')
        self.assertEqual(self.o.output.do[0].replaced, self.lt('S T'))

    def test_replace_translation(self):
        self.define('S/T/-B', 'longer')
        self.s.translations = self.lt('S/T')
        self.translate(stroke('-B'))
        self.assertTranslations(self.lt('S/T/-B'))
        self.assertOutput(self.lt('S/T'), self.lt('S/T/-B'), None)
        self.assertEqual(self.o.output.do[0].english, 'longer')
        self.assertEqual(self.o.output.do[0].replaced, self.lt('S/T'))

    def test_undo(self):
        self.s.translations = self.lt('POP')
        self.translate(stroke('*'))
        self.assertTranslations([])
        self.assertOutput(self.lt('POP'), [], None)

    def test_empty_undo(self):
        self.translate(stroke('*'))
        self.assertTranslations([])
        self.assertOutput([], [], None)

    def test_undo_translation(self):
        self.define('P/P', 'pop')
        self.translate(stroke('P'))
        self.translate(stroke('P'))
        self.translate(stroke('*'))
        self.assertTranslations(self.lt('P'))
        self.assertOutput(self.lt('P/P'), self.lt('P'), None)

    def test_undo_longer_translation(self):
        self.define('P/P/-D', 'popped')
        self.translate(stroke('P'))
        self.translate(stroke('P'))
        self.translate(stroke('-D'))
        self.translate(stroke('*'))
        self.assertTranslations(self.lt('P P'))
        self.assertOutput(self.lt('P/P/-D'), self.lt('P P'), None)

    def test_undo_tail(self):
        self.s.tail = self.t('T/A/I/L')
        self.translate(stroke('*'))
        self.assertTranslations([])
        self.assertOutput([], [], self.t('T/A/I/L'))
        
    def test_suffix_folding(self):
        self.define('K-L', 'look')
        self.define('-G', '{^ing}')
        lt = self.lt('K-LG')
        lt[0].english = 'look {^ing}'
        self.translate(stroke('K-LG'))
        self.assertTranslations(lt)

    def test_suffix_folding_multi_stroke(self):
        self.define('E/HR', 'he will')
        self.define('-S', '{^s}')
        self.translate(stroke('E'))
        self.translate(stroke('HR-S'))
        output = ' '.join(t.english for t in self.s.translations)
        self.assertEqual(output, 'he will {^s}')

    def test_suffix_folding_doesnt_interfere(self):
        self.define('E/HR', 'he will')
        self.define('-S', '{^s}')
        self.define('E', 'he')
        self.define('HR-S', 'also')
        self.translate(stroke('E'))
        self.translate(stroke('HR-S'))
        output = ' '.join(t.english for t in self.s.translations)
        self.assertEqual(output, 'he also')

    def test_suffix_folding_no_suffix(self):
        self.define('K-L', 'look')
        lt = self.lt('K-LG')
        self.assertEqual(lt[0].english, None)
        self.translate(stroke('K-LG'))
        self.assertTranslations(lt)
        
    def test_suffix_folding_no_main(self):
        self.define('-G', '{^ing}')
        lt = self.lt('K-LG')
        self.assertEqual(lt[0].english, None)
        self.translate(stroke('K-LG'))
        self.assertTranslations(lt)
    

if __name__ == '__main__':
    unittest.main()
