# -*- coding: utf-8 -*-
# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for json.py."""

import os
import unittest
import tempfile
from contextlib import contextmanager

from plover.dictionary.json_dict import load_dictionary
from plover.dictionary.base import DictionaryLoaderException


@contextmanager
def make_dict(contents):
    tf = tempfile.NamedTemporaryFile(delete=False)
    try:
        tf.write(contents)
        tf.close()
        yield tf.name
    finally:
        os.unlink(tf.name)

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
            with make_dict(contents) as filename:
                assertEqual(load_dictionary(filename), expected)

        for contents, exception in (
            # Invalid JSON.
            (u'{"foo", "bar",}', ValueError),
            # Invalid JSON.
            (u'foo', ValueError),
            # Cannot convert to dict.
            (u'"foo"', ValueError),
            # Ditto.
            (u'4.2', TypeError),
        ):
            with make_dict(contents) as filename:
                self.assertRaises(exception, load_dictionary, filename)
