# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

from plover.steno_dictionary import StenoDictionary
from rtfcre_dict import load_dictionary, TranslationConverter
import mock
import re
import unittest

class TestCase(unittest.TestCase):
    
    def test_converter(self):
        convert = TranslationConverter()
        
        cases = (
        
        ('', ''),
        (r'\-', '-'),
        (r'\\', '\\'),
        (r'\{', '{'),
        (r'\}', '}'),
        (r'\~', '{^ ^}'),
        (r'\_', '-'),
        ('\\\r\n', '{#Return}{#Return}'),
        (r'\cxds', '{^}'),
        (r'pre\cxds', 'pre{^}'),
        (r'\cxds post', '{^}post'),
        (r'\cxds in\cxds', '{^}in{^}'),
        (r'\cxfc', '{-|}'),
        (r'\cxfl', ''),
        (r'pre\cxfl', 'pre'),
        (r'\par', '{#Return}{#Return}'),
        (r'\s1', ''),
        (r'\par\s1', '{#Return}{#Return}'),
        (r'{\cxstit contents}', 'contents'),
        (r'{\cxfing c}', '{&c}'),
        (r'{\cxp.}', '{.}'),
        (r'{\cxp .}', '{.}'),
        (r'{\cxp . }', '{.}'),
        (r'{\cxp .  }', '{.}'),
        (r'{\cxp !}', '{!}'),
        (r'{\cxp ?}', '{?}'),
        (r'{\cxp ,}', '{,}'),
        (r'{\cxp ;}', '{;}'),
        (r'{\cxp :}', '{:}'),
        ('{\\cxp \'}', '{^\'}'),
        ('{\\cxp -}', '{^-^}'),
        ('{\\cxp /}', '{^/^}'),
        ('{\\cxp...  }', '{^...  ^}'),
        ('{\\cxp ") }', '{^") ^}'),
        ('{\\nonexistant }', ''),
        ('{\\nonexistant contents}', 'contents'),
        ('{\\nonexistant cont\\_ents}', 'cont-ents'),
        ('{\\*\\nonexistant }', ''),
        ('{\\*\\nonexistant contents}', ''),
        ('{eclipse command}', '{eclipse command}'),
        ('test text', 'test text'),
        ('test  text', 'test{^  ^}text'),
        (r'{\cxconf [{\cxc abc}]}', 'abc'),
        (r'{\cxconf [{\cxc abc}|{\cxc def}]}', 'def'),
        (r'{\cxconf [{\cxc abc}|{\cxc def}|{\cxc ghi}]}', 'ghi'),
        (r'{\cxconf [{\cxc abc}|{\cxc {\cxp... }}]}', '{^... ^}'),
        
        (r'{\nonexistant {\cxp .}}', '{.}'),
        (r'{\*\nonexistant {\cxp .}}', ''),
        )
        
        for before, after in cases:
            self.assertEqual(convert(before), after)
    
    def test_load_dict(self):
        """Test the load_dict function.

        This test just tests load_dict so it mocks out the converters and just
        verifies that they are called.

        """
        header = r'''{\rtf1\ansi\cxdict{\*\cxrev100}{\*\cxsystem Fake Software}
        {\stylesheet
        {\s0 Normal;}
        {\s1 Question;}
        {\s2 Answer;}
        {\s3 Colloquy;}
        {\s4 Continuation Q;}
        {\s5 Continuation A;}
        {\s6 Continuation Col;}
        {\s7 Paren;}
        {\s8 Centered;}
        }
        '''
        footer = '''
        }'''
        
        def make_dict(s):
            return (header.replace('\n', '\r\n') + s + 
                    footer.replace('\n', '\r\n'))
            
        def assertEqual(a, b):
            self.assertEqual(a._dict, b)
                        
        class Converter(object):
            def __call__(self, s):
                if s == 'return_none':
                    return None
                return 'converted(%s)' % s
                
        convert = Converter()
        normalize = lambda x: 'normalized(%s)' % x
        
        cases = (
        
        # Empty dictionary.
        ('', {}),
        # Only one translation.
        ('{\\*\\cxs SP}translation', {'SP': 'translation'}),
        # Multiple translations no newlines.
        ('{\\*\\cxs SP}translation{\\*\\cxs S}translation2', 
         {'SP': 'translation', 'S': 'translation2'}),
        # Multiple translations on separate lines.
        ('{\\*\\cxs SP}translation\r\n{\\*\\cxs S}translation2', 
         {'SP': 'translation', 'S': 'translation2'}),
        # Escaped \r\n handled
        ('{\\*\\cxs SP}trans\\\r\n', {'SP': 'trans\\\r\n'}),
        # Escaped \r\n handled in mid translation
        ('{\\*\\cxs SP}trans\\\r\nlation', {'SP': 'trans\\\r\nlation'}),
        # Whitespace is preserved in various situations.
        ('{\\*\\cxs S}t  ', {'S': 't  '}),
        ('{\\*\\cxs S}t   {\\*\\cxs T}t    ', {'S': 't   ', 'T': 't    '}),
        ('{\\*\\cxs S}t   \r\n{\\*\\cxs T}t    ', {'S': 't   ', 'T': 't    '}),
        ('{\\*\\cxs S}t  \r\n{\\*\\cxs T} t \r\n', {'S': 't  ', 'T': ' t '}),
        # Translations are ignored if converter returns None
        ('{\\*\\cxs S}return_none', {}),
        ('{\\*\\cxs T}t t t  ', {'T': 't t t  '}),
        # Conflicts result on only the last one kept.
        ('{\\*\\cxs T}t{\\*\\cxs T}g', {'T': 'g'}),
        ('{\\*\\cxs T}t{\\*\\cxs T}return_none', {'T': 't'}),
        
        )
        
        patch_path = 'plover.dictionary.rtfcre_dict'
        with mock.patch.multiple(patch_path, normalize_steno=normalize, 
                                 TranslationConverter=Converter):
            for s, expected in cases:
                expected = dict((normalize(k), convert(v)) 
                                for k, v in expected.iteritems())
                assertEqual(load_dictionary(make_dict(s)), expected)

if __name__ == '__main__':
    unittest.main()
