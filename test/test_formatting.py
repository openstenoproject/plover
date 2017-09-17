# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for formatting.py."""

import inspect

import pytest

from plover import formatting

from .test_blackbox import CaptureOutput


def parametrize(argvalues):
    ids = list(map(str, range(1, len(argvalues)+1)))
    def decorator(fn):
        parameters = list(inspect.signature(fn).parameters.keys())
        if 'self' == parameters[0]:
            parameters.pop(0)
        argnames = ','.join(parameters)
        return pytest.mark.parametrize(argnames, argvalues, ids=ids)(fn)
    return decorator

def action(**kwargs):
    return formatting._Action(**kwargs)

class MockTranslation(object):
    def __init__(self, rtfcre=tuple(), english=None, formatting=None):
        self.rtfcre = rtfcre
        self.english = english
        self.formatting = formatting

    def __str__(self):
        return str(self.__dict__)

def translation(**kwargs):
    return MockTranslation(**kwargs)

spaces_before = False
spaces_after = True


STARTING_STROKE_TESTS = (

    (True, True, [], [translation(rtfcre=('S'), english='hello')], None,
     ([action(text='Hello', word='Hello')],),
     [('s', 'Hello')]),

    (False, False, [], [translation(rtfcre=('S'), english='hello')], None,
     ([action(text=' hello', word='hello')],),
     [('s', ' hello')]),

    (True, False, [], [translation(rtfcre=('S'), english='hello')], None,
     ([action(text=' Hello', word='Hello')],),
     [('s', ' Hello')]),

    (False, True, [], [translation(rtfcre=('S'), english='hello')], None,
     ([action(text='hello', word='hello')],),
     [('s', 'hello')]),

)

@parametrize(STARTING_STROKE_TESTS)
def test_starting_stroke(capitalized, attached, undo, do, prev,
                         expected_formats, expected_outputs):
    output = CaptureOutput()
    formatter = formatting.Formatter()
    formatter.set_output(output)
    formatter.start_capitalized = capitalized
    formatter.start_attached = attached
    formatter.format(undo, do, prev)
    for i, t in enumerate(do):
        assert t.formatting == expected_formats[i]
    assert output.instructions == expected_outputs


FORMATTER_TESTS = (

    ([translation(formatting=[action(text='hello')])], [], None,
     (),
     [('b', 5)]),

    ([],
     [translation(rtfcre=('S'), english='hello')],
     [translation(rtfcre=('T'), english='a', formatting=[action(text='f')])]
     ,
     ([action(text=' hello', word='hello')],),
     [('s', ' hello')]),

    ([], [translation(rtfcre=('S'), english='hello')], None,
     ([action(text=' hello', word='hello')],),
     [('s', ' hello')]),

    ([], [translation(rtfcre=('ST-T',))], None,
     ([action(text=' ST-T', word='ST-T')],),
     [('s', ' ST-T')]),

    ([],
     [translation(rtfcre=('ST-T',))],
     [translation(formatting=[action(text='hi')])],
     ([action(text=' ST-T', word='ST-T')],),
     [('s', ' ST-T')]),

    ([translation(formatting=[action(text=' test')])],
     [translation(english='rest')],
     [translation(formatting=[action(capitalize=True)])],
     ([action(text=' Rest', word='Rest')],),
     [('b', 4), ('s', 'Rest')]),

    ([translation(formatting=[action(text='dare'),
                              action(text='ing', replace='e')])],
     [translation(english='rest')],
     [translation(formatting=[action(capitalize=True)])],
     ([action(text=' Rest', word='Rest')],),
     [('b', 6), ('s', ' Rest')]),

    ([translation(formatting=[action(text=' drive')])],
     [translation(english='driving')],
     None,
     ([action(text=' driving', word='driving')],),
     [('b', 1), ('s', 'ing')]),

    ([translation(formatting=[action(text=' drive')])],
     [translation(english='{#c}driving')],
     None,
     ([action(combo='c'), action(text=' driving', word='driving')],),
     [('b', 6), ('c', 'c'), ('s', ' driving')]),

    ([translation(formatting=[action(text=' drive')])],
     [translation(english='{PLOVER:c}driving')],
     None,
     ([action(command='c'), action(text=' driving', word='driving')],),
     [('b', 6), ('e', 'c'), ('s', ' driving')]),

    ([],
     [translation(rtfcre=('1',))],
     None,
     ([action(text=' 1', word='1', glue=True)],),
     [('s', ' 1')]),

    ([],
     [translation(rtfcre=('1',))],
     [translation(formatting=[action(text='hi', word='hi')])],
     ([action(text=' 1', word='1', glue=True)],),
     [('s', ' 1')]),

    ([],
     [translation(rtfcre=('1',))],
     [translation(formatting=[action(text='hi', word='hi', glue=True)])],
     ([action(text='1', word='hi1', glue=True)],),
     [('s', '1')]),

    ([],
     [translation(rtfcre=('1-9',))],
     [translation(formatting=[action(text='hi', word='hi', glue=True)])],
     ([action(text='19', word='hi19', glue=True)],),
     [('s', '19')]),

    ([],
     [translation(rtfcre=('ST-PL',))],
     [translation(formatting=[action(text='hi', word='hi')])],
     ([action(text=' ST-PL', word='ST-PL')],),
     [('s', ' ST-PL')]),

    ([],
     [translation(rtfcre=('ST-PL',))],
     None,
     ([action(text=' ST-PL', word='ST-PL')],),
     [('s', ' ST-PL')]),

)

