# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for formatting.py."""

import formatting
import unittest

# Add tests with partial output specified.

def action(**kwargs):
    return formatting._Action(**kwargs)

class CaptureOutput(object):
    def __init__(self):
        self.instructions = []
    
    def send_backspaces(self, n):
        self.instructions.append(('b', n))
        
    def send_string(self, s):
        self.instructions.append(('s', s))
        
    def send_key_combination(self, c):
        self.instructions.append(('c', c))
        
    def send_engine_command(self, c):
        self.instructions.append(('e', c))

class MockTranslation(object):
    def __init__(self, rtfcre=tuple(), english=None, formatting=None):
        self.rtfcre = rtfcre
        self.english = english
        self.formatting = formatting
        
    def __str__(self):
        return str(self.__dict__)
        
def translation(**kwargs):
    return MockTranslation(**kwargs)

class FormatterTestCase(unittest.TestCase):

    def check(self, f, cases):
        for input, output in cases:
            self.assertEqual(f(input), output)
            
    def check_arglist(self, f, cases):
        for inputs, expected in cases:
            actual = f(*inputs)
            if actual != expected:
                print actual, '!=', expected, 'for', inputs
            self.assertEqual(actual, expected)

    def test_formatter(self):
        cases = (

        (
         ([translation(formatting=[action(text='hello')])], [], None),
         (),
         [('b', 5)]
        ),
        
        (
         ([], 
          [translation(rtfcre=('S'), english='hello')], 
          translation(rtfcre=('T'), english='a', formatting=[action(text='f')])
         ),
         ([action(text=' hello', word='hello')],),
         [('s', ' hello')]
        ),
        
        (
         ([], [translation(rtfcre=('S'), english='hello')], None),
         ([action(text=' hello', word='hello')],),
         [('s', ' hello')]
        ),
        
        (
         ([], [translation(rtfcre=('ST-T',))], None),
         ([action(text=' ST-T', word='ST-T')],),
         [('s', ' ST-T')]
        ),
        
        (
         ([], 
          [translation(rtfcre=('ST-T',))], 
          translation(formatting=[action(text='hi')])),
         ([action(text=' ST-T', word='ST-T')],),
         [('s', ' ST-T')]
        ),
        
        (
         ([translation(formatting=[action(text=' test')])],
          [translation(english='rest')],
          translation(formatting=[action(capitalize=True)])),
         ([action(text=' Rest', word='Rest')],),
         [('b', 4), ('s', 'Rest')]
        ),
        
        (
         ([translation(formatting=[action(text='dare'), 
                                   action(text='ing', replace='e')])],
         [translation(english='rest')],
         translation(formatting=[action(capitalize=True)])),
         ([action(text=' Rest', word='Rest')],),
         [('b', 6), ('s', ' Rest')]
        ),
        
        (
         ([translation(formatting=[action(text=' drive')])],
         [translation(english='driving')],
         None),
         ([action(text=' driving', word='driving')],),
         [('b', 1), ('s', 'ing')]
        ),
        
        (
         ([translation(formatting=[action(text=' drive')])],
         [translation(english='{#c}driving')],
         None),
         ([action(combo='c'), action(text=' driving', word='driving')],),
         [('b', 6), ('c', 'c'), ('s', ' driving')]
        ),
        
        (
         ([translation(formatting=[action(text=' drive')])],
         [translation(english='{PLOVER:c}driving')],
         None),
         ([action(command='c'), action(text=' driving', word='driving')],),
         [('b', 6), ('e', 'c'), ('s', ' driving')]
        ),
        
        (
         ([],
          [translation(rtfcre=('1',))],
          None),
         ([action(text=' 1', word='1', glue=True)],),
         [('s', ' 1')]
        ),
        
        (
         ([],
          [translation(rtfcre=('1',))],
          translation(formatting=[action(text='hi', word='hi')])),
         ([action(text=' 1', word='1', glue=True)],),
         [('s', ' 1')]
        ),

        (
         ([],
          [translation(rtfcre=('1',))],
          translation(formatting=[action(text='hi', word='hi', glue=True)])),
         ([action(text='1', word='hi1', glue=True)],),
         [('s', '1')]
        ),

        (
         ([],
          [translation(rtfcre=('1-9',))],
          translation(formatting=[action(text='hi', word='hi', glue=True)])),
         ([action(text='19', word='hi19', glue=True)],),
         [('s', '19')]
        ),

        (
         ([],
          [translation(rtfcre=('ST-PL',))],
          translation(formatting=[action(text='hi', word='hi')])),
         ([action(text=' ST-PL', word='ST-PL')],),
         [('s', ' ST-PL')]
        ),

        (
         ([],
          [translation(rtfcre=('ST-PL',))],
          None),
         ([action(text=' ST-PL', word='ST-PL')],),
         [('s', ' ST-PL')]
        ),

        )

        for args, formats, outputs in cases:
            output = CaptureOutput()
            formatter = formatting.Formatter()
            formatter.set_output(output)
            undo, do, prev = args
            formatter.format(undo, do, prev)
            for i in xrange(len(do)):
                self.assertEqual(do[i].formatting, formats[i])
            self.assertEqual(output.instructions, outputs)

    def test_get_last_action(self):
        self.assertEqual(formatting._get_last_action(None), action())
        self.assertEqual(formatting._get_last_action([]), action())
        actions = [action(text='hello'), action(text='world')]
        self.assertEqual(formatting._get_last_action(actions), actions[-1])

    def test_action(self):
        self.assertNotEqual(action(word='test'), 
                            action(word='test', attach=True))
        self.assertEqual(action(text='test'), action(text='test'))
        self.assertEqual(action(text='test', word='test').copy_state(),
                         action(word='test'))

    def test_translation_to_actions(self):
        cases = [
        (('test', action()), 
         [action(text=' test', word='test')]),
        
        (('{^^}', action()), [action(attach=True, orthography=False)]),
         
        (('1-9', action()), 
         [action(word='1-9', text=' 1-9')]),
         
        (('32', action()), 
         [action(word='32', text=' 32', glue=True)]),
         
        (('', action(text=' test', word='test', attach=True)),
         [action(word='test', attach=True)]),
         
        (('  ', action(text=' test', word='test', attach=True)),
         [action(word='test', attach=True)]),
         
        (('{^} {.} hello {.} {#ALT_L(Grave)}{^ ^}', action()),
         [action(attach=True, orthography=False), 
          action(text='.', capitalize=True), 
          action(text=' Hello', word='Hello'), 
          action(text='.', capitalize=True), 
          action(combo='ALT_L(Grave)', capitalize=True),
          action(text=' ', attach=True)
         ]),
         
         (('{-|} equip {^s}', action()),
          [action(capitalize=True),
           action(text=' Equip', word='Equip'),
           action(text='s', word='Equips'),
          ]),

        (('{-|} equip {^ed}', action()),
         [action(capitalize=True),
          action(text=' Equip', word='Equip'),
          action(text='ped', word='Equipped'),
         ]),

        (('{>} Equip', action()),
         [action(lower=True),
          action(text=' equip', word='equip')
         ]),

        (('{>} equip', action()),
         [action(lower=True),
          action(text=' equip', word='equip')
         ]),
         
        (('equip {^} {^ed}', action()),
         [action(text=' equip', word='equip'),
          action(word='equip', attach=True, orthography=False),
          action(text='ed', word='equiped'),
         ]),
        ]
        self.check_arglist(formatting._translation_to_actions, cases)

    def test_raw_to_actions(self):
        cases = (

        (
         ('2-6', action()),
         [action(glue=True, text=' 26', word='26')]
        ),

        (
         ('2', action()),
         [action(glue=True, text=' 2', word='2')]
        ),

        (
         ('-8', action()),
         [action(glue=True, text=' 8', word='8')]
        ),


        (
         ('-68', action()),
         [action(glue=True, text=' 68', word='68')]
        ),

        (
         ('S-T', action()),
         [action(text=' S-T', word='S-T')]
        ),


        )
        self.check_arglist(formatting._raw_to_actions, cases)

    def test_atom_to_action(self):
        cases = [
        (('{^ed}', action(word='test')), 
         action(text='ed', replace='', word='tested')),
         
        (('{^ed}', action(word='carry')), 
         action(text='ied', replace='y', word='carried')),
          
        (('{^er}', action(word='test')), 
         action(text='er', replace='', word='tester')),
         
        (('{^er}', action(word='carry')), 
         action(text='ier', replace='y', word='carrier')),
                 
        (('{^ing}', action(word='test')), 
         action(text='ing', replace='', word='testing')),

        (('{^ing}', action(word='begin')), 
         action(text='ning', replace='', word='beginning')),
        
        (('{^ing}', action(word='parade')), 
         action(text='ing', replace='e', word='parading')),
                 
        (('{^s}', action(word='test')), 
         action(text='s', replace='', word='tests')),
                 
        (('{,}', action(word='test')), action(text=',')),
         
        (('{:}', action(word='test')), action(text=':')),
         
        (('{;}', action(word='test')), action(text=';')),
         
        (('{.}', action(word='test')), 
         action(text='.', capitalize=True)),
         
        (('{?}', action(word='test')),
         action(text='?', capitalize=True)),

        (('{!}', action(word='test')),
         action(text='!', capitalize=True)),

        (('{-|}', action(word='test')),
         action(capitalize=True, word='test')),

        (('{>}', action(word='test')),
         action(lower=True, word='test')),
          
        (('{PLOVER:test_command}', action(word='test')),
         action(word='test', command='test_command')),
          
        (('{&glue_text}', action(word='test')),
         action(text=' glue_text', word='glue_text', glue=True)),

        (('{&glue_text}', action(word='test', glue=True)),
         action(text='glue_text', word='testglue_text', glue=True)),
           
        (('{&glue_text}', action(word='test', attach=True)),
         action(text='glue_text', word='testglue_text', glue=True)),
           
        (('{^attach_text}', action(word='test')),
         action(text='attach_text', word='testattach_text')),
          
        (('{^attach_text^}', action(word='test')),
         action(text='attach_text', word='testattach_text', attach=True)),
          
        (('{attach_text^}', action(word='test')),
         action(text=' attach_text', word='attach_text', attach=True)),
                
        (('{#ALT_L(A)}', action(word='test')), 
         action(combo='ALT_L(A)', word='test')),
         
        (('text', action(word='test')), 
         action(text=' text', word='text')),

        (('text', action(word='test', glue=True)), 
         action(text=' text', word='text')),
         
        (('text', action(word='test', attach=True)), 
         action(text='text', word='text')),
         
        (('text', action(word='test', capitalize=True)), 
         action(text=' Text', word='Text')),

        (('some text', action(word='test')), 
         action(text=' some text', word='text')),

        ]
        self.check_arglist(formatting._atom_to_action, cases)
    
    def test_get_meta(self):
        cases = [('', None), ('{abc}', 'abc'), ('abc', None)]
        self.check(formatting._get_meta, cases)
    
    def test_apply_glue(self):
        cases = [('abc', '{&abc}'), ('1', '{&1}')]
        self.check(formatting._apply_glue, cases)
    
    def test_unescape_atom(self):
        cases = [('', ''), ('abc', 'abc'), (r'\{', '{'), (r'\}', '}'), 
                 (r'\{abc\}}{', '{abc}}{')]
        self.check(formatting._unescape_atom, cases)
    
    def test_get_engine_command(self):
        cases = [('', None), ('{PLOVER:command}', 'command')]
        self.check(formatting._get_engine_command, cases)
    
    def test_capitalize(self):
        cases = [('', ''), ('abc', 'Abc'), ('ABC', 'ABC')]
        self.check(formatting._capitalize, cases)
    
    def test_rightmost_word(self):
        cases = [('', ''), ('abc', 'abc'), ('a word', 'word'), 
                 ('word.', 'word.')]
        self.check(formatting._rightmost_word, cases)

if __name__ == '__main__':
    unittest.main()
