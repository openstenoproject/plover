# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for json.py."""

import StringIO
import unittest
from json_dict import load_dictionary
from base import DictionaryLoaderException

def make_dict(contents):
    d = StringIO.StringIO(contents)
    d.name = "'%s'" % contents
    return d

class JsonDictionaryTestCase(unittest.TestCase):

    def test_load_dictionary(self):
        def assertEqual(a, b):
            self.assertEqual(a._dict, b)

        for contents, expected in (
            ('{"S": "a"}'       , {('S', ): 'a'    }),
            ('{"S": "\xc3\xb1"}', {('S', ): u'\xf1'}),
            ('{"S": "\xf1"}'    , {('S', ): u'\xf1'}),
        ):
            assertEqual(load_dictionary(make_dict(contents)), expected)
        
        with self.assertRaises(DictionaryLoaderException):
            load_dictionary(make_dict('foo'))

if __name__ == '__main__':
    unittest.main()