@parametrize(FORMATTER_TESTS)
def test_formatter(undo, do, prev, expected_formats, expected_outputs):
    output = CaptureOutput()
    # Add some initial blank text so
    # undoing with no previous state
    # does not assert.
    output.text = ' ' * 128
    formatter = formatting.Formatter()
    formatter.set_output(output)
    formatter.format(undo, do, prev)
    for i, t in enumerate(do):
        assert t.formatting == expected_formats[i]
    assert output.instructions == expected_outputs


def test_get_last_action():
    formatter = formatting.Formatter()
    assert formatter._get_last_action(None) == action()
    assert formatter._get_last_action([]) == action()
    actions = [action(text='hello'), action(text='world')]
    assert formatter._get_last_action(actions) == actions[-1]
    formatter.start_attached = True
    formatter.start_capitalized = True
    assert formatter._get_last_action(None) == action(capitalize=True, attach=True)


def test_action():
    assert action(word='test') != action(word='test', attach=True)
    assert action(text='test') == action(text='test')
    assert action(text='test', word='test').copy_state() == action(word='test')


TRANSLATION_TO_ACTIONS_TESTS = (

    ('test', action(), spaces_before,
     [action(text=' test', word='test')]),

    ('{^^}', action(), spaces_before,
     [action(attach=True, orthography=False)]),

    ('1-9', action(), spaces_before,
     [action(word='1-9', text=' 1-9')]),

    ('32', action(), spaces_before,
     [action(word='32', text=' 32', glue=True)]),

    ('', action(text=' test', word='test', attach=True), spaces_before,
     [action(word='test', attach=True)]),

    ('  ', action(text=' test', word='test', attach=True), spaces_before,
     [action(word='test', attach=True)]),

    ('{^} {.} hello {.} {#ALT_L(Grave)}{^ ^}', action(), spaces_before,
     [action(attach=True, orthography=False),
      action(text='.', capitalize=True),
      action(text=' Hello', word='Hello'),
      action(text='.', capitalize=True),
      action(combo='ALT_L(Grave)', capitalize=True),
      action(text=' ', attach=True)
     ]),

    ('{-|}{>}{&a}{>}{&b}', action(), spaces_before,
     [action(capitalize=True),
      action(lower=True),
      action(text=' a', word='a', glue=True),
      action(lower=True, word='a', text='', glue=True),
      action(text='b', word='ab', glue=True),
     ]),

    ('{-|}{>}{&a}{>}{&b}', action(), spaces_after,
     [action(capitalize=True),
      action(lower=True),
      action(text='a ', word='a', glue=True),
      action(lower=True, word='a', text=' ', replace=' ', glue=True),
      action(text='b ', replace=' ', word='ab', glue=True),
     ]),

    ('{-|} equip {^s}', action(), spaces_before,
     [action(capitalize=True),
      action(text=' Equip', word='Equip'),
      action(text='s', word='Equips'),
     ]),

    ('{-|} equip {^ed}', action(), spaces_before,
     [action(capitalize=True),
      action(text=' Equip', word='Equip'),
      action(text='ped', word='Equipped'),
     ]),

    ('{>} Equip', action(), spaces_before,
     [action(lower=True),
      action(text=' equip', word='equip')
     ]),

    ('{>} equip', action(), spaces_before,
     [action(lower=True),
      action(text=' equip', word='equip')
     ]),

    ('{<} equip', action(), spaces_before,
     [action(upper=True),
      action(text=' EQUIP', word='EQUIP', upper_carry=True)
     ]),

    ('{<} EQUIP', action(), spaces_before,
     [action(upper=True),
      action(text=' EQUIP', word='EQUIP', upper_carry=True)
     ]),

    ('{<} equip {^ed}', action(), spaces_after,
     [action(upper=True),
      action(text='EQUIP ', word='EQUIP', upper_carry=True),
      action(text='PED ', word='EQUIPPED', replace=' ', upper_carry=True)
     ]),

    ('equip {*-|}', action(), spaces_before,
     [action(text=' equip', word='equip'),
      action(text=' Equip', word='Equip', replace=' equip'),
     ]),

    ('equip {^ed} {*-|}', action(), spaces_before,
     [action(text=' equip', word='equip'),
      action(text='ped', word='equipped'),
      action(text='Equipped', word='Equipped', replace='equipped'),
     ]),

    ('Equip {*>}', action(), spaces_before,
     [action(text=' Equip', word='Equip'),
      action(text=' equip', word='equip', replace=' Equip'),
     ]),

    ('Equip {^ed} {*>}', action(), spaces_before,
     [action(text=' Equip', word='Equip'),
      action(text='ped', word='Equipped'),
      action(text='equipped', word='equipped', replace='Equipped'),
     ]),

    ('equip {*<}', action(), spaces_before,
     [action(text=' equip', word='equip'),
      action(text=' EQUIP', word='EQUIP', replace=' equip', upper_carry=True),
     ]),

    ('equip {^ed} {*<}', action(), spaces_before,
     [action(text=' equip', word='equip'),
      action(text='ped', word='equipped'),
      action(text='EQUIPPED', word='EQUIPPED', replace='equipped', upper_carry=True),
     ]),

    ('notanumber {*($c)}', action(), spaces_before,
     [action(text=' notanumber', word='notanumber'),
      action(text='', word='notanumber', replace=''),
     ]),

    ('0 {*($c)}', action(), spaces_before,
     [action(text=' 0', word='0'),
      action(text='$0', word='$0', replace='0'),
     ]),

    ('0.00 {*($c)}', action(), spaces_before,
     [action(text=' 0.00', word='0.00'),
      action(text='$0.00', word='$0.00', replace='0.00'),
     ]),

    ('1234 {*($c)}', action(), spaces_before,
     [action(text=' 1234', word='1234'),
      action(text='$1,234', word='$1,234', replace='1234'),
     ]),

    ('1234567 {*($c)}', action(), spaces_before,
     [action(text=' 1234567', word='1234567'),
      action(text='$1,234,567', word='$1,234,567', replace='1234567'),
     ]),

    ('1234.5 {*($c)}', action(), spaces_before,
     [action(text=' 1234.5', word='1234.5'),
      action(text='$1,234.50', word='$1,234.50', replace='1234.5'),
     ]),

    ('1234.56 {*($c)}', action(), spaces_before,
     [action(text=' 1234.56', word='1234.56'),
      action(text='$1,234.56', word='$1,234.56', replace='1234.56'),
     ]),

    ('1234.567 {*($c)}', action(), spaces_before,
     [action(text=' 1234.567', word='1234.567'),
      action(text='$1,234.57', word='$1,234.57', replace='1234.567'),
     ]),

    ('equip {^} {^ed}', action(), spaces_before,
     [action(text=' equip', word='equip'),
      action(word='equip', attach=True, orthography=False),
      action(text='ed', word='equiped'),
     ]),

     ('{prefix^} test {^ing}', action(), spaces_before,
      [action(text=' prefix', word='prefix', attach=True),
       action(text='test', word='test'),
       action(text='ing', word='testing'),
      ]),

    ('{two prefix^} test {^ing}', action(), spaces_before,
     [action(text=' two prefix', word='prefix', attach=True),
      action(text='test', word='test'),
      action(text='ing', word='testing'),
     ]),

    ('{-|}{^|~|^}', action(), spaces_before,
     [action(capitalize=True),
      action(word='|~|', text='|~|', attach=True),
     ]),

    ('{-|}{~|\'^}cause', action(), spaces_before,
     [action(capitalize=True),
      action(text=' \'', word='\'', attach=True, capitalize=True),
      action(text='Cause', word='Cause'),
     ]),

    ('{.}{~|\'^}cuz', action(), spaces_before,
     [action(text='.', word='', capitalize=True),
      action(text=' \'', word='\'', attach=True, capitalize=True),
      action(text='Cuz', word='Cuz'),
     ]),

    ('{.}{~|\'^}cause', action(), spaces_after,
     [action(text='. ', word='', capitalize=True),
      action(text='\'', word='\'', attach=True, capitalize=True),
      action(text='Cause ', word='Cause'),
     ]),

    ('{.}{^~|\"}heyyo', action(), spaces_before,
     [action(text='.', word='', capitalize=True),
      action(text='"', word='"', capitalize=True),
      action(text=' Heyyo', word='Heyyo'),
     ]),

    ('{.}{^~|\"}heyyo', action(), spaces_after,
     [action(text='. ', word='', capitalize=True),
      action(text='" ', word='"', capitalize=True, replace=' '),
      action(text='Heyyo ', word='Heyyo'),
     ]),

    ('test', action(), spaces_after,
     [action(text='test ', word='test')]),

    ('{^^}', action(), spaces_after,
     [action(attach=True, orthography=False)]),

    ('1-9', action(), spaces_after,
     [action(word='1-9', text='1-9 ')]),

    ('32', action(), spaces_after,
     [action(word='32', text='32 ', glue=True)]),

    ('', action(text='test ', word='test', attach=True), spaces_after,
     [action(word='test', attach=True)]),

    ('  ', action(text='test ', word='test', attach=True), spaces_after,
     [action(word='test', attach=True)]),

    ('{^} {.} hello {.} {#ALT_L(Grave)}{^ ^}', action(), spaces_after,
     [action(attach=True, orthography=False),
      action(text='. ', capitalize=True),
      action(text='Hello ', word='Hello'),
      action(text='. ', capitalize=True, replace=' '),
      action(combo='ALT_L(Grave)', capitalize=True),
      action(text=' ', attach=True)
     ]),

     ('{-|} equip {^s}', action(), spaces_after,
      [action(capitalize=True),
       action(text='Equip ', word='Equip'),
       action(text='s ', word='Equips', replace=' '),
      ]),

    ('{-|} equip {^ed}', action(), spaces_after,
     [action(capitalize=True),
      action(text='Equip ', word='Equip'),
      action(text='ped ', word='Equipped', replace=' '),
     ]),

    ('{>} Equip', action(), spaces_after,
     [action(lower=True),
      action(text='equip ', word='equip')
     ]),

    ('{>} equip', action(), spaces_after,
     [action(lower=True),
      action(text='equip ', word='equip')
     ]),

    ('{<} equip', action(), spaces_after,
     [action(upper=True),
      action(text='EQUIP ', word='EQUIP', upper_carry=True)
     ]),

    ('{<} EQUIP', action(), spaces_after,
     [action(upper=True),
      action(text='EQUIP ', word='EQUIP', upper_carry=True)
     ]),

    ('{<} equip {^ed}', action(), spaces_after,
     [action(upper=True),
      action(text='EQUIP ', word='EQUIP', upper_carry=True),
      action(text='PED ', word='EQUIPPED', replace=' ', upper_carry=True)
     ]),

    ('equip {*-|}', action(), spaces_after,
     [action(text='equip ', word='equip'),
      action(text='Equip ', word='Equip', replace='equip '),
     ]),

    ('equip {^ed} {*-|}', action(), spaces_after,
     [action(text='equip ', word='equip'),
      action(text='ped ', word='equipped', replace=' '),
      action(text='Equipped ', word='Equipped', replace='equipped '),
     ]),

    ('Equip {*>}', action(), spaces_after,
     [action(text='Equip ', word='Equip'),
      action(text='equip ', word='equip', replace='Equip '),
     ]),

    ('Equip {^ed} {*>}', action(), spaces_after,
     [action(text='Equip ', word='Equip'),
      action(text='ped ', word='Equipped', replace=' '),
      action(text='equipped ', word='equipped', replace='Equipped '),
     ]),

    ('equip {*<}', action(), spaces_after,
     [action(text='equip ', word='equip'),
      action(text='EQUIP ', word='EQUIP', replace='equip ', upper_carry=True),
     ]),

    ('equip {^ed} {*<}', action(), spaces_after,
     [action(text='equip ', word='equip'),
      action(text='ped ', word='equipped', replace=' '),
      action(text='EQUIPPED ', word='EQUIPPED', replace='equipped ', upper_carry=True),
     ]),

    ('{.}{^~|^}zshrc', action(), spaces_after,
     [action(text='. ', capitalize=True),
      action(attach=True, capitalize=True, replace=' '),
      action(text='Zshrc ', word='Zshrc')]),

    ('notanumber {*($c)}', action(), spaces_after,
     [action(text='notanumber ', word='notanumber'),
      action(text='', word='notanumber', replace=''),
     ]),

    ('0 {*($c)}', action(), spaces_after,
     [action(text='0 ', word='0'),
      action(text='$0 ', word='$0', replace='0 '),
     ]),

    ('0.00 {*($c)}', action(), spaces_after,
     [action(text='0.00 ', word='0.00'),
      action(text='$0.00 ', word='$0.00', replace='0.00 '),
     ]),

    ('1234 {*($c)}', action(), spaces_after,
     [action(text='1234 ', word='1234'),
      action(text='$1,234 ', word='$1,234', replace='1234 '),
     ]),

    ('1234567 {*($c)}', action(), spaces_after,
     [action(text='1234567 ', word='1234567'),
      action(text='$1,234,567 ', word='$1,234,567', replace='1234567 '),
     ]),

    ('1234.5 {*($c)}', action(), spaces_after,
     [action(text='1234.5 ', word='1234.5'),
      action(text='$1,234.50 ', word='$1,234.50', replace='1234.5 '),
     ]),

    ('1234.56 {*($c)}', action(), spaces_after,
     [action(text='1234.56 ', word='1234.56'),
      action(text='$1,234.56 ', word='$1,234.56', replace='1234.56 '),
     ]),

    ('1234.567 {*($c)}', action(), spaces_after,
     [action(text='1234.567 ', word='1234.567'),
      action(text='$1,234.57 ', word='$1,234.57', replace='1234.567 '),
     ]),

    ('equip {^} {^ed}', action(), spaces_after,
     [action(text='equip ', word='equip'),
      action(word='equip', attach=True, orthography=False, replace=' '),
      action(text='ed ', word='equiped'),
     ]),

     ('{prefix^} test {^ing}', action(), spaces_after,
      [action(text='prefix', word='prefix', attach=True),
       action(text='test ', word='test'),
       action(text='ing ', word='testing', replace=' '),
      ]),

    ('{two prefix^} test {^ing}', action(), spaces_after,
     [action(text='two prefix', word='prefix', attach=True),
      action(text='test ', word='test'),
      action(text='ing ', word='testing', replace=' '),
     ]),
)

