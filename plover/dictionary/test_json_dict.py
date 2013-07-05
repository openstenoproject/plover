# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for json.py."""

import unittest
from json_dict import load_dictionary
from base import DictionaryLoaderException

class JsonDictionaryTestCase(unittest.TestCase):
    
    def test_load_dictionary(self):
        def assertEqual(a, b):
            self.assertEqual(a._dict, b)

        assertEqual(load_dictionary('{"S": "a"}'), {('S',): 'a'})
        assertEqual(load_dictionary('{"S": "\xc3\xb1"}'), {('S',): u'\xf1'})
        assertEqual(load_dictionary('{"S": "\xf1"}'), {('S',): u'\xf1'})
        
        with self.assertRaises(DictionaryLoaderException):
            load_dictionary('foo')

if __name__ == '__main__':
    unittest.main()
