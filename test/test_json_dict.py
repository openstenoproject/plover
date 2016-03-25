# -*- coding: utf-8 -*-
# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for json.py."""

import StringIO
import unittest
from plover.dictionary.json_dict import load_dictionary
from plover.dictionary.base import DictionaryLoaderException

def make_dict(contents):
    d = StringIO.StringIO(contents)
    d.name = "'%s'" % contents
    return d

class JsonDictionaryTestCase(unittest.TestCase):

    def test_load_dictionary(self):
        def assertEqual(a, b):
            self.assertEqual(a._dict, b)

        for contents, expected in (
            (u'{"S": "a"}'       , {('S', ): 'a'    }),
            # Default encoding is utf-8.
            (u'{"S": "café"}'.encode('utf-8'), {('S', ): u'café'}),
            # But if that fails, the implementation
            # must automatically retry with latin-1.
            (u'{"S": "café"}'.encode('latin-1'), {('S', ): u'café'}),
        ):
            assertEqual(load_dictionary(make_dict(contents)), expected)
        
        with self.assertRaises(DictionaryLoaderException):
            load_dictionary(make_dict('foo'))

if __name__ == '__main__':
    unittest.main()
