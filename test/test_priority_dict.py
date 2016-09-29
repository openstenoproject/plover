import unittest

from plover.dictionary.prioritize_dictionaries import prioritize_dictionaries

class PriorityDictTest(unittest.TestCase):
    def setUp(self):
        self.starting_dict_order = \
                [u'~/.local/share/plover/spanish/main.json',
                u'~/.local/share/plover/main.json',
                u'~/.local/share/plover/commands.json',
                u'~/.local/share/plover/user.json']

    def test_shortest_path_dictionary_is_default(self):
        new_order_bare_main = prioritize_dictionaries("main.json",
                self.starting_dict_order)
        self.assertEqual(new_order_bare_main,
                [u'~/.local/share/plover/spanish/main.json',
                u'~/.local/share/plover/commands.json',
                u'~/.local/share/plover/user.json',
                u'~/.local/share/plover/main.json'])
        
        #vs

        new_order_spanish_main = prioritize_dictionaries("spanish/main.json",
                new_order_bare_main)
        self.assertEqual(new_order_spanish_main,
                [u'~/.local/share/plover/commands.json',
                u'~/.local/share/plover/user.json',
                u'~/.local/share/plover/main.json',
                u'~/.local/share/plover/spanish/main.json'])

    def test_order_multiple_dictionaries(self):
        #new_order = prioritize_dictionaries("commands.json;spanish/main.json; user.json;",
        new_order = prioritize_dictionaries("commands.json;spanish/main.json; user.json;",
                self.starting_dict_order)

        self.assertEqual(new_order,
                [u'~/.local/share/plover/main.json',
                u'~/.local/share/plover/user.json',
                u'~/.local/share/plover/spanish/main.json',
                u'~/.local/share/plover/commands.json'])

