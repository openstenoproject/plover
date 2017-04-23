
import os
import unittest
from contextlib import contextmanager
from functools import partial

import mock

from plover import system
from plover.config import DEFAULT_SYSTEM_NAME, DictionaryConfig
from plover.engine import ErroredDictionary, StenoEngine
from plover.registry import Registry
from plover.machine.base import StenotypeBase
from plover.steno_dictionary import StenoDictionaryCollection

from .utils import make_dict


class FakeConfig(object):

    DEFAULTS = {
        'auto_start'                : False,
        'machine_type'              : 'Fake',
        'machine_specific_options'  : {},
        'system_name'               : DEFAULT_SYSTEM_NAME,
        'system_keymap'             : [(k, k) for k in system.KEYS],
        'dictionaries'              : {},
        'log_file_name'             : os.devnull,
        'enable_stroke_logging'     : False,
        'enable_translation_logging': False,
        'space_placement'           : 'Before Output',
        'undo_levels'               : 10,
        'start_capitalized'         : True,
        'start_attached'            : False,
        'enabled_extensions'        : set(),
    }

    def __init__(self, **kwargs):
        self._options = {}
        for name, default in self.DEFAULTS.items():
            value = kwargs.get(name, default)
            self._options[name] = value
            self.__dict__['get_%s' % name] = partial(lambda v, *a: v, value)
        self.target_file = os.devnull

    def load(self, fp):
        pass

    def as_dict(self):
        return dict(self._options)

    def update(self, **kwargs):
        self._options.update(kwargs)


class FakeMachine(StenotypeBase):

    instance = None

    def __init__(self, options):
        super(FakeMachine, self).__init__()
        self.options = options
        self.is_suppressed = False

    @classmethod
    def get_keys(cls):
        return system.KEYS

    def start_capture(self):
        assert FakeMachine.instance is None
        FakeMachine.instance = self
        self._initializing()
        self._ready()

    def stop_capture(self):
        FakeMachine.instance = None
        self._stopped()

    def set_suppression(self, enabled):
        self.is_suppressed = enabled

class FakeKeyboardEmulation(object):

    def send_backspaces(self, b):
        pass

    def send_string(self, s):
        pass

    def send_key_combination(self, c):
        pass

class FakeEngine(StenoEngine):

    def _in_engine_thread(self):
        return True

    def quit(self, code=0):
        self._same_thread_hook(self._quit, code)

    def start(self):
        StenoEngine.start(self)