@parametrize(TRANSLATION_TO_ACTIONS_TESTS)
def test_translation_to_actions(translation, last_action, spaces_after, expected):
    assert formatting._translation_to_actions(translation, last_action, spaces_after) == expected


RAW_TO_ACTIONS_TESTS = (

    ('2-6', action(), spaces_before,
     [action(glue=True, text=' 26', word='26')]),

    ('2', action(), spaces_before,
     [action(glue=True, text=' 2', word='2')]),

    ('-8', action(), spaces_before,
     [action(glue=True, text=' 8', word='8')]),

    ('-68', action(), spaces_before,
     [action(glue=True, text=' 68', word='68')]),

    ('S-T', action(), spaces_before,
     [action(text=' S-T', word='S-T')]),

)

@parametrize(RAW_TO_ACTIONS_TESTS)
def test_raw_to_actions(stroke, last_action, spaces_after, expected):
    assert formatting._raw_to_actions(stroke, last_action, spaces_after) == expected


ATOM_TO_ACTION_TESTS = (

    ('{^ed}', action(word='test'), spaces_before,
     action(text='ed', replace='', word='tested')),

    ('{^ed}', action(word='carry'), spaces_before,
     action(text='ied', replace='y', word='carried')),

    ('{^er}', action(word='test'), spaces_before,
     action(text='er', replace='', word='tester')),

    ('{^er}', action(word='carry'), spaces_before,
     action(text='ier', replace='y', word='carrier')),

    ('{^ing}', action(word='test'), spaces_before,
     action(text='ing', replace='', word='testing')),

    ('{^ing}', action(word='begin'), spaces_before,
     action(text='ning', replace='', word='beginning')),

    ('{^ing}', action(word='parade'), spaces_before,
     action(text='ing', replace='e', word='parading')),

    ('{^s}', action(word='test'), spaces_before,
     action(text='s', replace='', word='tests')),

    ('{,}', action(word='test'), spaces_before,
     action(text=',')),

    ('{:}', action(word='test'), spaces_before,
     action(text=':')),

    ('{;}', action(word='test'), spaces_before,
     action(text=';')),

    ('{.}', action(word='test'), spaces_before,
     action(text='.', capitalize=True)),

    ('{?}', action(word='test'), spaces_before,
     action(text='?', capitalize=True)),

    ('{!}', action(word='test'), spaces_before,
     action(text='!', capitalize=True)),

    ('{-|}', action(word='test'), spaces_before,
     action(capitalize=True, word='test')),

    ('{>}', action(word='test'), spaces_before,
     action(lower=True, word='test')),

    ('{<}', action(word='test'), spaces_before,
     action(upper=True, word='test')),

    ('{*-|}', action(word='test'), spaces_before,
     action(word='Test', text='Test', replace='test')),

    ('{*>}', action(word='test'), spaces_before,
     action(word='test', text='test', replace='test')),

    ('{*<}', action(word='test'), spaces_before,
     action(word='TEST', text='TEST', replace='test', upper_carry=True)),

    ('{PLOVER:test_command}', action(word='test'), spaces_before,
     action(word='test', command='test_command')),

    ('{&glue_text}', action(word='test'), spaces_before,
     action(text=' glue_text', word='glue_text', glue=True)),

    ('{&glue_text}', action(word='test', glue=True), spaces_before,
     action(text='glue_text', word='testglue_text', glue=True)),

    ('{&glue_text}', action(word='test', attach=True), spaces_before,
     action(text='glue_text', word='testglue_text', glue=True)),

    ('{^attach_text}', action(word='test'), spaces_before,
     action(text='attach_text', word='testattach_text')),

    ('{^attach_text^}', action(word='test'), spaces_before,
     action(text='attach_text', word='testattach_text', attach=True)),

    ('{attach_text^}', action(word='test'), spaces_before,
     action(text=' attach_text', word='attach_text', attach=True)),

    ('{#ALT_L(A)}', action(word='test'), spaces_before,
     action(combo='ALT_L(A)', word='test')),

    ('text', action(word='test'), spaces_before,
     action(text=' text', word='text')),

    ('text', action(word='test', glue=True), spaces_before,
     action(text=' text', word='text')),

    ('text', action(word='test', attach=True), spaces_before,
     action(text='text', word='text')),

    ('text', action(word='test', capitalize=True), spaces_before,
     action(text=' Text', word='Text')),

    ('some text', action(word='test'), spaces_before,
     action(text=' some text', word='text')),

    ('some text',
     action(word='test',
            case=action().CASE_TITLE,
            space_char=''),
     spaces_before,
     action(text='SomeText', word='text',
            case=action().CASE_TITLE,
            space_char='')),

    ('some text',
     action(word='test', # This is camel case
            case=action().CASE_TITLE,
            space_char='', lower=True),
     spaces_before,
     action(text='someText', word='text',
            case=action().CASE_TITLE,
            space_char='')),

    ('some text', action(word='test', space_char='_'), spaces_before,
     action(text='_some_text', word='text', space_char='_')),

    ('some text', action(word='test', case=action().CASE_UPPER), spaces_before,
     action(text=' SOME TEXT', word='text', case=action().CASE_UPPER)),

    ('sOme TexT', action(word='test', case=action().CASE_LOWER), spaces_before,
     action(text=' some text', word='TexT', case=action().CASE_LOWER)),

    ('sOme TexT', action(word='test', case=action().CASE_TITLE), spaces_before,
     action(text=' Some Text', word='TexT', case=action().CASE_TITLE)),

    ('{MODE:CAPS}', action(word='test'), spaces_before,
     action(word='test', case=action().CASE_UPPER)),

    ('{MODE:LOWER}', action(word='test'), spaces_before,
     action(word='test', case=action().CASE_LOWER)),

    ('{^ed}', action(word='test', text='test '), spaces_after,
     action(text='ed ', replace=' ', word='tested')),

    ('{^ed}', action(word='carry', text='carry '), spaces_after,
     action(text='ied ', replace='y ', word='carried')),

    ('{^er}', action(word='test', text='test '), spaces_after,
     action(text='er ', replace=' ', word='tester')),

    ('{^er}', action(word='carry', text='carry '), spaces_after,
     action(text='ier ', replace='y ', word='carrier')),

    ('{^ing}', action(word='test', text='test '), spaces_after,
     action(text='ing ', replace=' ', word='testing')),

    ('{^ing}', action(word='begin', text='begin '), spaces_after,
     action(text='ning ', replace=' ', word='beginning')),

    ('{^ing}', action(word='parade', text='parade '), spaces_after,
     action(text='ing ', replace='e ', word='parading')),

    ('{^s}', action(word='test', text='test '), spaces_after,
     action(text='s ', replace=' ', word='tests')),

    ('{,}', action(word='test', text='test '), spaces_after,
     action(text=', ', replace=' ')),

    ('{:}', action(word='test', text='test '), spaces_after,
     action(text=': ', replace=' ')),

    ('{;}', action(word='test', text='test '), spaces_after,
     action(text='; ', replace=' ')),

    ('{.}', action(word='test', text='test '), spaces_after,
     action(text='. ', replace=' ', capitalize=True)),

    ('{?}', action(word='test', text='test '), spaces_after,
     action(text='? ', replace=' ', capitalize=True)),

    ('{!}', action(word='test', text='test '), spaces_after,
     action(text='! ', replace=' ', capitalize=True)),

    ('{-|}', action(word='test', text='test '), spaces_after,
     action(capitalize=True, word='test', text=' ', replace=' ')),

    ('{>}', action(word='test', text='test '), spaces_after,
     action(lower=True, word='test', replace=' ', text=' ')),

    ('{<}', action(word='test', text='test '), spaces_after,
     action(upper=True, word='test')),

    ('{*-|}', action(word='test', text='test '), spaces_after,
     action(word='Test', text='Test ', replace='test ')),

    ('{*>}', action(word='test', text='test '), spaces_after,
     action(word='test', text='test ', replace='test ')),

    ('{*<}', action(word='test', text='test '), spaces_after,
     action(word='TEST', text='TEST ', replace='test ', upper_carry=True)),

    ('{PLOVER:test_command}', action(word='test', text='test '), spaces_after,
     action(word='test', command='test_command')),

    ('{&glue_text}', action(word='test', text='test '), spaces_after,
     action(text='glue_text ', word='glue_text', glue=True)),

    ('{&glue_text}', action(word='test', text='test ', glue=True), spaces_after,
     action(text='glue_text ', word='testglue_text', replace=' ', glue=True)),

    ('{&glue_text}', action(word='test', text='test', attach=True), spaces_after,
     action(text='glue_text ', word='testglue_text', glue=True)),

    ('{^attach_text}', action(word='test', text='test '), spaces_after,
     action(text='attach_text ', word='testattach_text', replace=' ')),

    ('{^attach_text^}', action(word='test', text='test '), spaces_after,
     action(text='attach_text', word='testattach_text', replace=' ', attach=True)),

    ('{attach_text^}', action(word='test', text='test '), spaces_after,
     action(text='attach_text', word='attach_text', attach=True)),

    ('{#ALT_L(A)}', action(word='test', text='test '), spaces_after,
     action(combo='ALT_L(A)', word='test')),

    ('text', action(word='test', text='test '), spaces_after,
     action(text='text ', word='text')),

    ('text', action(word='test', text='test ', glue=True), spaces_after,
     action(text='text ', word='text')),

    ('text2', action(word='test2', text='test2', attach=True), spaces_after,
     action(text='text2 ', word='text2', replace='')),

    ('text', action(word='test', text='test ', capitalize=True), spaces_after,
     action(text='Text ', word='Text')),

    ('some text', action(word='test', text='test '), spaces_after,
     action(text='some text ', word='text')),

    ('some text',
     action(word='test',
            case=action().CASE_TITLE,
            space_char=''),
     spaces_after,
     action(text='SomeText', word='text',
            case=action().CASE_TITLE,
            space_char='')),

    ('some text',
     action(word='test', # This is camel case
            case=action().CASE_TITLE,
            space_char='', lower=True),
     spaces_after,
     action(text='someText', word='text',
            case=action().CASE_TITLE,
            space_char='')),

    ('some text', action(word='test', space_char='_'), spaces_after,
     action(text='some_text_', word='text', space_char='_')),

    ('some text', action(word='test', case=action().CASE_UPPER), spaces_after,
     action(text='SOME TEXT ', word='text', case=action().CASE_UPPER)),

    ('sOme TexT', action(word='test', case=action().CASE_LOWER), spaces_after,
     action(text='some text ', word='TexT', case=action().CASE_LOWER)),

    ('sOme TexT', action(word='test', case=action().CASE_TITLE), spaces_after,
     action(text='Some Text ', word='TexT', case=action().CASE_TITLE)),

    ('{MODE:CAPS}', action(word='test'), spaces_after,
     action(word='test', case=action().CASE_UPPER)),

    ('{MODE:LOWER}', action(word='test'), spaces_after,
     action(word='test', case=action().CASE_LOWER)),

)

