# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for config.py."""

from contextlib import ExitStack
from io import BytesIO
import inspect
import json
import os
import sys
import textwrap

import pytest

from plover import config
from plover.config import DictionaryConfig
from plover.machine.keyboard import Keyboard
from plover.machine.keymap import Keymap
from plover.misc import expand_path
from plover.registry import Registry
from plover.system import english_stenotype


def dedent_strip(s):
    return textwrap.dedent(s).strip()

def dict_replace(d, update):
    d = dict(d)
    d.update(update)
    return d


class FakeMachine:

    KEYMAP_MACHINE_TYPE = 'Keyboard'

    def get_keys():
        return Keyboard.get_keys()

    def get_actions():
        return Keyboard.get_actions()

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

FakeMachine.DEFAULT_OPTIONS = {k: v[0] for k, v in FakeMachine.get_option_info().items()}


class FakeSystem:
    KEYS = english_stenotype.KEYS
    IMPLICIT_HYPHEN_KEYS = ()
    SUFFIX_KEYS = ()
    NUMBER_KEY = english_stenotype.NUMBER_KEY
    NUMBERS = english_stenotype.NUMBERS
    UNDO_STROKE_STENO = english_stenotype.UNDO_STROKE_STENO
    ORTHOGRAPHY_RULES = []
    ORTHOGRAPHY_RULES_ALIASES = {}
    ORTHOGRAPHY_WORDLIST = None
    KEYMAPS = {
        'Faky faky': english_stenotype.KEYMAPS['Keyboard'],
    }
    DEFAULT_DICTIONARIES = ('utilisateur.json', 'principal.json')


def test_config_dict():
    short_path = os.path.normcase(os.path.normpath('~/foo/bar'))
    full_path = os.path.normcase(os.path.expanduser(os.path.normpath('~/foo/bar')))
    # Path should be expanded.
    assert DictionaryConfig(short_path).path == full_path
    assert DictionaryConfig(full_path).path == full_path
    # Short path is available through `short_path`.
    assert DictionaryConfig(full_path).short_path == short_path
    assert DictionaryConfig(short_path).short_path == short_path
    # Enabled default to True.
    assert DictionaryConfig('foo').enabled
    assert not DictionaryConfig('foo', False).enabled
    # When converting to a dict (for dumping to JSON),
    # a dictionary with the shortened path is used.
    assert DictionaryConfig(full_path).to_dict() == \
            {'path': short_path, 'enabled': True}
    assert DictionaryConfig(short_path, False).to_dict() == \
            {'path': short_path, 'enabled': False}
    # Test from_dict creation helper.
    assert DictionaryConfig.from_dict({'path': short_path}) == \
            DictionaryConfig(short_path)
    assert DictionaryConfig.from_dict({'path': full_path, 'enabled': False}) == \
            DictionaryConfig(short_path, False)


if sys.platform.startswith('win32'):
    ABS_PATH = os.path.normcase(r'c:/foo/bar')
else:
    ABS_PATH = '/foo/bar'

DEFAULT_KEYMAP = Keymap(Keyboard.get_keys(), english_stenotype.KEYS + Keyboard.get_actions())
DEFAULT_KEYMAP.set_mappings(english_stenotype.KEYMAPS['Keyboard'])

DEFAULTS = {
    'space_placement': 'Before Output',
    'start_attached': False,
    'start_capitalized': False,
    'undo_levels': config.DEFAULT_UNDO_LEVELS,
    'log_file_name': expand_path('strokes.log'),
    'enable_stroke_logging': False,
    'enable_translation_logging': False,
    'start_minimized': False,
    'show_stroke_display': False,
    'show_suggestions_display': False,
    'translation_frame_opacity': 100,
    'classic_dictionaries_display_order': False,
    'enabled_extensions': set(),
    'auto_start': False,
    'machine_type': 'Keyboard',
    'machine_specific_options': { 'arpeggiate': False },
    'system_name': config.DEFAULT_SYSTEM_NAME,
    'system_keymap': DEFAULT_KEYMAP,
    'dictionaries': [DictionaryConfig(p) for p in english_stenotype.DEFAULT_DICTIONARIES]
}

