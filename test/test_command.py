""" Unit tests for built-in engine command plugins. """

import ast
import io

import pytest

from plover.command.set_config import set_config
from plover.config import Config, DictionaryConfig
from test.test_config import DEFAULTS, DEFAULT_KEYMAP


class _CFGFakeEngine:
    """ The plugin sets the engine.config property, which unpacks a dict as keywords into config.update. """
    def __init__(self):
        self._cfg = Config()
    @property
    def config(self):
        return self._cfg.as_dict()
    @config.setter
    def config(self, options):
        self._cfg.update(**options)
    def cfg_to_bytes(self):
        stream = io.BytesIO()
        self._cfg.save(stream)
        return stream.getvalue()


def test_set_config():
    """ Unit tests for set_config command. Test at least one of each valid data type. """
    # Config values are sometimes converted and stored as different types than the input,
    # so the expected output config values may not always be strictly equal to the input.
    valid_tests = [
        ('"space_placement":"After Output"',               "After Output"),
        ('"start_attached":True',                          True),
        ('"undo_levels":10',                               10),
        ('"log_file_name":"c:/whatever/morestrokes.log"',  "c:/whatever/morestrokes.log"),
        ('"enabled_extensions":[]',                        set()),
        ('"machine_type":"Keyboard"',                      "Keyboard"),
        ('"machine_specific_options":{"arpeggiate":True}', {"arpeggiate": True}),
        ('"system_keymap":'+str(DEFAULT_KEYMAP),           DEFAULT_KEYMAP),
        ('"dictionaries":("user.json","main.json")',       list(map(DictionaryConfig, ("user.json", "main.json")))),
    ]
    engine = _CFGFakeEngine()
    engine.config = DEFAULTS
    # For each valid command, make sure the value made it in and back out acceptably.
    for (cmdline, expected) in valid_tests:
        set_config(engine, cmdline)
        key, value = ast.literal_eval("{"+cmdline+"}").popitem()
        assert engine.config[key] == expected
    # Save the modified config file to a bytes object for reference.
    file_individual = engine.cfg_to_bytes()
    # Multiple options can be set with one command if separated by commas.
    # Try setting every test option from scratch with a single command
    # and make sure the saved results are the same as before.
    engine.config = DEFAULTS
    compound_cmdline = ",".join(t[0] for t in valid_tests)
    set_config(engine, compound_cmdline)
    file_compound = engine.cfg_to_bytes()
    assert file_individual == file_compound


def test_set_config_exceptions():
    """ Unit tests for set_config exception handling. """
    invalid_tests = [
        '"undo_levels"10',                                    # No delimiter in command.
        '"undo_levels":"does a string work?"',                # Wrong value type.
        '"machine_type":"Telepathy"',                         # Unsupported value.
        '"machine_specific_options":{"closing_brace":False',  # Bad format for dict literal.
    ]
    engine = _CFGFakeEngine()
    for cmdline in invalid_tests:
        with pytest.raises(ValueError):
            set_config(engine, cmdline)
