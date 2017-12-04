# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for formatting.py."""

import inspect

import pytest

from plover import formatting
from plover_build_utils.testing import CaptureOutput


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
    # Suport using something like `text_and_word='stuff'`
    # as a shortcut for `text='stuff', word='stuff'`.
    for k, v in list(kwargs.items()):
        if '_and_' in k:
            del kwargs[k]
            for k in k.split('_and_'):
                kwargs[k] = v
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


STARTING_STROKE_TESTS = (

    (True, True, [], [translation(rtfcre=('S'), english='hello')], None,
     ([action(prev_attach=True, text='Hello', trailing_space=' ', word='hello')],),
     [('s', 'Hello')]),

    (False, False, [], [translation(rtfcre=('S'), english='hello')], None,
     ([action(text_and_word='hello', trailing_space=' ')],),
     [('s', ' hello')]),

    (True, False, [], [translation(rtfcre=('S'), english='hello')], None,
     ([action(text='Hello', word='hello', trailing_space=' ')],),
     [('s', ' Hello')]),

    (False, True, [], [translation(rtfcre=('S'), english='hello')], None,
     ([action(text_and_word='hello', prev_attach=True, trailing_space=' ')],),
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

    ([translation(formatting=[action(text_and_word='hello', trailing_space=' ')])],
     [],
     None,
     (),
     [('b', 6)]),

    ([],
     [translation(rtfcre=('S'), english='hello')],
     [translation(rtfcre=('T'), english='a', formatting=[action(text_and_word='f', trailing_space=' ')])]
     ,
     ([action(text_and_word='hello', trailing_space=' ')],),
     [('s', ' hello')]),

    ([], [translation(rtfcre=('S'), english='hello')], None,
     ([action(text_and_word='hello', trailing_space=' ')],),
     [('s', ' hello')]),

    ([], [translation(rtfcre=('ST-T',))], None,
     ([action(text_and_word='ST-T', trailing_space=' ')],),
     [('s', ' ST-T')]),

    ([],
     [translation(rtfcre=('ST-T',))],
     [translation(formatting=[action(text_and_word='hi', trailing_space=' ')])],
     ([action(text_and_word='ST-T', trailing_space=' ')],),
     [('s', ' ST-T')]),

    ([translation(formatting=[action(text_and_word='test', trailing_space=' ')])],
     [translation(english='rest')],
     [translation(formatting=[action(next_case=formatting.CASE_CAP_FIRST_WORD, trailing_space=' ')])],
     ([action(text='Rest', word='rest', trailing_space=' ')],),
     [('b', 4), ('s', 'Rest')]),

    ([translation(formatting=[action(text_and_word='dare'),
                              action(prev_attach=True, text='ing', word='daring', prev_replace='e')])],
     [translation(english='rest')],
     [translation(formatting=[action(next_case=formatting.CASE_CAP_FIRST_WORD,
                                     trailing_space=' ')])],
     ([action(text='Rest', word='rest', trailing_space=' ')],),
     [('b', 6), ('s', 'Rest')]),

    ([translation(formatting=[action(text_and_word='drive', trailing_space=' ')])],
     [translation(english='driving')],
     None,
     ([action(text_and_word='driving', trailing_space=' ')],),
     [('b', 1), ('s', 'ing')]),

    ([translation(formatting=[action(text_and_word='drive', trailing_space=' ')])],
     [translation(english='{#c}driving')],
     None,
     ([action(combo='c'), action(text_and_word='driving', trailing_space=' ')],),
     [('b', 6), ('c', 'c'), ('s', ' driving')]),

    ([translation(formatting=[action(text_and_word='drive', trailing_space=' ')])],
     [translation(english='{PLOVER:c}driving')],
     None,
     ([action(command='c'), action(text_and_word='driving', trailing_space=' ')],),
     [('b', 6), ('e', 'c'), ('s', ' driving')]),

    ([],
     [translation(rtfcre=('1',))],
     None,
     ([action(text_and_word='1', trailing_space=' ', glue=True)],),
     [('s', ' 1')]),

    ([],
     [translation(rtfcre=('1',))],
     [translation(formatting=[action(text_and_word='hi', trailing_space=' ')])],
     ([action(text_and_word='1', trailing_space=' ', glue=True)],),
     [('s', ' 1')]),

    ([],
     [translation(rtfcre=('1',))],
     [translation(formatting=[action(text_and_word='hi', trailing_space=' ', glue=True)])],
     ([action(prev_attach=True, text='1', trailing_space=' ', word='hi1', glue=True)],),
     [('s', '1')]),

    ([],
     [translation(rtfcre=('1-9',))],
     [translation(formatting=[action(text_and_word='hi', trailing_space=' ', glue=True)])],
     ([action(prev_attach=True, text='19', trailing_space=' ', word='hi19', glue=True)],),
     [('s', '19')]),

    ([],
     [translation(rtfcre=('ST-PL',))],
     [translation(formatting=[action(text_and_word='hi', trailing_space=' ')])],
     ([action(text_and_word='ST-PL', trailing_space=' ')],),
     [('s', ' ST-PL')]),

    ([],
     [translation(rtfcre=('ST-PL',))],
     None,
     ([action(text_and_word='ST-PL', trailing_space=' ')],),
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


def test_action():
    assert action(word='test') != action(word='test', next_attach=True)
    assert action(text='test') == action(text='test')
    assert action(text='test', word='test').copy_state() == action(word='test')


TRANSLATION_TO_ACTIONS_TESTS = (

    ('test', action(),
     [action(text_and_word='test', trailing_space=' ')]),

    ('{^^}', action(),
     [action(prev_attach=True, text_and_word='', next_attach=True, orthography=False)]),

    ('1-9', action(),
     [action(text_and_word='1-9', trailing_space=' ')]),

    ('32', action(),
     [action(text_and_word='32', trailing_space=' ', glue=True)]),

    ('', action(text_and_word='test', next_attach=True),
     [action(prev_attach=True, word='test', next_attach=True)]),

    ('  ', action(text_and_word='test', next_attach=True),
     [action(prev_attach=True, word='test', next_attach=True)]),

    ('{^} {.} hello {.} {#ALT_L(Grave)}{^ ^}', action(),
     [action(prev_attach=True, text_and_word='', next_attach=True, orthography=False),
      action(prev_attach=True, text_and_word='.', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD),
      action(text='Hello', word='hello', trailing_space=' '),
      action(prev_attach=True, text_and_word='.', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD),
      action(word='.', trailing_space=' ', combo='ALT_L(Grave)', next_case=formatting.CASE_CAP_FIRST_WORD),
      action(prev_attach=True, text=' ', word='', next_attach=True)
     ]),

    ('{-|}{>}{&a}{>}{&b}', action(),
     [action(next_case=formatting.CASE_CAP_FIRST_WORD),
      action(next_case=formatting.CASE_LOWER_FIRST_CHAR),
      action(text_and_word='a', trailing_space=' ', glue=True),
      action(next_case=formatting.CASE_LOWER_FIRST_CHAR, word='a', trailing_space=' ', glue=True),
      action(prev_attach=True, text='b', word='ab', trailing_space=' ', glue=True),
     ]),

    ('{-|}{>}{&a}{>}{&b}', action(),
     [action(next_case=formatting.CASE_CAP_FIRST_WORD),
      action(next_case=formatting.CASE_LOWER_FIRST_CHAR),
      action(text_and_word='a', trailing_space=' ', glue=True),
      action(next_case=formatting.CASE_LOWER_FIRST_CHAR, word='a', trailing_space=' ', glue=True),
      action(prev_attach=True, text='b', word='ab', trailing_space=' ', glue=True),
     ]),

    ('{-|} equip {^s}', action(),
     [action(next_case=formatting.CASE_CAP_FIRST_WORD),
      action(text='Equip', word='equip', trailing_space=' '),
      action(prev_attach=True, text='s', trailing_space=' ', word='equips'),
     ]),

    ('{-|} equip {^ed}', action(),
     [action(next_case=formatting.CASE_CAP_FIRST_WORD),
      action(text='Equip', word='equip', trailing_space=' '),
      action(prev_attach=True, text='ped', trailing_space=' ', word='equipped'),
     ]),

    ('{>} Equip', action(),
     [action(next_case=formatting.CASE_LOWER_FIRST_CHAR),
      action(text='equip', word='Equip', trailing_space=' ')
     ]),

    ('{>} equip', action(),
     [action(next_case=formatting.CASE_LOWER_FIRST_CHAR),
      action(text_and_word='equip', trailing_space=' ')
     ]),

    ('{<} equip', action(),
     [action(next_case=formatting.CASE_UPPER_FIRST_WORD),
      action(text='EQUIP', word='equip', trailing_space=' ', upper_carry=True)
     ]),

    ('{<} EQUIP', action(),
     [action(next_case=formatting.CASE_UPPER_FIRST_WORD),
      action(text_and_word='EQUIP', trailing_space=' ', upper_carry=True)
     ]),

    ('{<} equip {^ed}', action(),
     [action(next_case=formatting.CASE_UPPER_FIRST_WORD),
      action(text='EQUIP', word='equip', trailing_space=' ', upper_carry=True),
      action(prev_attach=True, text='PED', trailing_space=' ', word='equipped', upper_carry=True)
     ]),

    ('equip {*-|}', action(),
     [action(text_and_word='equip', trailing_space=' '),
      action(prev_attach=True, text='Equip', trailing_space=' ', word_and_prev_replace='equip'),
     ]),

    ('equip {^ed} {*-|}', action(),
     [action(text_and_word='equip', trailing_space=' '),
      action(prev_attach=True, text='ped', trailing_space=' ', word='equipped'),
      action(prev_attach=True, text='Equipped', trailing_space=' ', word_and_prev_replace='equipped'),
     ]),

    ('Equip {*>}', action(),
     [action(text_and_word='Equip', trailing_space=' '),
      action(prev_attach=True, text='equip', trailing_space=' ', word_and_prev_replace='Equip'),
     ]),

    ('Equip {^ed} {*>}', action(),
     [action(text_and_word='Equip', trailing_space=' '),
      action(prev_attach=True, text='ped', trailing_space=' ', word='Equipped'),
      action(prev_attach=True, text='equipped', trailing_space=' ', word_and_prev_replace='Equipped'),
     ]),

    ('equip {*<}', action(),
     [action(text_and_word='equip', trailing_space=' '),
      action(prev_attach=True, text='EQUIP', trailing_space=' ', word_and_prev_replace='equip'),
     ]),

    ('equip {^ed} {*<}', action(),
     [action(text_and_word='equip', trailing_space=' '),
      action(prev_attach=True, text='ped', trailing_space=' ', word='equipped'),
      action(prev_attach=True, text='EQUIPPED', trailing_space=' ', word_and_prev_replace='equipped'),
     ]),

    ('notanumber {*($c)}', action(),
     [action(text_and_word='notanumber', trailing_space=' '),
      action(word='notanumber', trailing_space=' '),
     ]),

    ('0 {*($c)}', action(),
     [action(text_and_word='0', trailing_space=' '),
      action(prev_attach=True, text='$0', word='0', trailing_space=' ', prev_replace='0'),
     ]),

    ('0.00 {*($c)}', action(),
     [action(text_and_word='0.00', trailing_space=' '),
      action(prev_attach=True, text='$0.00', word='0.00', trailing_space=' ', prev_replace='0.00'),
     ]),

    ('1234 {*($c)}', action(),
     [action(text_and_word='1234', trailing_space=' '),
      action(prev_attach=True, text='$1,234', word='1,234', trailing_space=' ', prev_replace='1234'),
     ]),

    ('1234567 {*($c)}', action(),
     [action(text_and_word='1234567', trailing_space=' '),
      action(prev_attach=True, text='$1,234,567', word='1,234,567', trailing_space=' ', prev_replace='1234567'),
     ]),

    ('1234.5 {*($c)}', action(),
     [action(text_and_word='1234.5', trailing_space=' '),
      action(prev_attach=True, text='$1,234.50', word='1,234.50', trailing_space=' ', prev_replace='1234.5'),
     ]),

    ('1234.56 {*($c)}', action(),
     [action(text_and_word='1234.56', trailing_space=' '),
      action(prev_attach=True, text='$1,234.56', word='1,234.56', trailing_space=' ', prev_replace='1234.56'),
     ]),

    ('1234.567 {*($c)}', action(),
     [action(text_and_word='1234.567', trailing_space=' '),
      action(prev_attach=True, text='$1,234.57', word='1,234.57', trailing_space=' ', prev_replace='1234.567'),
     ]),

    ('equip {^} {^ed}', action(),
     [action(text_and_word='equip', trailing_space=' '),
      action(prev_attach=True, text='', word='equip', next_attach=True, orthography=False),
      action(prev_attach=True, text='ed', trailing_space=' ', word='equiped'),
     ]),

     ('{prefix^} test {^ing}', action(),
      [action(text_and_word='prefix', next_attach=True),
       action(prev_attach=True, text_and_word='test', trailing_space=' '),
       action(prev_attach=True, text='ing', trailing_space=' ', word='testing'),
      ]),

    ('{two prefix^} test {^ing}', action(),
     [action(text='two prefix', word='prefix', next_attach=True),
      action(prev_attach=True, text_and_word='test', trailing_space=' '),
      action(prev_attach=True, text='ing', trailing_space=' ', word='testing'),
     ]),

    ('{-|}{^|~|^}', action(),
     [action(next_case=formatting.CASE_CAP_FIRST_WORD),
      action(prev_attach=True, text_and_word='|~|', next_attach=True),
     ]),

    ('{-|}{~|\'^}cause', action(),
     [action(next_case=formatting.CASE_CAP_FIRST_WORD),
      action(text_and_word='\'', next_attach=True, next_case=formatting.CASE_CAP_FIRST_WORD),
      action(prev_attach=True, text='Cause', trailing_space=' ', word='cause'),
     ]),

    ('{.}{~|\'^}cuz', action(),
     [action(prev_attach=True, text_and_word='.', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD),
      action(text_and_word='\'', next_attach=True, next_case=formatting.CASE_CAP_FIRST_WORD),
      action(prev_attach=True, text='Cuz', trailing_space=' ', word='cuz'),
     ]),

    ('{.}{~|\'^}cause', action(),
     [action(prev_attach=True, text_and_word='.', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD),
      action(text_and_word='\'', next_attach=True, next_case=formatting.CASE_CAP_FIRST_WORD),
      action(prev_attach=True, text='Cause', trailing_space=' ', word='cause'),
     ]),

    ('{.}{^~|\"}heyyo', action(),
     [action(prev_attach=True, text_and_word='.', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD),
      action(prev_attach=True, text_and_word='"', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD),
      action(text='Heyyo', trailing_space=' ', word='heyyo'),
     ]),

    ('{.}{^~|^}zshrc', action(),
     [action(prev_attach=True, text_and_word='.', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD),
      action(prev_attach=True, text_and_word='', next_attach=True, next_case=formatting.CASE_CAP_FIRST_WORD),
      action(prev_attach=True, text='Zshrc', trailing_space=' ', word='zshrc')]),

    ('{.}', action(),
     [action(prev_attach=True, text_and_word='.', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD)]
    ),

    ('{,}', action(),
     [action(prev_attach=True, text_and_word=',', trailing_space=' ')]
    ),

    ('test{prefix^}', action(),
     [action(text_and_word='test', trailing_space=' '),
      action(text_and_word='prefix', next_attach=True),
     ]),

    ('{prefix^}{prefix^}', action(),
     [action(text_and_word='prefix', next_attach=True),
      action(prev_attach=True, text='prefix', word='prefixprefix', next_attach=True),
     ]),

    ('{prefix^}{^ing}', action(),
     [action(text_and_word='prefix', next_attach=True),
      action(prev_attach=True, text='ing', trailing_space=' ', word='prefixing'),
     ]),

    ('{prefix^}cancel{^ing}', action(),
     [action(text_and_word='prefix', next_attach=True),
      action(prev_attach=True, text='cancel', trailing_space=' ', word='cancel'),
      action(prev_attach=True, text='ing', trailing_space=' ', word='canceling'),
     ]),

)

@parametrize(TRANSLATION_TO_ACTIONS_TESTS)
def test_translation_to_actions(translation, last_action, expected):
    ctx = formatting._Context([], action())
    ctx.translated(last_action)
    assert formatting._translation_to_actions(translation, ctx) == expected


RAW_TO_ACTIONS_TESTS = (

    ('2-6', action(),
     [action(glue=True, text_and_word='26', trailing_space=' ')]),

    ('2', action(),
     [action(glue=True, text_and_word='2', trailing_space=' ')]),

    ('-8', action(),
     [action(glue=True, text_and_word='8', trailing_space=' ')]),

    ('-68', action(),
     [action(glue=True, text_and_word='68', trailing_space=' ')]),

    ('S-T', action(),
     [action(text_and_word='S-T', trailing_space=' ')]),

)

@parametrize(RAW_TO_ACTIONS_TESTS)
def test_raw_to_actions(stroke, last_action, expected):
    ctx = formatting._Context([], action())
    ctx.translated(last_action)
    assert formatting._raw_to_actions(stroke, ctx) == expected


ATOM_TO_ACTION_TESTS = (

    ('{^ed}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text='ed', trailing_space=' ', word='tested')),

    ('{^ed}', action(text_and_word='carry', trailing_space=' '),
     action(prev_attach=True, text='ied', trailing_space=' ', prev_replace='y', word='carried')),

    ('{^er}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text='er', trailing_space=' ', word='tester')),

    ('{^er}', action(text_and_word='carry', trailing_space=' '),
     action(prev_attach=True, text='ier', trailing_space=' ', prev_replace='y', word='carrier')),

    ('{^ing}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text='ing', trailing_space=' ', word='testing')),

    ('{^ing}', action(text_and_word='begin', trailing_space=' '),
     action(prev_attach=True, text='ning', trailing_space=' ', word='beginning')),

    ('{^ing}', action(text_and_word='parade', trailing_space=' '),
     action(prev_attach=True, text='ing', trailing_space=' ', prev_replace='e', word='parading')),

    ('{^s}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text='s', trailing_space=' ', word='tests')),

    ('{,}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text_and_word=',', trailing_space=' ')),

    ('{:}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text_and_word=':', trailing_space=' ')),

    ('{;}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text_and_word=';', trailing_space=' ')),

    ('{.}', action(prev_attach=True, word='test', trailing_space=' '),
     action(prev_attach=True, text_and_word='.', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD)),

    ('{?}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text_and_word='?', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD)),

    ('{!}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text_and_word='!', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD)),

    ('{-|}', action(text_and_word='test', trailing_space=' '),
     action(next_case=formatting.CASE_CAP_FIRST_WORD, word='test', trailing_space=' ')),

    ('{>}', action(text_and_word='test', trailing_space=' '),
     action(next_case=formatting.CASE_LOWER_FIRST_CHAR, word='test', trailing_space=' ')),

    ('{<}', action(text_and_word='test', trailing_space=' '),
     action(next_case=formatting.CASE_UPPER_FIRST_WORD, word='test', trailing_space=' ')),

    ('{*-|}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text='Test', trailing_space=' ', word_and_prev_replace='test')),

    ('{*>}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text_and_word_and_prev_replace='test',
            trailing_space=' ')),

    ('{*<}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text='TEST', word_and_prev_replace='test', trailing_space=' ')),

    ('{PLOVER:test_command}', action(text_and_word='test', trailing_space=' '),
     action(word='test', command='test_command', trailing_space=' ')),

    ('{&glue_text}', action(text_and_word='test', trailing_space=' '),
     action(text_and_word='glue_text', trailing_space=' ', glue=True)),

    ('{&glue_text}', action(text_and_word='test', trailing_space=' ', glue=True),
     action(prev_attach=True, text='glue_text', trailing_space=' ', word='testglue_text', glue=True)),

    ('{&glue_text}', action(text_and_word='test', next_attach=True),
     action(prev_attach=True, text='glue_text', trailing_space=' ', word='glue_text', glue=True)),

    ('{^attach_text}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text='attach_text', trailing_space=' ', word='testattach_text')),

    ('{^attach_text^}', action(text_and_word='test', trailing_space=' '),
     action(prev_attach=True, text='attach_text', word='testattach_text', next_attach=True)),

    ('{attach_text^}', action(text_and_word='test', trailing_space=' '),
     action(text_and_word='attach_text', next_attach=True)),

    ('{#ALT_L(A)}', action(text_and_word='test', trailing_space=' '),
     action(combo='ALT_L(A)', trailing_space=' ', word='test')),

    ('text', action(text_and_word='test', trailing_space=' '),
     action(text_and_word='text', trailing_space=' ')),

    ('text', action(text_and_word='test', trailing_space=' ', glue=True),
     action(text_and_word='text', trailing_space=' ')),

    ('text', action(text_and_word='test', next_attach=True),
     action(prev_attach=True, text_and_word='text', trailing_space=' ')),

    ('text', action(text_and_word='test', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD),
     action(text='Text', trailing_space=' ', word='text')),

    ('some text', action(text_and_word='test', trailing_space=' '),
     action(text='some text', trailing_space=' ', word='text')),

    ('some text',
     action(text_and_word='test', trailing_space=' ',
            case=formatting.CASE_TITLE,
            space_char=''),
     action(text='SomeText', word='text',
            case=formatting.CASE_TITLE,
            space_char='')),

    ('some text',
     action(text_and_word='test', trailing_space=' ', # This is camel case
            case=formatting.CASE_TITLE,
            space_char='', next_case=formatting.CASE_LOWER_FIRST_CHAR),
     action(text='someText', word='text',
            case=formatting.CASE_TITLE,
            space_char='')),

    ('some text', action(text_and_word='test', trailing_space=' ', space_char='_'),
     action(text='some_text', trailing_space='_', word='text', space_char='_')),

    ('some text', action(text_and_word='test', trailing_space=' ', case=formatting.CASE_UPPER),
     action(text='SOME TEXT', trailing_space=' ', word='text', case=formatting.CASE_UPPER)),

    ('sOme TexT', action(text_and_word='test', trailing_space=' ', case=formatting.CASE_LOWER),
     action(text='some text', trailing_space=' ', word='TexT', case=formatting.CASE_LOWER)),

    ('sOme TexT', action(text_and_word='test', trailing_space=' ', case=formatting.CASE_TITLE),
     action(text='Some Text', trailing_space=' ', word='TexT', case=formatting.CASE_TITLE)),

    ('{MODE:CAPS}', action(text_and_word='test', trailing_space=' '),
     action(word='test', trailing_space=' ', case=formatting.CASE_UPPER)),

    ('{MODE:LOWER}', action(text_and_word='test', trailing_space=' '),
     action(word='test', trailing_space=' ', case=formatting.CASE_LOWER)),

)

@parametrize(ATOM_TO_ACTION_TESTS)
def test_atom_to_action(atom, last_action, expected):
    ctx = formatting._Context((), last_action)
    ctx.translated(last_action)
    assert formatting._atom_to_action(atom, ctx) == expected


CHANGE_MODE_TESTS = (
    # Undefined
    ('', action(),
     action()),
    ('ABCD', action(),
     action()),
    # CAPS: Uppercase
    ('CAPS', action(),
     action(case=formatting.CASE_UPPER)),
    # LOWER: Lowercase
    ('LOWER', action(),
     action(case=formatting.CASE_LOWER)),
    # TITLE: Titlecase
    ('TITLE', action(),
     action(case=formatting.CASE_TITLE)),
    # CAMEL: Titlecase without space
    ('CAMEL', action(),
     action(case=formatting.CASE_TITLE, space_char='',
            next_case=formatting.CASE_LOWER_FIRST_CHAR)),
    # SNAKE: Underscore space
    ('SNAKE', action(),
     action(space_char='_')),
    # RESET_SPACE: Default space
    ('RESET_SPACE', action(space_char='ABCD'),
     action()),
    # RESET_CASE: No case
    ('RESET_CASE', action(case=formatting.CASE_UPPER),
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
def test_meta_mode(meta, last_action, expected):
    ctx = formatting._Context((), action())
    ctx.translated(last_action)
    assert formatting._atom_to_action('{MODE:' + meta + '}', ctx) == expected


last_action_normal = action()
last_action_capitalized = action(next_case=formatting.CASE_CAP_FIRST_WORD)
last_action_attached = action(next_attach=True)

META_CARRY_CAPITALIZE_TESTS = (

    # Test word handling and space handling, standard.
    ('~|*', last_action_normal,
     (action(word='*', text='*', trailing_space=' '))),

    # With attach flags:
    ('~|*^', last_action_normal,
     (action(word='*', text='*', next_attach=True))),
    ('^~|*', last_action_normal,
     (action(word='*', text='*', trailing_space=' ', prev_attach=True))),
    ('^~|*^', last_action_normal,
     (action(word='*', text='*', prev_attach=True, next_attach=True))),

    # Should 'do nothing'.
    ('~|', last_action_capitalized,
     (last_action_capitalized)),

    # Should lose 'next_attach' flag.
    ('~|', last_action_attached,
     (action(prev_attach=True))),

    # Verify capitalize carry.
    ('^~|^', last_action_capitalized,
     (action(next_case=formatting.CASE_CAP_FIRST_WORD, text_and_word='', prev_attach=True, next_attach=True))),
    ('^~|aset^', last_action_capitalized,
     (action(next_case=formatting.CASE_CAP_FIRST_WORD, prev_attach=True, next_attach=True, text='Aset', word='aset'))),
    ('~|aset', last_action_capitalized,
     (action(next_case=formatting.CASE_CAP_FIRST_WORD, text='Aset', trailing_space=' ', word='aset'))),

    # Verify 'next_attach' flag overriding.
    ('~|aset', last_action_attached,
     (action(prev_attach=True, text_and_word='aset', trailing_space=' '))),
    ('~|aset^', last_action_attached,
     (action(prev_attach=True, text_and_word='aset', next_attach=True))),

)

@parametrize(META_CARRY_CAPITALIZE_TESTS)
def test_meta_carry_capitalize(meta, last_action, expected):
    ctx = formatting._Context((), action())
    ctx.translated(last_action)
    assert formatting._atom_to_action('{' + meta + '}', ctx) == expected


class TestApplyModeCase(object):

    test = ' some test '
    test2 = 'test Me'
    test3 = ' SOME TEST '

    TESTS = (
        # INVALID
        (test, '', False, ValueError),
        (test, 'TEST', False, ValueError),
        # NO-OP
        (test, None, False, test),
        (test, None, True, test),
        # TITLE
        (test, formatting.CASE_TITLE, False, ' Some Test '),
        # TITLE will not affect appended output
        (test, formatting.CASE_TITLE, True, ' some test '),
        (test2, formatting.CASE_TITLE, True, 'test Me'),
        # LOWER
        (test, formatting.CASE_LOWER, False, ' some test '),
        (test3, formatting.CASE_LOWER, False, ' some test '),
        (test2, formatting.CASE_LOWER, True, 'test me'),
        # UPPER
        (test.upper(), formatting.CASE_UPPER, False, ' SOME TEST '),
        (test3, formatting.CASE_UPPER, False, ' SOME TEST '),
        (test2, formatting.CASE_UPPER, True, 'TEST ME'),
    )

    @parametrize(TESTS)
    def test_apply_case(self, input_text, case, appended, expected):
        if inspect.isclass(expected):
            with pytest.raises(expected):
                formatting._apply_mode_case(input_text, case, appended)
        else:
            assert formatting._apply_mode_case(input_text, case, appended) == expected


def TestApplyModeSpaceChar(object):

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
        assert formatting._apply_mode_space_char(text, space_char) == expected


@parametrize([('', None), ('{abc}', 'abc'), ('abc', None)])
def test_get_meta(atom, meta):
    assert formatting._get_meta(atom) == meta


@parametrize([('abc', '{&abc}'), ('1', '{&1}')])
def test_glue_translation(s, expected):
    assert formatting._glue_translation(s) == expected


@parametrize([('', ''), ('abc', 'abc'), (r'\{', '{'),
              (r'\}', '}'), (r'\{abc\}}{', '{abc}}{')])
def test_unescape_atom(atom, text):
    assert formatting._unescape_atom(atom) == text


@parametrize([('', ''), ('abc', 'Abc'), ('ABC', 'ABC')])
def test_capitalize_first_word(s, expected):
    assert formatting._capitalize_first_word(s) == expected


RIGHTMOST_WORD_TESTS = (
    ('', ''),
    ('\n', ''),
    ('\t', ''),
    ('abc', 'abc'),
    ('a word', 'word'),
    ('word.', '.'),
    ('word ', ''),
    ('word\n', ''),
    ('word\t', ''),
    (' word', 'word'),
    ('\nword', 'word'),
    ('\tword', 'word'),
)

@parametrize(RIGHTMOST_WORD_TESTS)
def test_rightmost_word(s, expected):
    assert formatting._rightmost_word(s) == expected


REPLACE_TESTS = (

    # Check that 'prev_replace' does not unconditionally erase
    # the previous character if it does not match.
    ([
        translation(english='{MODE:SET_SPACE:}'),
        translation(english='foobar'),
        translation(english='{^}{#Return}{^}{-|}'),

    ], [('s', 'foobar'), ('c', 'Return')]),

    # Check 'prev_replace' correctly takes into account
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


class TestRetroFormatter(object):

    def setup_method(self):
        self.formatter = formatting.Formatter()
        self.translations = []
        self.retro_formatter = formatting.RetroFormatter(self.translations)

    def format(self, text):
        t = translation(english=text)
        self.formatter.format([], [t], self.translations)
        self.translations.append(t)
        return t

    ITER_LAST_ACTIONS_TESTS = (

        (['Luca', 'mela'],
         [action(text_and_word='mela', trailing_space=' '),
          action(text_and_word='Luca', trailing_space=' ')]),

        (['{Luca^}', '{^mela}'],
         [action(prev_attach=True, text='mela', trailing_space=' ', word='Lucamela'),
          action(text_and_word='Luca', next_attach=True)]),

        (['Luca', '{^ ^}', 'mela'],
         [action(text_and_word='mela', trailing_space=' ', prev_attach=True),
          action(text=' ', word='', prev_attach=True, next_attach=True),
          action(text_and_word='Luca', trailing_space=' ')]),

        (['Luca', '{-|}', 'mela'],
         [action(text='Mela', trailing_space=' ', word='mela'),
          action(word='Luca', trailing_space=' ', next_case=formatting.CASE_CAP_FIRST_WORD),
          action(text_and_word='Luca', trailing_space=' ')]),

    )

    @parametrize(ITER_LAST_ACTIONS_TESTS)
    def test_iter_last_actions(self, translation_list, action_list):
        for t in translation_list:
            self.format(t)
        assert list(self.retro_formatter.iter_last_actions()) == action_list

    ITER_LAST_FRAGMENTS_TESTS = (

        (False,
         ['Luca', 'mela'],
         ['mela', 'Luca ']),

        (False,
         ['Luca{^ ^}mela'],
         ['mela', 'Luca ']),

        (False,
         ['Luca, mela.'],
         ['mela.', 'Luca, ']),

        (False,
         ['Luca{-|}mela'],
         ['Mela', 'Luca ']),

        (True,
         ['Luca{-|}mela'],
         ['Mela', 'Luca ']),

    )

    @parametrize(ITER_LAST_FRAGMENTS_TESTS)
    def test_iter_last_fragments(self, spaces_after, translation_list, fragment_list):
        if spaces_after:
            self.formatter.set_space_placement('After Output')
        for t in translation_list:
            self.format(t)
        assert list(self.retro_formatter.iter_last_fragments()) == fragment_list

    ITER_LAST_WORDS_TESTS = (

        (False,
         ['Luca', 'mela'],
         ['mela', 'Luca ']),

        (False,
         ['Luca{^ ^}mela'],
         ['mela', 'Luca ']),

        (False,
         ['Luca, mela.'],
         ['.', 'mela', ', ', 'Luca']),

        (False,
         ['Luca{-|}mela'],
         ['Mela', 'Luca ']),

        (True,
         ['Luca{-|}mela'],
         ['Mela', 'Luca ']),
    )

    @parametrize(ITER_LAST_WORDS_TESTS)
    def test_iter_last_words(self, spaces_after, translation_list, word_list):
        if spaces_after:
            self.formatter.set_space_placement('After Output')
        for t in translation_list:
            self.format(t)
        assert list(self.retro_formatter.iter_last_words()) == word_list

    LAST_TEXT_TESTS = (

        (False,
         ['Luca{-|}mela'],
         3,
         'ela'),

        (False,
         ['Luca{-|}mela'],
         5,
         ' Mela'),

        (False,
         ['Luca{-|}mela'],
         12,
         'Luca Mela'),

        (False,
         ['Luca{-|}mela'],
         20,
         'Luca Mela'),

        (True,
         ['Luca{-|}mela'],
         6,
         'a Mela'),

    )

    @parametrize(LAST_TEXT_TESTS)
    def test_last_text(self, spaces_after, translation_list, count, text):
        if spaces_after:
            self.formatter.set_space_placement('After Output')
        for t in translation_list:
            self.format(t)
        assert self.retro_formatter.last_text(count) == text
