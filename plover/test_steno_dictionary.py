# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for steno_dictionary.py."""

import unittest
from steno_dictionary import StenoDictionary, load_dictionary

class StenoDictionaryTestCase(unittest.TestCase):

    def test_dictionary(self):
        notifications = []
        def listener(longest_key):
            notifications.append(longest_key)
        
        d = StenoDictionary()
        self.assertEqual(d.longest_key, 0)
        
        d.add_longest_key_listener(listener)
        d[('S',)] = 'a'
        self.assertEqual(d.longest_key, 1)
        self.assertEqual(notifications, [1])
        d[('S', 'S', 'S', 'S')] = 'b'
        self.assertEqual(d.longest_key, 4)
        self.assertEqual(notifications, [1, 4])
        d[('S', 'S')] = 'c'
        self.assertEqual(d.longest_key, 4)
        self.assertEqual(d[('S', 'S')], 'c')
        self.assertEqual(notifications, [1, 4])
        del d[('S', 'S', 'S', 'S')]
        self.assertEqual(d.longest_key, 2)
        self.assertEqual(notifications, [1, 4, 2])
        del d[('S',)]
        self.assertEqual(d.longest_key, 2)
        self.assertEqual(notifications, [1, 4, 2])
        d.clear()
        self.assertEqual(d.longest_key, 0)
        self.assertEqual(notifications, [1, 4, 2, 0])
        
        d.remove_longest_key_listener(listener)
        d[('S', 'S')] = 'c'
        self.assertEqual(d.longest_key, 2)
        self.assertEqual(notifications, [1, 4, 2, 0])
        
        self.assertEqual(StenoDictionary([('a', 'b')]).items(), [('a', 'b')])
        self.assertEqual(StenoDictionary(a='b').items(), [('a', 'b')])

    def test_load_dictionary(self):
        def assertEqual(a, b):
            self.assertEqual(a._dict, b)
        
        assertEqual(load_dictionary('{"S": "a"}'), {('S',): 'a'})
        assertEqual(load_dictionary('{"S": "\xc3\xb1"}'), {('S',): u'\xf1'})
        assertEqual(load_dictionary('{"S": "\xf1"}'), {('S',): u'\xf1'})
        
if __name__ == '__main__':
    unittest.main()