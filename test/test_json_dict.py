# -*- coding: utf-8 -*-
# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for json.py."""

import os
import unittest
import tempfile
from contextlib import contextmanager

from plover.dictionary.json_dict import load_dictionary, save_dictionary


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
            (u'{"S": "a"}'.encode('utf-8'), {('S', ): u'a'}),
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
            with make_dict(contents.encode('utf-8')) as filename:
                self.assertRaises(exception, load_dictionary, filename)

    def test_save_dictionary(self):
        for contents, expected in (
            # Simple test.
            ({('S', ): 'a'},
             u'{\n"S": "a"\n}'),
            # Check strokes format: '/' separated.
            ({('SAPL', '-PL'): u'sample'},
             u'{\n"SAPL/-PL": "sample"\n}'),
            # Contents should be saved as UTF-8, no escaping.
            ({('S', ): u'café'},
             u'{\n"S": "café"\n}'),
            # Check escaping of special characters.
            ({('S', ): u'{^"\n\t"^}'},
             u'{\n"S": "' + r'{^\"\n\t\"^}' + u'"\n}'),
            # Keys are sorted on save.
            ({('B', ): u'bravo', ('A', ): u'alpha', ('C', ): u'charlie'},
             u'{\n"A": "alpha",\n"B": "bravo",\n"C": "charlie"\n}'),
        ):
            with make_dict(b'foo') as filename:
                with open(filename, 'wb') as fp:
                    save_dictionary(contents, fp)
                with open(filename, 'rb') as fp:
                    contents = fp.read().decode('utf-8')
                self.assertEqual(contents, expected)