@parametrize(ATOM_TO_ACTION_TESTS)
def test_atom_to_action(atom, last_action, spaces_after, expected):
    assert formatting._atom_to_action(atom, last_action, spaces_after) == expected


CHANGE_MODE_TESTS = (
    # Undefined
    ('', action(),
     action()),
    ('ABCD', action(),
     action()),
    # CAPS: Uppercase
    ('CAPS', action(),
     action(case=action().CASE_UPPER)),
    # LOWER: Lowercase
    ('LOWER', action(),
     action(case=action().CASE_LOWER)),
    # TITLE: Titlecase
    ('TITLE', action(),
     action(case=action().CASE_TITLE)),
    # CAMEL: Titlecase without space
    ('CAMEL', action(),
     action(case=action().CASE_TITLE, space_char='', lower=True)),
    # SNAKE: Underscore space
    ('SNAKE', action(),
     action(space_char='_')),
    # RESET_SPACE: Default space
    ('RESET_SPACE', action(space_char='ABCD'),
     action()),
    # RESET_CASE: No case
    ('RESET_CASE', action(case=action().CASE_UPPER),
     action()),
    # SET_SPACE:xy: Set space to xy
    ('SET_SPACE:', action(space_char='test'),
     action(space_char='')),
    ('SET_SPACE:-', action(space_char='test'),
     action(space_char='-')),
    ('SET_SPACE:123 45', action(space_char='test'),
     action(space_char='123 45')),
    # RESET: No case, default space
)