CONFIG_TESTS = (

    ('defaults',
     '''
     ''',
     DEFAULTS,
     {}, {},
     '''
     ''',
    ),

    ('simple_options',
     '''
     [Output Configuration]
     space_placement = After Output
     start_attached = true
     start_capitalized = yes
     undo_levels = 42
     ''',
     dict_replace(DEFAULTS, {
         'space_placement': 'After Output',
         'start_attached': True,
         'start_capitalized': True,
         'undo_levels': 42,
     }),
     {
         'space_placement': 'Before Output',
         'start_attached': False,
         'start_capitalized': False,
         'undo_levels': 200,
     },
     None,
     '''
     [Output Configuration]
     space_placement = Before Output
     start_attached = False
     start_capitalized = False
     undo_levels = 200
     ''',
    ),

    ('machine_options',
     '''
     [Machine Configuration]
     auto_start = True
     machine_type = keyboard

     [Keyboard]
     arpeggiate = True
     ''',
     dict_replace(DEFAULTS, {
         'auto_start': True,
         'machine_specific_options': dict_replace(
             DEFAULTS['machine_specific_options'], {
                 'arpeggiate': True,
             }),
     }),
     {
         'machine_type': 'faKY FAky',
         'machine_specific_options': {
                 'stroption1': 42,
                 'floatoption1': '4.2',
                 'booloption1': False,
         },
         'system_name': 'FAUX SYSTÈME',
         'system_keymap': str(DEFAULT_KEYMAP),
     },
     {
         'machine_type': 'Faky faky',
         'machine_specific_options': dict_replace(
             FakeMachine.DEFAULT_OPTIONS, {
                 'stroption1': '42',
                 'floatoption1': 4.2,
                 'booloption1': False,
             }),
         'system_name': 'Faux système',
         'system_keymap': DEFAULT_KEYMAP,
         'dictionaries': [DictionaryConfig('utilisateur.json'),
                          DictionaryConfig('principal.json')],
     },
     '''
     [Machine Configuration]
     auto_start = True
     machine_type = Faky faky

     [Keyboard]
     arpeggiate = True

     [Faky faky]
     booloption1 = False
     booloption2 = False
     floatoption1 = 4.2
     intoption1 = 3
     stroption1 = 42
     stroption2 = abc

     [System]
     name = Faux système

     [System: Faux système]
     keymap[faky faky] = %s
     ''' % DEFAULT_KEYMAP,
    ),

    ('machine_bool_option',
     '''
     ''',
     DEFAULTS,
     {
         'machine_specific_options': {
                 'arpeggiate': True,
         },
     },
     {
         'machine_specific_options': {
             'arpeggiate': True,
         }
     },
     '''
     [Keyboard]
     arpeggiate = True
     '''
    ),

    ('legacy_dictionaries_1',
     '''
     [Dictionary Configuration]
     dictionary_file = main.json
     ''',
     dict_replace(DEFAULTS, {
         'dictionaries': [DictionaryConfig('main.json')],
     }),
     {
         'dictionaries': ['user.json', 'main.json'],
     },
     {
         'dictionaries': [DictionaryConfig('user.json'),
                          DictionaryConfig('main.json')],
     },
     '''
     [System: English Stenotype]
     dictionaries = [{"enabled": true, "path": "user.json"}, {"enabled": true, "path": "main.json"}]
     '''
    ),

    ('legacy_dictionaries_2',
     '''
     [Dictionary Configuration]
     dictionary_file1 = main.json
     dictionary_file3 = user.json
     ''',
     dict_replace(DEFAULTS, {
         'dictionaries': [DictionaryConfig('user.json'),
                          DictionaryConfig('main.json')],
     }),
     {
         'dictionaries': ['user.json', 'commands.json', 'main.json'],
     },
     {
         'dictionaries': [DictionaryConfig('user.json'),
                          DictionaryConfig('commands.json'),
                          DictionaryConfig('main.json')],
     },
     '''
     [System: English Stenotype]
     dictionaries = [{"enabled": true, "path": "user.json"}, {"enabled": true, "path": "commands.json"}, {"enabled": true, "path": "main.json"}]
     '''
    ),

    ('dictionaries',
     '''
     [System: English Stenotype]
     dictionaries = %s
     ''' % json.dumps([os.path.join(ABS_PATH, 'user.json'),
                       "english/main.json"]),
     dict_replace(DEFAULTS, {
         'dictionaries': [DictionaryConfig(os.path.join(ABS_PATH, 'user.json')),
                          DictionaryConfig('english/main.json')],
     }),
     {
         'dictionaries': [DictionaryConfig(os.path.join(ABS_PATH, 'user.json')),
                          DictionaryConfig('english/main.json')],
     },
     {
         'dictionaries': [DictionaryConfig(os.path.join(ABS_PATH, 'user.json')),
                          DictionaryConfig('english/main.json')],
     },
     '''
     [System: English Stenotype]
     dictionaries = %s
     ''' % json.dumps([{"enabled": True, "path": os.path.join(ABS_PATH, 'user.json')},
                       {"enabled": True, "path": os.path.join('english', 'main.json')}],
                      sort_keys=True)
    ),

    ('invalid_config',
     '''
     [Startup]
     Start Minimized = True

     [Machine Configuratio
     machine_type = Faky faky
     ''',
     config.InvalidConfigurationError,
     {},
     {},
     '''
     '''
    ),

    ('invalid_keymap_1',
     '''
     [System: English Stenotype]
     keymap[keyboard] = [["_-"]]
     ''',
     DEFAULTS,
     {},
     {},
     None,
    ),

    ('invalid_keymap_2',
     '''
     [System: English Stenotype]
     keymap[keyboard] = 42
     ''',
     DEFAULTS,
     {},
     {},
     None,
    ),

    ('invalid_options_1',
     '''
     [System]
     name = foobar
     ''',
     DEFAULTS,
     {},
     {},
     None,
    ),

    ('invalid_options_2',
     '''
     [Machine Configuration]
     machine_type = Faky faky

     [Faky faky]
     booloption2 = 50
     intoption1 = 3.14
     ''',
     dict_replace(DEFAULTS, {
         'machine_type': 'Faky faky',
         'machine_specific_options': FakeMachine.DEFAULT_OPTIONS,
     }),
     {},
     {},
     None,
    ),

    ('invalid_update_1',
     '''
     [Translation Frame]
     opacity = 75
     ''',
     dict_replace(DEFAULTS, {
         'translation_frame_opacity': 75,
     }),
     {
         'start_minimized': False,
         'show_stroke_display': True,
         'translation_frame_opacity': 101,
     },
     config.InvalidConfigOption,
     None,
    ),

    ('invalid_update_2',
     '''
     ''',
     DEFAULTS,
     {
         'machine_type': 'FakeMachine',
         'machine_specific_options': dict_replace(
             FakeMachine.DEFAULT_OPTIONS, {
                 'stroption1': '42',
             }),
     },
     config.InvalidConfigOption,
     None,
    ),

    ('setitem_valid',
     '''
     ''',
     DEFAULTS,
     ('auto_start', True),
     None,
     '''
     [Machine Configuration]
     auto_start = True
     '''
    ),

    ('setitem_invalid',
     '''
     ''',
     DEFAULTS,
     ('undo_levels', -42),
     config.InvalidConfigOption,
     '''
     '''
    ),
)


