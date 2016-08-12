# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for steno_dictionary.py."""

import unittest

# Python 2/3 compatibility.
from six import assertCountEqual

from plover.steno_dictionary import StenoDictionary, StenoDictionaryCollection


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
        
        self.assertEqual(list(StenoDictionary([('a', 'b')]).items()), [('a', 'b')])
        self.assertEqual(list(StenoDictionary(a='b').items()), [('a', 'b')])

    def test_dictionary_collection(self):
        dc = StenoDictionaryCollection()
        d1 = StenoDictionary()
        d1[('S',)] = 'a'
        d1[('T',)] = 'b'
        d1.set_path('d1')
        d2 = StenoDictionary()
        d2[('S',)] = 'c'
        d2[('W',)] = 'd'
        d2.set_path('d2')
        dc.set_dicts([d1, d2])
        self.assertEqual(dc.lookup(('S',)), 'c')
        self.assertEqual(dc.lookup(('W',)), 'd')
        self.assertEqual(dc.lookup(('T',)), 'b')
        f = lambda k, v: v == 'c'
        dc.add_filter(f)
        self.assertIsNone(dc.lookup(('S',)))
        self.assertEqual(dc.raw_lookup(('S',)), 'c')
        self.assertEqual(dc.lookup(('W',)), 'd')
        self.assertEqual(dc.lookup(('T',)), 'b')
        self.assertEqual(dc.reverse_lookup('c'), [('S',)])
        
        dc.remove_filter(f)
        self.assertEqual(dc.lookup(('S',)), 'c')
        self.assertEqual(dc.lookup(('W',)), 'd')
        self.assertEqual(dc.lookup(('T',)), 'b')
        
        self.assertEqual(dc.reverse_lookup('c'), [('S',)])
        
        dc.set(('S',), 'e')
        self.assertEqual(dc.lookup(('S',)), 'e')
        self.assertEqual(d2[('S',)], 'e')

        dc.set(('S',), 'f', dictionary='d1')
        self.assertEqual(dc.lookup(('S',)), 'e')
        self.assertEqual(d1[('S',)], 'f')
        self.assertEqual(d2[('S',)], 'e')

    def test_dictionary_collection_longest_key(self):

        k1 = ('S',)
        k2 = ('S', 'T')
        k3 = ('S', 'T', 'R')

        dc = StenoDictionaryCollection()
        self.assertEqual(dc.longest_key, 0)

        d1 = StenoDictionary()
        d1._path = 'd1'
        d1.save = lambda: None
        d1[k1] = 'a'

        dc.set_dicts([d1])
        self.assertEqual(dc.longest_key, 1)

        d1[k2] = 'a'
        self.assertEqual(dc.longest_key, 2)

        d2 = StenoDictionary()
        d2._path = 'd2'
        d2[k3] = 'c'

        dc.set_dicts([d1, d2])
        self.assertEqual(dc.longest_key, 3)

        del d1[k2]
        self.assertEqual(dc.longest_key, 3)

        dc.set_dicts([d1])
        self.assertEqual(dc.longest_key, 1)

        dc.set_dicts([])
        self.assertEqual(dc.longest_key, 0)

    def test_reverse_lookup(self):
        dc = StenoDictionaryCollection()

        d1 = StenoDictionary()
        d1[('PWAOUFL',)] = 'beautiful'
        d1[('WAOUFL',)] = 'beautiful'

        d2 = StenoDictionary()
        d2[('PW-FL',)] = 'beautiful'

        d3 = StenoDictionary()
        d3[('WAOUFL',)] = 'not beautiful'

        # Simple test.
        dc.set_dicts([d1])
        assertCountEqual(self,
                         dc.reverse_lookup('beautiful'),
                         [('PWAOUFL',), ('WAOUFL',)])

        # No duplicates.
        dc.set_dicts([d2, StenoDictionary(d2)])
        assertCountEqual(self,
                         dc.reverse_lookup('beautiful'),
                         [('PW-FL',)])

        # Don't stop at the first dictionary with matches.
        dc.set_dicts([d1, d2])
        assertCountEqual(self,
                         dc.reverse_lookup('beautiful'),
                         [('PWAOUFL',), ('WAOUFL',), ('PW-FL',)])

        # Ignore keys overriden by a higher precedence dictionary.
        dc.set_dicts([d1, d2, d3])
        assertCountEqual(self,
                         dc.reverse_lookup('beautiful'),
                         [('PWAOUFL',), ('PW-FL',)])
