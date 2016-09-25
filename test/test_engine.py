
import os
import json
import unittest
from contextlib import contextmanager
from functools import partial

import mock

from plover import app
from plover.machine.base import StenotypeBase
from plover import system


class FakeConfig(object):

    def __init__(self, **kwargs):
        for name, default in (
            ('auto_start'                , False                        ),
            ('machine_type'              , 'Fake'                       ),
            ('machine_specific_options'  , {}                           ),
            ('system_keymap'             , [(k, k) for k in system.KEYS]),
            ('dictionary_file_names'     , []                           ),
            ('log_file_name'             , os.devnull                   ),
            ('enable_stroke_logging'     , False                        ),
            ('enable_translation_logging', False                        ),
            ('space_placement'           , 'Before Output'              ),
            ('undo_levels'               , 10                           ),
            ('start_capitalized'         , True                         ),
            ('start_attached'            , False                        ),
        ):
            value = kwargs.get(name, default)
            self.__dict__['get_%s' % name] = partial(lambda v, *a: v, value)

class FakeRegistry(object):

    def __init__(self, **kwargs):
        self._machines = kwargs

    def get(self, name):
        return self._machines[name]

class FakeMachine(StenotypeBase):

    KEYS_LAYOUT = ' '.join(system.KEYS)

    def __init__(self, options):
        super(FakeMachine, self).__init__()
        self._options = options

class EngineTestCase(unittest.TestCase):

    @contextmanager
    def _setup(self, **kwargs):
        self.reg = FakeRegistry(Fake=FakeMachine)
        self.cfg = FakeConfig(**kwargs)
        self.state_transitions = []
        self.engine = app.StenoEngine()
        try:
            with mock.patch('plover.app.machine_registry', self.reg):
                def callback(state):
                    self.state_transitions.append((state, self.engine.is_running))
                self.engine.add_callback(callback)
                yield
        finally:
            del self.reg
            del self.cfg
            del self.engine
            del self.state_transitions

    def test_engine_init(self):
        with self._setup():
            app.init_engine(self.engine, self.cfg)
            self.assertEqual(self.state_transitions, [
                (None, False), # engine init
                (None, False), #
            ])
            self.assertIsInstance(self.engine.machine, FakeMachine)

    def test_engine_bad_mappings(self):
        with self._setup(system_keymap='invalid'):
            with self.assertRaises(Exception):
                app.init_engine(self.engine, self.cfg)
            self.assertEqual(self.engine.machine, None)

    def test_engine_auto_start(self):
        with self._setup(auto_start=True):
            app.init_engine(self.engine, self.cfg)
            self.assertEqual(self.state_transitions, [
                (None, True), # engine init
                (None, True), #
            ])

    def test_engine_update_no_changes(self):
        with self._setup():
            app.init_engine(self.engine, self.cfg)
            self.assertEqual(self.state_transitions, [
                (None, False), # engine init
                (None, False), #
            ])

    def test_engine_reconnect(self):
        with self._setup():
            app.init_engine(self.engine, self.cfg)
            self.engine.machine._ready()
            self.engine.set_is_running(True)
            self.engine.machine._error()
            app.update_engine(self.engine, self.cfg, reset_machine=True)
            self.engine.machine._ready()
            self.assertEqual(self.state_transitions, [
                (None          , False), # engine init
                (None          , False), #
                ('connected'   , False), # machine ready
                (None          , True ), # set_is_running(True)
                ('disconnected', True ), # machine error
                (None          , True ), # engine update
                ('connected'   , True ), # machine ready
            ])

