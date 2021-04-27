# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import textwrap

import pytest

from plover.dictionary.rtfcre_dict import RtfDictionary, format_translation

from plover_build_utils.testing import dictionary_test, parametrize


@parametrize((
    lambda: ('', ''),
    lambda: ('{^in^}', r'\cxds in\cxds '),
    lambda: ('{pre^}', r'pre\cxds '),
    lambda: ('{pre^} ', r'pre\cxds '),
    lambda: ('{pre^}  ', r'pre\cxds '),
))
def test_format_translation(before, expected):
    result = format_translation(before)
    assert result == expected


def rtf_load_test(*spec):
    assert 1 <= len(spec) <= 2
    if len(spec) == 2:
        # Conversion test.
        rtf_entries = r'{\*\cxs S}%s' % spec[0]
        dict_entries = '"S": %r' % spec[1]
    else:
        spec = textwrap.dedent(spec[0]).lstrip()
        if not spec:
            rtf_entries, dict_entries = '', ''
        else:
            rtf_entries, dict_entries = tuple(spec.rsplit('\n\n', 1))
    return rtf_entries, dict_entries

RTF_LOAD_TESTS = (

    # Empty dictionary.
    lambda: rtf_load_test(
        '''



        '''),

    # Only one translation.
    lambda: rtf_load_test(
        r'''
        {\*\cxs SP}translation

        'SP': 'translation',
        '''),

    # One translation on multiple lines.
    lambda: pytest.param(*rtf_load_test(
        '''
        {\\*\\cxs SP}\r\ntranslation

        'SP': 'translation'
        '''), marks=pytest.mark.xfail),

    # Multiple translations no newlines.
    lambda: rtf_load_test(
        r'''
        {\*\cxs SP}translation{\*\cxs S}translation2

        'SP': 'translation',
        'S': 'translation2',
        '''),

    # Multiple translations on separate lines.
    lambda: rtf_load_test(
        '''
        {\\*\\cxs SP}translation\r\n{\\*\\cxs S}translation2

        'SP': 'translation',
        'S': 'translation2',
        '''),
    lambda: rtf_load_test(
        '''
        {\\*\\cxs SP}translation\n{\\*\\cxs S}translation2

        'SP': 'translation',
        'S': 'translation2',
        '''),

    # Escaped \r and \n handled.
    lambda: rtf_load_test(
        '''
        {\\*\\cxs SP}trans\\\r\\\n

        'SP': 'trans{#Return}{#Return}{#Return}{#Return}',
        '''),

    # Escaped \r\n handled in mid translation.
    lambda: rtf_load_test(
        '''
        {\\*\\cxs SP}trans\\\r\\\nlation

        'SP': 'trans{#Return}{#Return}{#Return}{#Return}lation',
        '''),

    # Whitespace is preserved in various situations.
    lambda: rtf_load_test(
        r'''
        {\*\cxs S}t  

        'S': 't{^  ^}',
        '''),
    lambda: rtf_load_test(
        r'''
        {\*\cxs S}  t

        'S': '{^  ^}t',
        '''),
    lambda: rtf_load_test(
        r'''
        {\*\cxs S}t   {\*\cxs T}t    

        'S': 't{^   ^}',
        'T': 't{^    ^}',
        '''),
    lambda: rtf_load_test(
        '''
        {\\*\\cxs S}t   \r\n{\\*\\cxs T}t    

        'S': 't{^   ^}',
        'T': 't{^    ^}',
        '''),
    lambda: rtf_load_test(
        '''
        {\\*\\cxs S}t  \r\n{\\*\\cxs T} t \r\n

        'S': 't{^  ^}',
        'T': ' t ',
        '''),

    # Translations are ignored if converter returns None
    lambda: rtf_load_test(
        r'''
        {\*\cxs S}return_none

        'S': 'return_none',
        '''),

    lambda: rtf_load_test(
        r'''
        {\*\cxs T}t t t  

        'T': 't t t{^  ^}',
        '''),

    # Conflicts result on only the last one kept.
    lambda: rtf_load_test(
        r'''
        {\*\cxs T}t
        {\*\cxs T}g

        'T': 'g',
        '''),
    lambda: rtf_load_test(
        r'''
        {\*\cxs T}t
        {\*\cxs T}return_none

        'T': 'return_none',
        '''),

    # Translation conversion tests.

    lambda: rtf_load_test('', ''),
    lambda: rtf_load_test(r'\-', '-'),
    lambda: rtf_load_test(r'\\ ', '\\ '),
    lambda: pytest.param(*rtf_load_test(r'\\', '\\'), marks=pytest.mark.xfail),
    lambda: rtf_load_test(r'\{', '{'),
    lambda: rtf_load_test(r'\}', '}'),
    lambda: rtf_load_test(r'\~', '{^ ^}'),
    lambda: rtf_load_test(r'\_', '-'),
    lambda: rtf_load_test('\\\r', '{#Return}{#Return}'),
    lambda: rtf_load_test('\\\n', '{#Return}{#Return}'),
    lambda: rtf_load_test(r'\cxds', '{^}'),
    lambda: rtf_load_test(r'pre\cxds ', '{pre^}'),
    lambda: rtf_load_test(r'pre\cxds  ', '{pre^} '),
    lambda: rtf_load_test(r'pre\cxds', '{pre^}'),
    lambda: rtf_load_test(r'\cxds post', '{^post}'),
    lambda: rtf_load_test(r'\cxds in\cxds', '{^in^}'),
    lambda: rtf_load_test(r'\cxds in\cxds ', '{^in^}'),
    lambda: rtf_load_test(r'\cxfc', '{-|}'),
    lambda: rtf_load_test(r'\cxfl', '{>}'),
    lambda: rtf_load_test(r'pre\cxfl', 'pre{>}'),
    lambda: rtf_load_test(r'\par', '{#Return}{#Return}'),
    # Stenovations extensions...
    lambda: rtf_load_test(r'{\*\cxsvatdictflags N}', '{-|}'),
    lambda: rtf_load_test(r'{\*\cxsvatdictflags LN1}', '{-|}'),
    # caseCATalyst declares new styles without a preceding \par so we treat
    # it as an implicit par.
    lambda: rtf_load_test(r'\s1', '{#Return}{#Return}'),
    # But if the \par is present we don't treat \s as an implicit par.
    lambda: rtf_load_test(r'\par\s1', '{#Return}{#Return}'),
    # Continuation styles are indented too.
    lambda: rtf_load_test(r'\par\s4', '{#Return}{#Return}{^    ^}'),
    # caseCATalyst punctuation.
    lambda: rtf_load_test(r'.', '{.}'),
    lambda: rtf_load_test(r'. ', '{.} '),
    lambda: rtf_load_test(r' . ', ' . '),
    lambda: rtf_load_test(r'{\cxa Q.}.', 'Q..'),
    # Don't mess with period that is part of a word.
    lambda: rtf_load_test(r'Mr.', 'Mr.'),
    lambda: rtf_load_test(r'.attribute', '.attribute'),
    lambda: rtf_load_test(r'{\cxstit contents}', 'contents'),
    lambda: rtf_load_test(r'{\cxfing c}', '{&c}'),
    lambda: rtf_load_test(r'{\cxp.}', '{.}'),
    lambda: rtf_load_test(r'{\cxp .}', '{.}'),
    lambda: rtf_load_test(r'{\cxp . }', '{.}'),
    lambda: rtf_load_test(r'{\cxp .  }', '{.}'),
    lambda: rtf_load_test(r'{\cxp !}', '{!}'),
    lambda: rtf_load_test(r'{\cxp ?}', '{?}'),
    lambda: rtf_load_test(r'{\cxp ,}', '{,}'),
    lambda: rtf_load_test(r'{\cxp ;}', '{;}'),
    lambda: rtf_load_test(r'{\cxp :}', '{:}'),
    lambda: rtf_load_test('{\\cxp \'}', '{^\'}'),
    lambda: rtf_load_test('{\\cxp -}', '{^-^}'),
    lambda: rtf_load_test('{\\cxp /}', '{^/^}'),
    lambda: rtf_load_test('{\\cxp...  }', '{^...  ^}'),
    lambda: rtf_load_test('{\\cxp ") }', '{^") ^}'),
    lambda: rtf_load_test('{\\nonexistent }', ''),
    lambda: rtf_load_test('{\\nonexistent contents}', 'contents'),
    lambda: rtf_load_test('{\\nonexistent cont\\_ents}', 'cont-ents'),
    lambda: rtf_load_test('{\\*\\nonexistent }', ''),
    lambda: rtf_load_test('{\\*\\nonexistent contents}', ''),
    lambda: rtf_load_test('{eclipse command}', '{eclipse command}'),
    lambda: rtf_load_test('test text', 'test text'),
    lambda: rtf_load_test('test  text', 'test{^  ^}text'),
    lambda: rtf_load_test(r'{\cxconf [{\cxc abc}]}', 'abc'),
    lambda: rtf_load_test(r'{\cxconf [{\cxc abc}|{\cxc def}]}', 'def'),
    lambda: rtf_load_test(r'{\cxconf [{\cxc abc}|{\cxc def}|{\cxc ghi}]}', 'ghi'),
    lambda: rtf_load_test(r'{\cxconf [{\cxc abc}|{\cxc {\cxp... }}]}', '{^... ^}'),
    lambda: rtf_load_test(r'be\cxds{\*\cxsvatdictentrydate\yr2006\mo5\dy10}', '{be^}'),
    lambda: rtf_load_test(r'{\nonexistent {\cxp .}}', '{.}'),
    lambda: rtf_load_test(r'{\*\nonexistent {\cxp .}}', ''),
)

