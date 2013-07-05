# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for config.py."""

import unittest
from mock import patch
from collections import namedtuple
import plover.config as config
from cStringIO import StringIO
from plover.machine.registry import Registry

class ConfigTestCase(unittest.TestCase):

    def test_simple_fields(self):
        Case = namedtuple('Case', ['field', 'section', 'option', 'default', 
                                   'value1', 'value2', 'value3'])

        cases = (
        ('machine_type', config.MACHINE_CONFIG_SECTION, 
         config.MACHINE_TYPE_OPTION, config.DEFAULT_MACHINE_TYPE, 'foo', 'bar', 
         'blee'),
        ('dictionary_file_name', config.DICTIONARY_CONFIG_SECTION, 
         config.DICTIONARY_FILE_OPTION, config.DEFAULT_DICTIONARY_FILE, 'dict1', 
         'd2', 'third'),
        ('log_file_name', config.LOGGING_CONFIG_SECTION, config.LOG_FILE_OPTION, 
         config.DEFAULT_LOG_FILE, 'l1', 'log', 'sawzall'),
        ('enable_stroke_logging', config.LOGGING_CONFIG_SECTION, 
         config.ENABLE_STROKE_LOGGING_OPTION, 
         config.DEFAULT_ENABLE_STROKE_LOGGING, False, True, False),
        ('enable_translation_logging', config.LOGGING_CONFIG_SECTION, 
         config.ENABLE_TRANSLATION_LOGGING_OPTION, 
         config.DEFAULT_ENABLE_TRANSLATION_LOGGING, False, True, False),
        ('auto_start', config.MACHINE_CONFIG_SECTION, 
         config.MACHINE_AUTO_START_OPTION, config.DEFAULT_MACHINE_AUTO_START, 
         True, False, True),
        )

        for case in cases:
            case = Case(*case)
            c = config.Config()
            getter = getattr(c, 'get_' + case.field)
            setter = getattr(c, 'set_' + case.field)
            # Check the default value.
            self.assertEqual(getter(), case.default)
            # Set a value...
            setter(case.value1)
            # ...and make sure it is really set.
            self.assertEqual(getter(), case.value1)
            # Load from a file...
            f = StringIO('[%s]\n%s: %s' % (case.section, case.option,
                                           case.value2))
            c.load(f)
            # ..and make sure the right value is set.
            self.assertEqual(getter(), case.value2)
            # Set a value...
            setter(case.value3)
            f = StringIO()
            # ...save it...
            c.save(f)
            # ...and make sure it's right.
            self.assertEqual(f.getvalue(), 
                             '[%s]\n%s = %s\n\n' % (case.section, case.option,
                                                    case.value3))

    def test_clone(self):
        s = '[%s]%s = %s\n\n' % (config.MACHINE_CONFIG_SECTION, 
                                 config.MACHINE_TYPE_OPTION, 'foo')
        c = config.Config()
        c.load(StringIO(s))
        f1 = StringIO()
        c.save(f1)
        c2 = c.clone()
        f2 = StringIO()
        c2.save(f2)
        self.assertEqual(f1.getvalue(), f2.getvalue())

    def test_machine_specific_options(self):
        class FakeMachine(object):
            @staticmethod
            def get_option_info():
                bool_converter = lambda s: s == 'True'
                return {
                    'stroption1': (None, str),
                    'intoption1': (3, int),
                    'stroption2': ('abc', str),
                    'floatoption1': (1, float),
                    'booloption1': (True, bool_converter),
                    'booloption2': (False, bool_converter)
                }
        machine_name = 'machine foo'
        registry = Registry()
        registry.register(machine_name, FakeMachine)
        with patch('plover.config.machine_registry', registry):
            c = config.Config()
            
            # Check default value.
            expected = {
                'stroption1': None,
                'intoption1': 3,
                'stroption2': 'abc',
                'floatoption1': 1,
                'booloption1': True,
                'booloption2': False,
            }
            actual = c.get_machine_specific_options(machine_name)
            self.assertEqual(actual, expected)

            # Make sure setting a value is reflecting in the getter.
            options = {
                'stroption1': 'something',
                'intoption1': 5,
                'floatoption1': 5.9,
                'booloption1': False,
            }
            c.set_machine_specific_options(machine_name, options)
            actual = c.get_machine_specific_options(machine_name)
            self.assertEqual(actual, options)
            
            # Test loading a file.
            s = '\n'.join(('[machine foo]', 'stroption1 = foo', 
                           'intoption1 = 3', 'booloption1 = True', 
                           'booloption2 = False'))
            f = StringIO(s)
            c.load(f)
            expected = {
                'stroption1': 'foo',
                'intoption1': 3,
                'booloption1': True,
                'booloption2': False,
            }
            actual = c.get_machine_specific_options(machine_name)
            self.assertEqual(actual, expected)
            
            # Test saving a file.
            f = StringIO()
            c.save(f)
            self.assertEqual(f.getvalue(), s + '\n\n')

if __name__ == '__main__':
    unittest.main()