@parametrize(CHANGE_MODE_TESTS)
def test_change_mode(command, action, expected_action):
    assert formatting._change_mode(command, action) == expected_action


last_action_normal = action()
last_action_capitalized = action(capitalize=True)
last_action_attached = action(attach=True)

META_CARRY_CAPITALIZE_TESTS = (

    # Test word handling and space handling, standard.
    ('~|*', last_action_normal, spaces_before,
     (action(word='*', text=' *'))),
    ('~|*', last_action_normal, spaces_after,
     (action(word='*', text='* '))),

    # With attach flags:
    ('~|*^', last_action_normal, spaces_before,
     (action(word='*', text=' *', attach=True))),
    ('~|*^', last_action_normal, spaces_after,
     (action(word='*', text='*', attach=True))),
    ('^~|*', last_action_normal, spaces_before,
     (action(word='*', text='*'))),
    ('^~|*', last_action_normal, spaces_after,
     (action(word='*', text='* '))),
    ('^~|*^', last_action_normal, spaces_before,
     (action(word='*', text='*', attach=True))),
    ('^~|*^', last_action_normal, spaces_after,
     (action(word='*', text='*', attach=True))),

    # Should 'do nothing'.
    ('~|', last_action_capitalized, spaces_before,
     (last_action_capitalized)),

    # Should lose 'attach' flag.
    ('~|', last_action_attached, spaces_before,
     (action())),

    # Verify capitalize carry.
    ('^~|^', last_action_capitalized, spaces_before,
     (action(capitalize=True, attach=True))),
    ('^~|aset^', last_action_capitalized, spaces_before,
     (action(capitalize=True, attach=True, word="aset", text="aset"))),
    ('~|aset', last_action_capitalized, spaces_before,
     (action(capitalize=True, word="aset", text=" aset"))),
    ('~|aset', last_action_capitalized, spaces_after,
     (action(capitalize=True, word="aset", text="aset "))),

    # Verify 'attach' flag overriding.
    ('~|aset', last_action_attached, spaces_after,
     (action(word="aset", text="aset "))),
    ('~|aset^', last_action_attached, spaces_after,
     (action(word="aset", text="aset", attach=True))),

)