def make_config(contents=''):
    return BytesIO(b'\n'.join(line.strip().encode('utf-8')
                              for line in contents.split('\n')))
def config_contents(f):
    return f.getvalue().decode('utf-8').strip()


@pytest.mark.parametrize(('original_contents', 'original_config',
                          'config_update', 'validated_config_update',
                          'resulting_contents'),
                         [t[1:] for t in CONFIG_TESTS],
                         ids=[t[0] for t in CONFIG_TESTS])
def test_config(original_contents, original_config,
                config_update, validated_config_update,
                resulting_contents, monkeypatch):
    registry = Registry()
    registry.register_plugin('machine', 'Keyboard', Keyboard)
    registry.register_plugin('machine', 'Faky faky', FakeMachine)
    registry.register_plugin('system', 'English Stenotype', english_stenotype)
    registry.register_plugin('system', 'Faux système', FakeSystem)
    monkeypatch.setattr('plover.config.registry', registry)
    # Check initial contents.
    f = make_config(original_contents)
    cfg = config.Config()
    if inspect.isclass(original_config):
        with pytest.raises(original_config):
            cfg.load(f)
        original_config = dict(DEFAULTS)
        cfg.clear()
    else:
        cfg.load(f)
    cfg_dict = cfg.as_dict()
    for name, value in original_config.items():
        assert cfg[name] == value
        assert cfg_dict[name] == value
    # Check updated contents.
    with ExitStack() as stack:
        if inspect.isclass(validated_config_update):
            stack.enter_context(pytest.raises(validated_config_update))
            validated_config_update = None
        elif validated_config_update is None:
            validated_config_update = config_update
        if isinstance(config_update, dict):
            cfg.update(**config_update)
        else:
            key, value = config_update
            cfg[key] = value
        if validated_config_update is not None:
            if isinstance(validated_config_update, dict):
                cfg_dict.update(validated_config_update)
            else:
                key, value = validated_config_update
                cfg_dict[key] = value
        assert cfg.as_dict() == cfg_dict
    f = make_config()
    cfg.save(f)
    if resulting_contents is None:
        resulting_contents = original_contents
    assert config_contents(f) == dedent_strip(resulting_contents)