class EngineTestCase(unittest.TestCase):

    @contextmanager
    def _setup(self, **kwargs):
        FakeMachine.instance = None
        self.reg = Registry()
        self.reg.register_plugin('machine', 'Fake', FakeMachine)
        self.kbd = FakeKeyboardEmulation()
        self.cfg = FakeConfig(**kwargs)
        self.events = []
        self.engine = FakeEngine(self.cfg, self.kbd)
        def hook_callback(hook, *args, **kwargs):
            self.events.append((hook, args, kwargs))
        for hook in self.engine.HOOKS:
            self.engine.hook_connect(hook, partial(hook_callback, hook))
        try:
            with mock.patch('plover.engine.registry', self.reg):
                yield
        finally:
            del self.reg
            del self.cfg
            del self.engine
            del self.events

    def test_engine(self):
        with self._setup():
            # Config load.
            self.assertEqual(self.engine.load_config(), True)
            self.assertEqual(self.events, [])
            # Startup.
            self.engine.start()
            self.assertEqual(self.events, [
                ('machine_state_changed', ('Fake', 'initializing'), {}),
                ('machine_state_changed', ('Fake', 'connected'), {}),
                ('config_changed', (self.cfg.as_dict(),), {}),
            ])
            self.assertIsNotNone(FakeMachine.instance)
            self.assertFalse(FakeMachine.instance.is_suppressed)
            # Output enabled.
            self.events = []
            self.engine.output = True
            self.assertEqual(self.events, [
                ('output_changed', (True,), {}),
            ])
            self.assertTrue(FakeMachine.instance.is_suppressed)
            # Machine reconnection.
            self.events = []
            self.engine.reset_machine()
            self.assertEqual(self.events, [
                ('machine_state_changed', ('Fake', 'stopped'), {}),
                ('machine_state_changed', ('Fake', 'initializing'), {}),
                ('machine_state_changed', ('Fake', 'connected'), {}),
            ])
            self.assertIsNotNone(FakeMachine.instance)
            self.assertTrue(FakeMachine.instance.is_suppressed)
            # No machine reset on keymap change.
            self.events = []
            new_keymap = list(zip(system.KEYS, reversed(system.KEYS)))
            config_update = { 'system_keymap': new_keymap }
            self.assertNotEqual(FakeMachine.instance.keymap, new_keymap)
            self.engine.config = config_update
            self.assertEqual(self.events, [
                ('config_changed', (config_update,), {}),
            ])
            self.assertEqual(FakeMachine.instance.keymap, new_keymap)
            # Output disabled
            self.events = []
            self.engine.output = False
            self.assertEqual(self.events, [
                ('output_changed', (False,), {}),
            ])
            self.assertFalse(FakeMachine.instance.is_suppressed)
            # Stopped.
            self.events = []
            self.engine.quit(42)
            self.assertEqual(self.engine.join(), 42)
            self.assertEqual(self.events, [
                ('machine_state_changed', ('Fake', 'stopped'), {}),
                ('quit', (), {}),
            ])
            self.assertIsNone(FakeMachine.instance)

    def test_loading_dictionaries(self):
        def check_loaded_events(actual_events, expected_events):
            self.assertEqual(len(actual_events), len(expected_events), msg='events: %r' % self.events)
            for n, event in enumerate(actual_events):
                event_type, event_args, event_kwargs = event
                msg = 'event %u: %r' % (n, event)
                self.assertEqual(event_type, 'dictionaries_loaded', msg=msg)
                self.assertEqual(event_kwargs, {}, msg=msg)
                self.assertEqual(len(event_args), 1, msg=msg)
                self.assertIsInstance(event_args[0], StenoDictionaryCollection, msg=msg)
                self.assertEqual([
                    (d.path, d.enabled, isinstance(d, ErroredDictionary))
                    for d in event_args[0].dicts
                ], expected_events[n], msg=msg)
        with \
                make_dict(b'{}', 'json', 'valid1') as valid_dict_1, \
                make_dict(b'{}', 'json', 'valid2') as valid_dict_2, \
                make_dict(b'', 'json', 'invalid1') as invalid_dict_1, \
                make_dict(b'', 'json', 'invalid2') as invalid_dict_2, \
                self._setup():
            self.engine.start()
            for test in (
                # Load one valid dictionary.
                [[
                    # path, enabled
                    (valid_dict_1, True),
                ], [
                    # path, enabled, errored
                    (valid_dict_1, True, False),
                ]],
                # Load another invalid dictionary.
                [[
                    (valid_dict_1, True),
                    (invalid_dict_1, True),
                ], [
                    (valid_dict_1, True, False),
                    (invalid_dict_1, True, True),
                ]],
                # Disable first dictionary.
                [[
                    (valid_dict_1, False),
                    (invalid_dict_1, True),
                ], [
                    (valid_dict_1, False, False),
                    (invalid_dict_1, True, True),
                ]],
                # Replace invalid dictonary with another invalid one.
                [[
                    (valid_dict_1, False),
                    (invalid_dict_2, True),
                ], [
                    (valid_dict_1, False, False),
                ], [
                    (valid_dict_1, False, False),
                    (invalid_dict_2, True, True),
                ]]
            ):
                config_dictionaries = [
                    DictionaryConfig(path, enabled)
                    for path, enabled in test[0]
                ]
                self.events = []
                config_update = { 'dictionaries': list(config_dictionaries), }
                self.engine.config = dict(config_update)
                self.assertEqual(self.events[0], ('config_changed', (config_update,), {}))
                check_loaded_events(self.events[1:], test[1:])
            # Simulate an outdated dictionary.
            self.events = []
            self.engine.dictionaries[valid_dict_1].timestamp -= 1
            self.engine.config = {}
            check_loaded_events(self.events, [[
                (invalid_dict_2, True, True),
            ], [
                (valid_dict_1, False, False),
                (invalid_dict_2, True, True),
            ]])