@parametrize(META_CARRY_CAPITALIZE_TESTS)
def test_meta_carry_capitalize(meta, last_action, spaces_after, expected):
    assert formatting._apply_carry_capitalize(meta, last_action, spaces_after) == expected


class TestApplyCase(object):

    test = ' some test '
    test2 = 'test Me'
    test3 = ' SOME TEST '

    TESTS = (
        # UNDEFINED
        (test, '', False, test),
        (test, 'TEST', False, test),
        # TITLE
        (test, action().CASE_TITLE, False, ' Some Test '),
        # TITLE will not affect appended output
        (test, action().CASE_TITLE, True, ' some test '),
        (test2, action().CASE_TITLE, True, 'test Me'),
        # LOWER
        (test, action().CASE_LOWER, False, ' some test '),
        (test3, action().CASE_LOWER, False, ' some test '),
        (test2, action().CASE_LOWER, True, 'test me'),
        # UPPER
        (test.upper(), action().CASE_UPPER, False, ' SOME TEST '),
        (test3, action().CASE_UPPER, False, ' SOME TEST '),
        (test2, action().CASE_UPPER, True, 'TEST ME'),
    )

    @parametrize(TESTS)
    def test_apply_case(self, input_text, case, appended, expected):
        assert formatting._apply_case(input_text, case, appended) == expected


