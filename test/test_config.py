# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for config.py."""

from collections import namedtuple
from io import BytesIO
import json
import os
import sys
import unittest

from mock import patch

from plover import config, system
from plover.config import DictionaryConfig
from plover.machine.keymap import Keymap
from plover.misc import expand_path, normalize_path
from plover.registry import Registry
from plover.oslayer.config import CONFIG_DIR


if sys.platform.startswith('win32'):
    ABS_PATH = os.path.normcase(r'c:\foo\bar')
else:
    ABS_PATH = '/foo/bar'


def make_config(contents=''):
    return BytesIO(b'\n'.join(line.strip().encode('utf-8')
                              for line in contents.split('\n')))


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


class ConfigTestCase(unittest.TestCase):

    def test_simple_fields(self):
        Case = namedtuple('Case', ['field', 'section', 'option', 'default', 
                                   'value1', 'value2', 'value3'])

        cases = (
        ('machine_type', config.MACHINE_CONFIG_SECTION, 
         config.MACHINE_TYPE_OPTION, config.DEFAULT_MACHINE_TYPE, 'Gemini PR', 'TX Bolt',
         'Passport'),
        ('log_file_name', config.LOGGING_CONFIG_SECTION, config.LOG_FILE_OPTION, 
         normalize_path(os.path.join(CONFIG_DIR, config.DEFAULT_LOG_FILE)),
         os.path.join(ABS_PATH, 'l1'), os.path.join(ABS_PATH, 'log'), os.path.join(ABS_PATH, 'sawzall')),
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

    def test_machine_specific_options(self):
        defaults = {k: v[0] for k, v in FakeMachine.get_option_info().items()}

        machine_name = 'machine foo'
        registry = Registry()
        registry.register_plugin('machine', machine_name, FakeMachine)
        with patch('plover.config.registry', registry):
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

    def test_config_dict(self):
        short_path = os.path.normcase(os.path.normpath('~/foo/bar'))
        full_path = os.path.normcase(os.path.expanduser(os.path.normpath('~/foo/bar')))
        # Path should be expanded.
        self.assertEqual(DictionaryConfig(short_path).path, full_path)
        self.assertEqual(DictionaryConfig(full_path).path, full_path)
        # Short path is available through `short_path`.
        self.assertEqual(DictionaryConfig(full_path).short_path, short_path)
        self.assertEqual(DictionaryConfig(short_path).short_path, short_path)
        # Enabled default to True.
        self.assertEqual(DictionaryConfig('foo').enabled, True)
        self.assertEqual(DictionaryConfig('foo', False).enabled, False)
        # When converting to a dict (for dumping to JSON),
        # a dictionary with the shortened path is used.
        self.assertEqual(DictionaryConfig(full_path).to_dict(),
                         {'path': short_path, 'enabled': True})
        self.assertEqual(DictionaryConfig(short_path, False).to_dict(),
                         {'path': short_path, 'enabled': False})
        # Test from_dict creation helper.
        self.assertEqual(config.DictionaryConfig.from_dict(
            {'path': short_path}), DictionaryConfig(short_path))
        self.assertEqual(config.DictionaryConfig.from_dict(
            {'path': full_path, 'enabled': False}), DictionaryConfig(short_path, False))

    def test_dictionary_config(self):
        short_path = os.path.normcase(os.path.normpath('~/foo/bar'))
        full_path = os.path.normcase(os.path.expanduser(os.path.normpath('~/foo/bar')))
        dc = DictionaryConfig(short_path)
        # Path should be expanded.
        self.assertEqual(dc.path, full_path)
        # Shortened path is available through short_path.
        self.assertEqual(dc.short_path, short_path)
        # Enabled default to True.
        self.assertEqual(dc.enabled, True)
        # Check conversion to dict: short path should be used.
        self.assertEqual(dc.to_dict(), {'path': short_path, 'enabled': True})
        # Test replace method.
        dc = dc.replace(enabled=False)
        self.assertEqual(dc.path, full_path)
        self.assertEqual(dc.enabled, False)
        # Test creation from dict.
        self.assertEqual(DictionaryConfig.from_dict({'path': short_path, 'enabled': False}), dc)

    def test_dictionaries_option(self):
        section = config.SYSTEM_CONFIG_SECTION % config.DEFAULT_SYSTEM_NAME
        option = config.SYSTEM_DICTIONARIES_OPTION
        legacy_section = config.LEGACY_DICTIONARY_CONFIG_SECTION
        legacy_option = config.LEGACY_DICTIONARY_FILE_OPTION
        c = config.Config()
        config_dir = os.path.normcase(os.path.realpath(config.CONFIG_DIR))
        # Check the default value.
        self.assertEqual(c.get_dictionaries(),
                         [DictionaryConfig(path)
                          for path in system.DEFAULT_DICTIONARIES])
        # Load from a file encoded the ancient way...
        filename = normalize_path('/some_file')
        f = make_config('[%s]\n%s: %s' % (legacy_section, legacy_option, filename))
        c.load(f)
        # ..and make sure the right value is set.
        self.assertEqual(c.get_dictionaries(), [DictionaryConfig(filename)])
        # Load from a file encoded the old way...
        filenames = [os.path.join(ABS_PATH, f) for f in ('b', 'a', 'd', 'c')]
        dictionaries = [DictionaryConfig(path) for path in filenames]
        value = '\n'.join('%s%d: %s' % (legacy_option, d, v)
                              for d, v in enumerate(reversed(filenames), start=1))
        f = make_config('[%s]\n%s' % (legacy_section, value))
        c.load(f)
        # ...and make sure the right value is set.
        self.assertEqual(c.get_dictionaries(), dictionaries)
        # Check the config is saved back converted to the new way.
        f = make_config()
        c.save(f)
        new_config_contents = '[%s]\n%s = %s\n\n' % (
            section, option, json.dumps([
                {'path': path, 'enabled': True}
                for path in filenames
            ], sort_keys=True))
        self.assertEqual(f.getvalue().decode('utf-8'), new_config_contents)
        # Load from a file encoded the new way...
        f = make_config(new_config_contents)
        c.load(f)
        # ...and make sure the right value is set.
        self.assertEqual(c.get_dictionaries(), dictionaries)
        # Set a value...
        dictionaries.reverse()
        filenames.reverse()
        c.set_dictionaries(dictionaries)
        f = make_config()
        # ...save it...
        c.save(f)
        # ...and make sure it's right.
        new_config_contents = '[%s]\n%s = %s\n\n' % (
            section, option, json.dumps([
                {'path': path, 'enabled': True}
                for path in filenames
            ], sort_keys=True))
        self.assertEqual(f.getvalue().decode('utf-8'), new_config_contents)
        # The new way must take precedence over the old way.
        legacy_value = '\n'.join('%s%d = %s' % (legacy_option, d, v)
                              for d, v in enumerate(['/foo', '/bar'], start=1))
        f = make_config(new_config_contents + '\n[%s]\n%s\n' % ( legacy_section, legacy_value))
        c.load(f)
        self.assertEqual(c.get_dictionaries(), dictionaries)

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
        section = config.SYSTEM_CONFIG_SECTION % config.DEFAULT_SYSTEM_NAME
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
            classic_dictionaries_display_order
            dictionaries
            enable_stroke_logging
            enable_translation_logging
            enabled_extensions
            log_file_name
            machine_specific_options
            machine_type
            show_stroke_display
            show_suggestions_display
            space_placement
            start_attached
            start_capitalized
            start_minimized
            system_keymap
            system_name
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
            'dictionaries'         : [DictionaryConfig('user.json', False)],
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
