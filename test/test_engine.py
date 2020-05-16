from functools import partial
import os
import tempfile

import pytest

from plover import system
from plover.config import Config, DictionaryConfig
from plover.engine import ErroredDictionary, StenoEngine
from plover.machine.base import StenotypeBase
from plover.machine.keymap import Keymap
from plover.registry import Registry
from plover.steno_dictionary import StenoDictionaryCollection

from .utils import make_dict


class FakeMachine(StenotypeBase):

    instance = None

    def __init__(self, options):
        super().__init__()
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

class FakeKeyboardEmulation:

    def send_backspaces(self, b):
        pass

    def send_string(self, s):
        pass

    def send_key_combination(self, c):
        pass

class FakeEngine(StenoEngine):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []
        def hook_callback(hook, *args, **kwargs):
            self.events.append((hook, args, kwargs))
        for hook in self.HOOKS:
            self.hook_connect(hook, partial(hook_callback, hook))

    def _in_engine_thread(self):
        return True

    def quit(self, code=0):
        self._same_thread_hook(self._quit, code)

    def start(self):
        StenoEngine.start(self)


@pytest.fixture
def engine(monkeypatch):
    FakeMachine.instance = None
    registry = Registry()
    registry.update()
    registry.register_plugin('machine', 'Fake', FakeMachine)
    monkeypatch.setattr('plover.config.registry', registry)
    monkeypatch.setattr('plover.engine.registry', registry)
    kbd = FakeKeyboardEmulation()
    cfg_file = tempfile.NamedTemporaryFile(prefix='plover',
                                           suffix='config',
                                           delete=False)
    try:
        cfg_file.close()
        cfg = Config(cfg_file.name)
        cfg['dictionaries'] = []
        cfg['machine_type'] = 'Fake'
        cfg['system_keymap'] = [(k, k) for k in system.KEYS]
        cfg.save()
        yield FakeEngine(cfg, kbd)
    finally:
        os.unlink(cfg_file.name)


def test_engine(engine):
    # Config load.
    assert engine.load_config()
    assert engine.events == []
    # Startup.
    engine.start()
    assert engine.events == [
        ('machine_state_changed', ('Fake', 'initializing'), {}),
        ('machine_state_changed', ('Fake', 'connected'), {}),
        ('config_changed', (engine.config,), {}),
    ]
    assert FakeMachine.instance is not None
    assert not FakeMachine.instance.is_suppressed
    # Output enabled.
    engine.events.clear()
    engine.output = True
    assert engine.events == [
        ('output_changed', (True,), {}),
    ]
    assert FakeMachine.instance.is_suppressed
    # Machine reconnection.
    engine.events.clear()
    engine.reset_machine()
    assert engine.events == [
        ('machine_state_changed', ('Fake', 'stopped'), {}),
        ('machine_state_changed', ('Fake', 'initializing'), {}),
        ('machine_state_changed', ('Fake', 'connected'), {}),
    ]
    assert FakeMachine.instance is not None
    assert FakeMachine.instance.is_suppressed
    # No machine reset on keymap change.
    engine.events.clear()
    new_keymap = Keymap(system.KEYS, system.KEYS)
    new_keymap.set_mappings(zip(system.KEYS, reversed(system.KEYS)))
    config_update = { 'system_keymap': new_keymap }
    assert FakeMachine.instance.keymap != new_keymap
    engine.config = config_update
    assert engine.events == [
        ('config_changed', (config_update,), {}),
    ]
    assert FakeMachine.instance.keymap == new_keymap
    # Output disabled
    engine.events.clear()
    engine.output = False
    assert engine.events == [
        ('output_changed', (False,), {}),
    ]
    assert not FakeMachine.instance.is_suppressed
    # Stopped.
    engine.events.clear()
    engine.quit(42)
    assert engine.join() == 42
    assert engine.events == [
        ('machine_state_changed', ('Fake', 'stopped'), {}),
        ('quit', (), {}),
    ]
    assert FakeMachine.instance is None

def test_loading_dictionaries(engine):
    def check_loaded_events(actual_events, expected_events):
        assert len(actual_events) == len(expected_events)
        for n, event in enumerate(actual_events):
            event_type, event_args, event_kwargs = event
            msg = 'event %u: %r' % (n, event)
            assert event_type == 'dictionaries_loaded', msg
            assert event_kwargs == {}, msg
            assert len(event_args) == 1, msg
            assert isinstance(event_args[0], StenoDictionaryCollection), msg
            assert [
                (d.path, d.enabled, isinstance(d, ErroredDictionary))
                for d in event_args[0].dicts
            ] == expected_events[n], msg
    with \
            make_dict(b'{}', 'json', 'valid1') as valid_dict_1, \
            make_dict(b'{}', 'json', 'valid2') as valid_dict_2, \
            make_dict(b'', 'json', 'invalid1') as invalid_dict_1, \
            make_dict(b'', 'json', 'invalid2') as invalid_dict_2:
        engine.start()
        for new_dictionaries, *expected_events in (
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
            engine.events.clear()
            config_update = {
                'dictionaries': [DictionaryConfig(*d)
                                 for d in new_dictionaries]
            }
            engine.config = dict(config_update)
            assert engine.events[0] == ('config_changed', (config_update,), {})
            check_loaded_events(engine.events[1:], expected_events)
        # Simulate an outdated dictionary.
        engine.events.clear()
        engine.dictionaries[valid_dict_1].timestamp -= 1
        engine.config = {}
        check_loaded_events(engine.events, [[
            (invalid_dict_2, True, True),
        ], [
            (valid_dict_1, False, False),
            (invalid_dict_2, True, True),
        ]])