def TestApplySpaceChar(object):

    test = ' some text '
    test2 = "don't"

    TESTS = (
        (test, '_', '_some_text_'),
        (test, '', 'sometext'),
        (test2, '_', test2),
        (test2, '', test2),
    )

    @parametrize(TESTS)
    def test_apply_space_char(text, space_char, expected):
        assert formatting._apply_space_char(text, space_char) == expected


@parametrize([('', None), ('{abc}', 'abc'), ('abc', None)])
def test_get_meta(atom, meta):
    assert formatting._get_meta(atom) == meta


@parametrize([('abc', '{&abc}'), ('1', '{&1}')])
def test_apply_glue(s, expected):
    assert formatting._apply_glue(s) == expected


@parametrize([('', ''), ('abc', 'abc'), (r'\{', '{'),
              (r'\}', '}'), (r'\{abc\}}{', '{abc}}{')])
def test_unescape_atom(atom, text):
    assert formatting._unescape_atom(atom) == text


@parametrize([('', None), ('{PLOVER:command}', 'command')])
def test_get_engine_command(atom, command):
    assert formatting._get_engine_command(atom) == command


@parametrize([('', ''), ('abc', 'Abc'), ('ABC', 'ABC')])
def test_capitalize(s, expected):
    assert formatting._capitalize(s) == expected


