import unittest

from plover.command.toggle_dict import toggle_dictionaries
from plover.misc import expand_path

from plover.config import DictionaryConfig


class PriorityDictTest(unittest.TestCase):

    def setUp(self):
        self.spanish = DictionaryConfig(expand_path('spanish/main.json'), True)
        self.english = DictionaryConfig(expand_path('main.json'), True)
        self.commands = DictionaryConfig(expand_path('commands.json'), True)
        self.user = DictionaryConfig(expand_path('user.json'), True)
        self.dictionaries = [
            self.spanish,
            self.english,
            self.commands,
            self.user,
        ]

    def test_shortest_path_dictionary_is_default(self):
        toggles = toggle_dictionaries([
            '+main.json',
            '-spanish/main.json',
        ], self.dictionaries)
        self.assertEqual(toggles, {
            self.english.path: '+',
            self.spanish.path: '-',
        })

    def test_last_win(self):
        toggles = toggle_dictionaries([
            '+commands.json',
            '-commands.json',
            '!commands.json',
        ], self.dictionaries)
        self.assertEqual(toggles, {
            self.commands.path: '!',
        })

    def test_toggle_multiple_dictionaries(self):
        toggles = toggle_dictionaries([
            '+spanish/main.json',
            '!commands.json',
            '-user.json',
        ], self.dictionaries)
        self.assertEqual(toggles, {
            self.commands.path: '!',
            self.spanish.path: '+',
            self.user.path: '-',
        })

    def test_invalid_toggle(self):
        with self.assertRaises(ValueError):
            toggle_dictionaries(['=user.json'], self.dictionaries)

    def test_invalid_dictionaries(self):
        with self.assertRaises(ValueError):
            toggle_dictionaries(['+foobar.json'], self.dictionaries)
