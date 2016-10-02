# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for config.py."""

import unittest
import os
import json
from collections import namedtuple

# Python 2/3 compatibility.
from six import BytesIO

from mock import patch

from plover import config
from plover.machine.keymap import Keymap
from plover.machine.registry import Registry
from plover.oslayer.config import CONFIG_DIR


def make_config(contents=''):
    return BytesIO(b'\n'.join(line.strip().encode('utf-8')
                              for line in contents.split('\n')))


class ConfigTestCase(unittest.TestCase):

    def test_simple_fields(self):
        Case = namedtuple('Case', ['field', 'section', 'option', 'default', 
                                   'value1', 'value2', 'value3'])

        cases = (
        ('machine_type', config.MACHINE_CONFIG_SECTION, 
         config.MACHINE_TYPE_OPTION, config.DEFAULT_MACHINE_TYPE, 'Gemini PR', 'TX Bolt',
         'Passport'),
        ('log_file_name', config.LOGGING_CONFIG_SECTION, config.LOG_FILE_OPTION, 
         os.path.realpath(os.path.join(CONFIG_DIR, config.DEFAULT_LOG_FILE)),
         os.path.abspath('/l1'), os.path.abspath('/log'), os.path.abspath('/sawzall')),
        ('enable_stroke_logging', config.LOGGING_CONFIG_SECTION, 
         config.ENABLE_STROKE_LOGGING_OPTION, 
         config.DEFAULT_ENABLE_STROKE_LOGGING, False, True, False),
        ('enable_translation_logging', config.LOGGING_CONFIG_SECTION, 
         config.ENABLE_TRANSLATION_LOGGING_OPTION, 
         config.DEFAULT_ENABLE_TRANSLATION_LOGGING, False, True, False),
        ('auto_start', config.MACHINE_CONFIG_SECTION, 
         config.MACHINE_AUTO_START_OPTION, config.DEFAULT_MACHINE_AUTO_START, 
         True, False, True),
        ('show_stroke_display', config.STROKE_DISPLAY_SECTION, 
         config.STROKE_DISPLAY_SHOW_OPTION, config.DEFAULT_STROKE_DISPLAY_SHOW, 
         True, False, True),
        ('space_placement', config.OUTPUT_CONFIG_SECTION, 
         config.OUTPUT_CONFIG_SPACE_PLACEMENT_OPTION, config.DEFAULT_OUTPUT_CONFIG_SPACE_PLACEMENT, 
         'Before Output', 'After Output', 'None'),
        ('stroke_display_on_top', config.STROKE_DISPLAY_SECTION, 
         config.STROKE_DISPLAY_ON_TOP_OPTION, 
         config.DEFAULT_STROKE_DISPLAY_ON_TOP, False, True, False),
        ('stroke_display_style', config.STROKE_DISPLAY_SECTION, 
         config.STROKE_DISPLAY_STYLE_OPTION, 
         config.DEFAULT_STROKE_DISPLAY_STYLE, 'Raw', 'Paper', 'Pseudo'),
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
            f = make_config('[%s]\n%s: %s' % (case.section, case.option,
                                              case.value2))
            c.load(f)
            # ..and make sure the right value is set.
            self.assertEqual(getter(), case.value2)
            # Set a value...
            setter(case.value3)
            f = make_config()
            # ...save it...
            c.save(f)
            # ...and make sure it's right.
            self.assertEqual(f.getvalue().decode('utf-8'),
                             '[%s]\n%s = %s\n\n' % (case.section, case.option,
                                                    case.value3))

    def test_clone(self):
        s = '[%s]%s = %s\n\n' % (config.MACHINE_CONFIG_SECTION, 
                                 config.MACHINE_TYPE_OPTION, 'foo')
        c = config.Config()
        c.load(make_config(s))
        f1 = make_config()
        c.save(f1)
        c2 = c.clone()
        f2 = make_config()
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
        defaults = {k: v[0] for k, v in FakeMachine.get_option_info().items()}

        machine_name = 'machine foo'
        registry = Registry()
        registry.register(machine_name, FakeMachine)
        with patch('plover.config.machine_registry', registry):
            c = config.Config()
            
            # Check default value.
            actual = c.get_machine_specific_options(machine_name)
            self.assertEqual(actual, defaults)

            # Make sure setting a value is reflecting in the getter.
            options = {
                'stroption1': 'something',
                'intoption1': 5,
                'floatoption1': 5.9,
                'booloption1': False,
            }
            c.set_machine_specific_options(options, machine_name)
            actual = c.get_machine_specific_options(machine_name)
            expected = dict(list(defaults.items()) + list(options.items()))
            self.assertEqual(actual, expected)
            
            # Test loading a file. Unknown option is ignored.
            s = '\n'.join(('[machine foo]', 'stroption1 = foo', 
                           'intoption1 = 3', 'booloption1 = True', 
                           'booloption2 = False', 'unknown = True'))
            f = make_config(s)
            c.load(f)
            expected = {
                'stroption1': 'foo',
                'intoption1': 3,
                'booloption1': True,
                'booloption2': False,
            }
            expected = dict(list(defaults.items()) + list(expected.items()))
            actual = c.get_machine_specific_options(machine_name)
            self.assertEqual(actual, expected)
            
            # Test saving a file.
            f = make_config()
            c.save(f)
            self.assertEqual(f.getvalue().decode('utf-8'), s + '\n\n')
            
            # Test reading invalid values.
            s = '\n'.join(['[machine foo]', 'floatoption1 = None', 
                           'booloption2 = True'])
            f = make_config(s)
            c.load(f)
            expected = {
                'floatoption1': 1,
                'booloption2': True,
            }
            expected = dict(list(defaults.items()) + list(expected.items()))
            actual = c.get_machine_specific_options(machine_name)
            self.assertEqual(actual, expected)
            # Check we can get/set the current machine options.
            c.set_machine_type(machine_name)
            self.assertEqual(c.get_machine_specific_options(), expected)
            expected['stroption1'] = 'foobar'
            expected['booloption2'] = False
            expected['floatoption1'] = 42.0
            c.set_machine_specific_options(expected)
            self.assertEqual(c.get_machine_specific_options(), expected)

    def test_dictionary_option(self):
        c = config.Config()
        section = config.DICTIONARY_CONFIG_SECTION
        option = config.DICTIONARY_FILE_OPTION
        config_dir = os.path.realpath(config.CONFIG_DIR)
        # Check the default value.
        self.assertEqual(c.get_dictionary_file_names(),
                         [os.path.join(config_dir, name)
                          for name in config.DEFAULT_DICTIONARIES])

        # Relative paths as assumed to be relative to CONFIG_DIR.
        filenames = [os.path.abspath(os.path.join(config_dir, path))
                     for path in ('b', 'a', 'd/c', 'e/f')]
        c.set_dictionary_file_names(filenames)
        self.assertEqual(c.get_dictionary_file_names(), filenames)
        # Absolute paths must remain unchanged...
        filenames = [os.path.abspath(path)
                     for path in ('/b', '/a', '/d', '/c')]
        c.set_dictionary_file_names(filenames)
        self.assertEqual(c.get_dictionary_file_names(), filenames)
        # Load from a file encoded the old way...
        filename = os.path.abspath('/some_file')
        f = make_config('[%s]\n%s: %s' % (section, option, filename))
        c.load(f)
        # ..and make sure the right value is set.
        self.assertEqual(c.get_dictionary_file_names(), [filename])
        # Load from a file encoded the new way...
        filenames = [os.path.abspath(path)
                     for path in ('/b', '/a', '/d', '/c')]
        value = '\n'.join('%s%d: %s' % (option, d, v) 
                              for d, v in enumerate(filenames, start=1))
        f = make_config('[%s]\n%s' % (section, value))
        c.load(f)
        # ...and make sure the right value is set.
        self.assertEqual(c.get_dictionary_file_names(), filenames)
        
        filenames.reverse()
        
        # Set a value...
        c.set_dictionary_file_names(filenames)
        f = make_config()
        # ...save it...
        c.save(f)
        # ...and make sure it's right.
        value = '\n'.join('%s%d = %s' % (option, d, v) 
                              for d, v in enumerate(filenames, start=1))
        self.assertEqual(f.getvalue().decode('utf-8'),
                         '[%s]\n%s\n\n' % (section, value))

    def test_system_keymap(self):
        mappings_list = [
            ['-D', ['[']],
            ['*', ["t", "g", "y", "h"]],
            # Keys can be a list of key names or a single key name.
            ['arpeggiate', 'space'],
            ['S-', ['a', 'q']],
        ]
        mappings_dict = dict(mappings_list)
        machine = 'Keyboard'
        section = config.SYSTEM_CONFIG_SECTION % config.DEFAULT_SYSTEM
        option = config.SYSTEM_KEYMAP_OPTION % machine.lower()
        cfg = config.Config()
        # Must return a Keymap instance.
        keymap = cfg.get_system_keymap(machine)
        self.assertIsInstance(keymap, Keymap)
        # Can be set from a Keymap.
        keymap.set_mappings(mappings_list)
        cfg.set_system_keymap(keymap, machine)
        self.assertEqual(cfg.get_system_keymap(machine), keymap)
        # Can also be set from a dictionary.
        cfg.set_system_keymap(mappings_dict, machine)
        self.assertEqual(cfg.get_system_keymap(machine), keymap)
        # Or from a compatible iterable of pairs (action, keys).
        cfg.set_system_keymap(mappings_list, machine)
        self.assertEqual(cfg.get_system_keymap(machine), keymap)
        # The config format should allow both:
        # - a list of pairs (action, keys)
        # - a dictionary (mapping each action to keys)
        def make_config_file(mappings):
            return make_config('[%s]\n%s = %s\n\n' % (section, option, json.dumps(mappings)))
        for mappings in (mappings_list, mappings_dict):
            cfg = config.Config()
            cfg.load(make_config_file(mappings))
            self.assertEqual(cfg.get_system_keymap(machine), keymap)
        # On save, a sorted list of pairs (action, keys) is expected.
        # (to reduce differences between saves)
        cfg = config.Config()
        cfg.set_system_keymap(keymap, machine)
        contents = make_config()
        cfg.save(contents)
        expected = make_config_file(sorted(keymap.get_mappings().items()))
        self.assertEqual(contents.getvalue(), expected.getvalue())
        # Check an invalid keymap is replaced by the default one.
        cfg = config.Config()
        default_keymap = cfg.get_system_keymap(machine)
        cfg.load(make_config('[%s]\n%s = pouet!' % (section, option)))
        self.assertEqual(cfg.get_system_keymap(machine), default_keymap)

    def test_as_dict_update(self):
        opt_list = '''
            auto_start
            dictionary_file_names
            enable_stroke_logging
            enable_translation_logging
            log_file_name
            machine_specific_options
            machine_type
            show_stroke_display
            show_suggestions_display
            space_placement
            start_attached
            start_capitalized
            start_minimized
            stroke_display_on_top
            stroke_display_style
            suggestions_display_on_top
            system_keymap
            translation_frame_opacity
            undo_levels
        '''.split()
        cfg = config.Config()
        excepted_dict = {
            opt: getattr(cfg, 'get_' + opt)()
            for opt in opt_list
        }
        self.assertEqual(cfg.as_dict(), excepted_dict)
        update = {
            'auto_start'           : False,
            'dictionary_file_names': [os.path.abspath('user.json')],
            'enable_stroke_logging': False,
            'space_placement'      : 'After Output',
            'start_minimized'      : False,
        }
        cfg.update(**update)
        excepted_dict.update(update)
        self.assertEqual(cfg.as_dict(), excepted_dict)

    def test_invalid_machine(self):
        cfg = config.Config()
        cfg.load(make_config(
            '[%s]\n%s: %s' % (config.MACHINE_CONFIG_SECTION,
                              'machine_type',  'foobar')
        ))
        self.assertEqual(cfg.get_machine_type(), config.DEFAULT_MACHINE_TYPE)
