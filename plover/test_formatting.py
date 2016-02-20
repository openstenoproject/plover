# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for formatting.py."""

from plover import formatting
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
            formatter.set_space_placement('Before Output')
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
        (('test', action(), False), 
         [action(text=' test', word='test')]),
        
        (('{^^}', action(), False), [action(attach=True, orthography=False)]),
         
        (('1-9', action(), False), 
         [action(word='1-9', text=' 1-9')]),
         
        (('32', action(), False), 
         [action(word='32', text=' 32', glue=True)]),
         
        (('', action(text=' test', word='test', attach=True), False),
         [action(word='test', attach=True)]),
         
        (('  ', action(text=' test', word='test', attach=True), False),
         [action(word='test', attach=True)]),
         
        (('{^} {.} hello {.} {#ALT_L(Grave)}{^ ^}', action(), False),
         [action(attach=True, orthography=False), 
          action(text='.', capitalize=True), 
          action(text=' Hello', word='Hello'), 
          action(text='.', capitalize=True), 
          action(combo='ALT_L(Grave)', capitalize=True),
          action(text=' ', attach=True)
         ]),
         
         (('{-|} equip {^s}', action(), False),
          [action(capitalize=True),
           action(text=' Equip', word='Equip'),
           action(text='s', word='Equips'),
          ]),

        (('{-|} equip {^ed}', action(), False),
         [action(capitalize=True),
          action(text=' Equip', word='Equip'),
          action(text='ped', word='Equipped'),
         ]),

        (('{>} Equip', action(), False),
         [action(lower=True),
          action(text=' equip', word='equip')
         ]),

        (('{>} equip', action(), False),
         [action(lower=True),
          action(text=' equip', word='equip')
         ]),

        (('{<} equip', action(), False),
         [action(upper=True),
          action(text=' EQUIP', word='EQUIP', upper_carry=True)
         ]),

        (('{<} EQUIP', action(), False),
         [action(upper=True),
          action(text=' EQUIP', word='EQUIP', upper_carry=True)
         ]),

        (('{<} equip {^ed}', action(), True),
         [action(upper=True),
          action(text='EQUIP ', word='EQUIP', upper_carry=True),
          action(text='PED ', word='EQUIPPED', replace=' ', upper_carry=True)
         ]),

        (('equip {*-|}', action(), False),
         [action(text=' equip', word='equip'),
          action(text=' Equip', word='Equip', replace=' equip'),
         ]),

        (('equip {^ed} {*-|}', action(), False),
         [action(text=' equip', word='equip'),
          action(text='ped', word='equipped'),
          action(text='Equipped', word='Equipped', replace='equipped'),
         ]),

        (('Equip {*>}', action(), False),
         [action(text=' Equip', word='Equip'),
          action(text=' equip', word='equip', replace=' Equip'),
         ]),

        (('Equip {^ed} {*>}', action(), False),
         [action(text=' Equip', word='Equip'),
          action(text='ped', word='Equipped'),
          action(text='equipped', word='equipped', replace='Equipped'),
         ]),

        (('equip {*<}', action(), False),
         [action(text=' equip', word='equip'),
          action(text=' EQUIP', word='EQUIP', replace=' equip', upper_carry=True),
         ]),

        (('equip {^ed} {*<}', action(), False),
         [action(text=' equip', word='equip'),
          action(text='ped', word='equipped'),
          action(text='EQUIPPED', word='EQUIPPED', replace='equipped', upper_carry=True),
         ]),

        (('notanumber {*($c)}', action(), False),
         [action(text=' notanumber', word='notanumber'),
          action(text='', word='notanumber', replace=''),
         ]),

        (('0 {*($c)}', action(), False),
         [action(text=' 0', word='0'),
          action(text='$0', word='$0', replace='0'),
         ]),

        (('0.00 {*($c)}', action(), False),
         [action(text=' 0.00', word='0.00'),
          action(text='$0.00', word='$0.00', replace='0.00'),
         ]),

        (('1234 {*($c)}', action(), False),
         [action(text=' 1234', word='1234'),
          action(text='$1,234', word='$1,234', replace='1234'),
         ]),

        (('1234567 {*($c)}', action(), False),
         [action(text=' 1234567', word='1234567'),
          action(text='$1,234,567', word='$1,234,567', replace='1234567'),
         ]),

        (('1234.5 {*($c)}', action(), False),
         [action(text=' 1234.5', word='1234.5'),
          action(text='$1,234.50', word='$1,234.50', replace='1234.5'),
         ]),

        (('1234.56 {*($c)}', action(), False),
         [action(text=' 1234.56', word='1234.56'),
          action(text='$1,234.56', word='$1,234.56', replace='1234.56'),
         ]),

        (('1234.567 {*($c)}', action(), False),
         [action(text=' 1234.567', word='1234.567'),
          action(text='$1,234.57', word='$1,234.57', replace='1234.567'),
         ]),

        (('equip {^} {^ed}', action(), False),
         [action(text=' equip', word='equip'),
          action(word='equip', attach=True, orthography=False),
          action(text='ed', word='equiped'),
         ]),
         
         (('{prefix^} test {^ing}', action(), False),
         [action(text=' prefix', word='prefix', attach=True),
          action(text='test', word='test'),
          action(text='ing', word='testing'),
         ]),

        (('{two prefix^} test {^ing}', action(), False),
         [action(text=' two prefix', word='prefix', attach=True),
          action(text='test', word='test'),
          action(text='ing', word='testing'),
         ]),


        (('test', action(), True), 
         [action(text='test ', word='test')]),
        
        (('{^^}', action(), True), [action(attach=True, orthography=False)]),
         
        (('1-9', action(), True), 
         [action(word='1-9', text='1-9 ')]),
         
        (('32', action(), True), 
         [action(word='32', text='32 ', glue=True)]),
         
        (('', action(text='test ', word='test', attach=True), True),
         [action(word='test', attach=True)]),
         
        (('  ', action(text='test ', word='test', attach=True), True),
         [action(word='test', attach=True)]),
         
        (('{^} {.} hello {.} {#ALT_L(Grave)}{^ ^}', action(), True),
         [action(attach=True, orthography=False), 
          action(text='. ', capitalize=True), 
          action(text='Hello ', word='Hello'), 
          action(text='. ', capitalize=True, replace=' '), 
          action(combo='ALT_L(Grave)', capitalize=True),
          action(text=' ', attach=True)
         ]),
         
         (('{-|} equip {^s}', action(), True),
          [action(capitalize=True),
           action(text='Equip ', word='Equip'),
           action(text='s ', word='Equips', replace=' '),
          ]),

        (('{-|} equip {^ed}', action(), True),
         [action(capitalize=True),
          action(text='Equip ', word='Equip'),
          action(text='ped ', word='Equipped', replace=' '),
         ]),

        (('{>} Equip', action(), True),
         [action(lower=True),
          action(text='equip ', word='equip')
         ]),

        (('{>} equip', action(), True),
         [action(lower=True),
          action(text='equip ', word='equip')
         ]),

        (('{<} equip', action(), True),
         [action(upper=True),
          action(text='EQUIP ', word='EQUIP', upper_carry=True)
         ]),

        (('{<} EQUIP', action(), True),
         [action(upper=True),
          action(text='EQUIP ', word='EQUIP', upper_carry=True)
         ]),

        (('{<} equip {^ed}', action(), True),
         [action(upper=True),
          action(text='EQUIP ', word='EQUIP', upper_carry=True),
          action(text='PED ', word='EQUIPPED', replace=' ', upper_carry=True)
         ]),

        (('equip {*-|}', action(), True),
         [action(text='equip ', word='equip'),
          action(text='Equip ', word='Equip', replace='equip '),
         ]),

        (('equip {^ed} {*-|}', action(), True),
         [action(text='equip ', word='equip'),
          action(text='ped ', word='equipped', replace=' '),
          action(text='Equipped ', word='Equipped', replace='equipped '),
         ]),

        (('Equip {*>}', action(), True),
         [action(text='Equip ', word='Equip'),
          action(text='equip ', word='equip', replace='Equip '),
         ]),

        (('Equip {^ed} {*>}', action(), True),
         [action(text='Equip ', word='Equip'),
          action(text='ped ', word='Equipped', replace=' '),
          action(text='equipped ', word='equipped', replace='Equipped '),
         ]),

        (('equip {*<}', action(), True),
         [action(text='equip ', word='equip'),
          action(text='EQUIP ', word='EQUIP', replace='equip ', upper_carry=True),
         ]),

        (('equip {^ed} {*<}', action(), True),
         [action(text='equip ', word='equip'),
          action(text='ped ', word='equipped', replace=' '),
          action(text='EQUIPPED ', word='EQUIPPED', replace='equipped ', upper_carry=True),
         ]),

        (('notanumber {*($c)}', action(), True),
         [action(text='notanumber ', word='notanumber'),
          action(text='', word='notanumber', replace=''),
         ]),

        (('0 {*($c)}', action(), True),
         [action(text='0 ', word='0'),
          action(text='$0 ', word='$0', replace='0 '),
         ]),

        (('0.00 {*($c)}', action(), True),
         [action(text='0.00 ', word='0.00'),
          action(text='$0.00 ', word='$0.00', replace='0.00 '),
         ]),

        (('1234 {*($c)}', action(), True),
         [action(text='1234 ', word='1234'),
          action(text='$1,234 ', word='$1,234', replace='1234 '),
         ]),

        (('1234567 {*($c)}', action(), True),
         [action(text='1234567 ', word='1234567'),
          action(text='$1,234,567 ', word='$1,234,567', replace='1234567 '),
         ]),

        (('1234.5 {*($c)}', action(), True),
         [action(text='1234.5 ', word='1234.5'),
          action(text='$1,234.50 ', word='$1,234.50', replace='1234.5 '),
         ]),

        (('1234.56 {*($c)}', action(), True),
         [action(text='1234.56 ', word='1234.56'),
          action(text='$1,234.56 ', word='$1,234.56', replace='1234.56 '),
         ]),

        (('1234.567 {*($c)}', action(), True),
         [action(text='1234.567 ', word='1234.567'),
          action(text='$1,234.57 ', word='$1,234.57', replace='1234.567 '),
         ]),
         
        (('equip {^} {^ed}', action(), True),
         [action(text='equip ', word='equip'),
          action(word='equip', attach=True, orthography=False, replace=' '),
          action(text='ed ', word='equiped'),
         ]),
         
         (('{prefix^} test {^ing}', action(), True),
         [action(text='prefix', word='prefix', attach=True),
          action(text='test ', word='test'),
          action(text='ing ', word='testing', replace=' '),
         ]),

        (('{two prefix^} test {^ing}', action(), True),
         [action(text='two prefix', word='prefix', attach=True),
          action(text='test ', word='test'),
          action(text='ing ', word='testing', replace=' '),
         ]),
        ]
        self.check_arglist(formatting._translation_to_actions, cases)

    def test_raw_to_actions(self):
        cases = (

        (
         ('2-6', action(), False),
         [action(glue=True, text=' 26', word='26')]
        ),

        (
         ('2', action(), False),
         [action(glue=True, text=' 2', word='2')]
        ),

        (
         ('-8', action(), False),
         [action(glue=True, text=' 8', word='8')]
        ),


        (
         ('-68', action(), False),
         [action(glue=True, text=' 68', word='68')]
        ),

        (
         ('S-T', action(), False),
         [action(text=' S-T', word='S-T')]
        ),


        )
        self.check_arglist(formatting._raw_to_actions, cases)

    def test_atom_to_action_spaces_before(self):
        an_action = action()
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

        (('{<}', action(word='test')),
         action(upper=True, word='test')),

        (('{*-|}', action(word='test')),
         action(word='Test', text='Test', replace='test')),

        (('{*>}', action(word='test')),
         action(word='test', text='test', replace='test')),

        (('{*<}', action(word='test')),
         action(word='TEST', text='TEST', replace='test', upper_carry=True)),
          
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

        (('some text', action(word='test',
                              case=an_action.CASE_TITLE,
                              space_char='')),
            action(text='SomeText', word='text',
                   case=an_action.CASE_TITLE,
                   space_char='')),

        (('some text', action(word='test', # This is camel case
                              case=an_action.CASE_TITLE,
                              space_char='', lower=True)),
            action(text='someText', word='text',
                   case=an_action.CASE_TITLE,
                   space_char='')),

        (('some text', action(word='test', space_char='_')),
         action(text='_some_text', word='text', space_char='_')),

        (('some text', action(word='test', case=an_action.CASE_UPPER)),
         action(text=' SOME TEXT', word='text', case=an_action.CASE_UPPER)),

        (('sOme TexT', action(word='test', case=an_action.CASE_LOWER)),
         action(text=' some text', word='TexT', case=an_action.CASE_LOWER)),

        (('sOme TexT', action(word='test', case=an_action.CASE_TITLE)),
         action(text=' Some Text', word='TexT', case=an_action.CASE_TITLE)),

        (('{MODE:CAPS}', action(word='test')),
         action(word='test', case=an_action.CASE_UPPER)),

        (('{MODE:LOWER}', action(word='test')),
         action(word='test', case=an_action.CASE_LOWER)),

        ]

        self.check_arglist(formatting._atom_to_action_spaces_before, cases)

    def test_atom_to_action_spaces_after(self):
        an_action = action()
        cases = [
        (('{^ed}', action(word='test', text='test ')),
         action(text='ed ', replace=' ', word='tested')),

        (('{^ed}', action(word='carry', text='carry ')),
         action(text='ied ', replace='y ', word='carried')),

        (('{^er}', action(word='test', text='test ')),
         action(text='er ', replace=' ', word='tester')),

        (('{^er}', action(word='carry', text='carry ')),
         action(text='ier ', replace='y ', word='carrier')),

        (('{^ing}', action(word='test', text='test ')),
         action(text='ing ', replace=' ', word='testing')),

        (('{^ing}', action(word='begin', text='begin ')),
         action(text='ning ', replace=' ', word='beginning')),

        (('{^ing}', action(word='parade', text='parade ')),
         action(text='ing ', replace='e ', word='parading')),

        (('{^s}', action(word='test', text='test ')),
         action(text='s ', replace=' ', word='tests')),

        (('{,}', action(word='test', text='test ')), action(text=', ', replace=' ')),

        (('{:}', action(word='test', text='test ')), action(text=': ', replace=' ')),

        (('{;}', action(word='test', text='test ')), action(text='; ', replace=' ')),

        (('{.}', action(word='test', text='test ')),
         action(text='. ', replace=' ', capitalize=True)),

        (('{?}', action(word='test', text='test ')),
         action(text='? ', replace=' ', capitalize=True)),

        (('{!}', action(word='test', text='test ')),
         action(text='! ', replace=' ', capitalize=True)),

        (('{-|}', action(word='test', text='test ')),
         action(capitalize=True, word='test')),

        (('{>}', action(word='test', text='test ')),
         action(lower=True, word='test')),

        (('{<}', action(word='test', text='test ')),
         action(upper=True, word='test')),

        (('{*-|}', action(word='test', text='test ')),
         action(word='Test', text='Test ', replace='test ')),

        (('{*>}', action(word='test', text='test ')),
         action(word='test', text='test ', replace='test ')),

        (('{*<}', action(word='test', text='test ')),
         action(word='TEST', text='TEST ', replace='test ', upper_carry=True)),

        (('{PLOVER:test_command}', action(word='test', text='test ')),
         action(word='test', command='test_command')),

        (('{&glue_text}', action(word='test', text='test ')),
         action(text='glue_text ', word='glue_text', glue=True)),

        (('{&glue_text}', action(word='test', text='test ', glue=True)),
         action(text='glue_text ', word='testglue_text', replace=' ', glue=True)),

        (('{&glue_text}', action(word='test', text='test', attach=True)),
         action(text='glue_text ', word='testglue_text', glue=True)),

        (('{^attach_text}', action(word='test', text='test ')),
         action(text='attach_text ', word='testattach_text', replace=' ')),

        (('{^attach_text^}', action(word='test', text='test ')),
         action(text='attach_text', word='testattach_text', replace=' ', attach=True)),

        (('{attach_text^}', action(word='test', text='test ')),
         action(text='attach_text', word='attach_text', attach=True)),

        (('{#ALT_L(A)}', action(word='test', text='test ')),
         action(combo='ALT_L(A)', word='test')),

        (('text', action(word='test', text='test ')),
         action(text='text ', word='text')),

        (('text', action(word='test', text='test ', glue=True)),
         action(text='text ', word='text')),

        (('text2', action(word='test2', text='test2', attach=True)),
         action(text='text2 ', word='text2', replace='')),

        (('text', action(word='test', text='test ', capitalize=True)),
         action(text='Text ', word='Text')),

        (('some text', action(word='test', text='test ')),
         action(text='some text ', word='text')),

        (('some text', action(word='test',
                              case=an_action.CASE_TITLE,
                              space_char='')),
            action(text='SomeText', word='text',
                   case=an_action.CASE_TITLE,
                   space_char='')),

        (('some text', action(word='test', # This is camel case
                              case=an_action.CASE_TITLE,
                              space_char='', lower=True)),
            action(text='someText', word='text',
                   case=an_action.CASE_TITLE,
                   space_char='')),

        (('some text', action(word='test', space_char='_')),
         action(text='some_text_', word='text', space_char='_')),

        (('some text', action(word='test', case=an_action.CASE_UPPER)),
         action(text='SOME TEXT ', word='text', case=an_action.CASE_UPPER)),

        (('sOme TexT', action(word='test', case=an_action.CASE_LOWER)),
         action(text='some text ', word='TexT', case=an_action.CASE_LOWER)),

        (('sOme TexT', action(word='test', case=an_action.CASE_TITLE)),
         action(text='Some Text ', word='TexT', case=an_action.CASE_TITLE)),

        (('{MODE:CAPS}', action(word='test')),
         action(word='test', case=an_action.CASE_UPPER)),

        (('{MODE:LOWER}', action(word='test')),
         action(word='test', case=an_action.CASE_LOWER)),

        ]
        self.check_arglist(formatting._atom_to_action_spaces_after, cases)

    def test_change_mode(self):
        an_action = action()
        cases = [
            # Undefined
            (('', action()), (action())),
            (('ABCD', action()), (action())),
            # CAPS: Uppercase
            (('CAPS', action()), (action(case=an_action.CASE_UPPER))),
            # LOWER: Lowercase
            (('LOWER', action()), (action(case=an_action.CASE_LOWER))),
            # TITLE: Titlecase
            (('TITLE', action()), (action(case=an_action.CASE_TITLE))),
            # CAMEL: Titlecase without space
            (('CAMEL', action()), (
                action(case=an_action.CASE_TITLE, space_char='',
                       lower=True)
                )),
            # SNAKE: Underscore space
            (('SNAKE', action()), (action(space_char='_'))),
            # RESET_SPACE: Default space
            (('RESET_SPACE', action(space_char='ABCD')), (action())),
            # RESET_CASE: No case
            (('RESET_CASE', action(
                case=an_action.CASE_UPPER)), (action())),
            # SET_SPACE:xy: Set space to xy
            (('SET_SPACE:', action(space_char='test')),
                (action(space_char=''))),
            (('SET_SPACE:-', action(space_char='test')),
                (action(space_char='-'))),
            (('SET_SPACE:123 45', action(space_char='test')),
                (action(space_char='123 45'))),
            # RESET: No case, default space
        ]

        self.check_arglist(formatting._change_mode, cases)

    def test_apply_case(self):
        an_action = action()
        # case, text, begin
        test = ' some test '
        test2 = 'test Me'
        test3 = ' SOME TEST '
        cases = [
            # UNDEFINED
            ((test, '', False), (test)),
            ((test, 'TEST', False), (test)),
            # TITLE
            ((test, an_action.CASE_TITLE, False), (' Some Test ')),
            # TITLE will not affect appended output
            ((test, an_action.CASE_TITLE, True), (' some test ')),
            ((test2, an_action.CASE_TITLE, True), ('test Me')),
            # LOWER
            ((test, an_action.CASE_LOWER, False), (' some test ')),
            ((test3, an_action.CASE_LOWER, False), (' some test ')),
            ((test2, an_action.CASE_LOWER, True), ('test me')),
            # UPPER
            ((test.upper(), an_action.CASE_UPPER, False), (' SOME TEST ')),
            ((test3, an_action.CASE_UPPER, False), (' SOME TEST ')),
            ((test2, an_action.CASE_UPPER, True), ('TEST ME')),
        ]

        self.check_arglist(formatting._apply_case, cases)

    def test_apply_space_char(self):
        # (text, space_char)
        test = ' some text '
        test2 = "don't"
        cases = [
            ((test, '_'), ('_some_text_')),
            ((test, ''), ('sometext')),
            ((test2, '_'), (test2)),
            ((test2, ''), (test2)),
        ]
        self.check_arglist(formatting._apply_space_char, cases)

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