RTF_SAVE_TESTS = (
    lambda: (
        '''
        'S/T': '{pre^}',
        ''',
        (b'{\\rtf1\\ansi{\\*\\cxrev100}\\cxdict{\\*\\cxsystem Plover}'
         b'{\\stylesheet{\\s0 Normal;}}\r\n'
         b'{\\*\\cxs S/T}pre\\cxds \r\n}\r\n')
    ),
)

@dictionary_test
class TestRtfDictionary:

    DICT_CLASS = RtfDictionary
    DICT_EXTENSION = 'rtf'
    DICT_REGISTERED = True
    DICT_LOAD_TESTS = RTF_LOAD_TESTS
    DICT_SAVE_TESTS = RTF_SAVE_TESTS
    DICT_SAMPLE = ''

    @staticmethod
    def make_dict(contents):
        if isinstance(contents, bytes):
            return contents
        rtf_styles = {
            0: 'Normal',
            1: 'Question',
            2: 'Answer',
            3: 'Colloquy',
            4: 'Continuation Q',
            5: 'Continuation A',
            6: 'Continuation Col',
            7: 'Paren',
            8: 'Centered',
        }
        rtf = (
            '\r\n'.join(
                [r'{\rtf1\ansi\cxdict{\*\cxrev100}{\*\cxsystem Fake Software}'] +
                [r'{\s%d %s;}' % (k, v) for k, v in rtf_styles.items()] +
                ['}'])
            + contents
            + '\r\n}'
        )
        return rtf.encode('cp1252')
