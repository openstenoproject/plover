import unittest

from plover.command.priority_dict import prioritize_dictionaries
from plover.misc import expand_path


class PriorityDictTest(unittest.TestCase):

    def setUp(self):
        self.spanish = expand_path('spanish/main.json')
        self.english = expand_path('main.json')
        self.commands = expand_path('commands.json')
        self.user = expand_path('user.json')
        self.starting_dict_order = [
            self.spanish,
            self.english,
            self.commands,
            self.user,
        ]

    def test_shortest_path_dictionary_is_default(self):
        new_order_bare_main = prioritize_dictionaries([
            'main.json',
        ], self.starting_dict_order)
        self.assertEqual(new_order_bare_main, [
            self.spanish,
            self.commands,
            self.user,
            self.english,
        ])
        #vs

        new_order_spanish_main = prioritize_dictionaries([
            'spanish/main.json',
        ], new_order_bare_main)
        self.assertEqual(new_order_spanish_main, [
            self.commands,
            self.user,
            self.english,
            self.spanish,
        ])

    def test_order_multiple_dictionaries(self):
        new_order = prioritize_dictionaries([
            'commands.json',
            'spanish/main.json',
            'user.json',
        ], self.starting_dict_order)

        self.assertEqual(new_order, [
            self.english,
            self.commands,
            self.spanish,
            self.user,
        ])

    def test_invalid_dictionaries(self):
        with self.assertRaises(ValueError):
            prioritize_dictionaries(['foobar.json'], self.starting_dict_order)