@parametrize([('', ''), ('abc', 'abc'), ('a word', 'word'), ('word.', 'word.')])
def test_rightmost_word(s, expected):
    assert formatting._rightmost_word(s) == expected


REPLACE_TESTS = (

    # Check that 'replace' does not unconditionally erase
    # the previous character if it does not match.
    ([
        translation(english='{MODE:SET_SPACE:}'),
        translation(english='foobar'),
        translation(english='{^}{#Return}{^}{-|}'),

    ], [('s', 'foobar'), ('c', 'Return')]),

    # Check 'replace' correctly takes into account
    # the previous translation.
    ([
        translation(english='test '),
        translation(english='{^,}'),

    ], [('s', 'test '), ('b', 1), ('s', ', ')]),

    # While the previous translation must be taken into account,
    # any meta-command must not be fired again.
    ([
        translation(english='{#Return}'),
        translation(english='test'),

    ], [('c', 'Return'), ('s', 'test ')]),

)

@parametrize(REPLACE_TESTS)
def test_replace(translations, expected_instructions):
    output = CaptureOutput()
    formatter = formatting.Formatter()
    formatter.set_output(output)
    formatter.set_space_placement('After Output')
    prev = []
    for t in translations:
        formatter.format([], [t], prev)
        prev.append(t)
    assert output.instructions == expected_instructions


def test_undo_replace():
    # Undoing a replace....
    output = CaptureOutput()
    formatter = formatting.Formatter()
    formatter.set_output(output)
    formatter.set_space_placement('After Output')
    prev = [translation(english='test')]
    formatter.format([], prev, None)
    undo = translation(english='{^,}')
    formatter.format([], [undo], prev)
    # Undo.
    formatter.format([undo], [], prev)
    assert output.instructions == [
        ('s', 'test '), ('b', 1), ('s', ', '), ('b', 2), ('s', ' '),
    ]


OUTPUT_OPTIMISATION_TESTS = (

    # No change.
    ([
        translation(english='noop'),
    ], [
        translation(english='noop'),
    ], [('s', ' noop')]),

    # Append only.
    ([
        translation(english='test'),
    ], [
        translation(english='testing'),
    ], [('s', ' test'), ('s', 'ing')]),

    # Chained meta-commands.
    ([
        translation(english='{#a}'),
    ], [
        translation(english='{#a}{#b}'),
    ], [('c', 'a'), ('c', 'b')]),

)

@parametrize(OUTPUT_OPTIMISATION_TESTS)
def test_output_optimization(undo, do, expected_instructions):
    output = CaptureOutput()
    formatter = formatting.Formatter()
    formatter.set_output(output)
    formatter.format([], undo, None)
    formatter.format(undo, do, None)
    assert output.instructions == expected_instructions
