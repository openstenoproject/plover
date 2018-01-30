# -*- coding: utf-8 -*-
# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for json.py."""

import unittest

from plover.dictionary.json_dict import JsonDictionary

from .utils import make_dict


class JsonDictionaryTestCase(unittest.TestCase):

    def test_load_dictionary(self):

        for contents, expected in (
            ('{"S": "a"}'.encode('utf-8'), {('S', ): 'a'}),
            # Default encoding is utf-8.
            ('{"S": "café"}'.encode('utf-8'), {('S', ): 'café'}),
            # But if that fails, the implementation
            # must automatically retry with latin-1.
            ('{"S": "café"}'.encode('latin-1'), {('S', ): 'café'}),
        ):
            with make_dict(contents) as filename:
                d = JsonDictionary.load(filename)
                self.assertEqual(dict(d.items()), expected)

        for contents, exception in (
            # Invalid JSON.
            ('{"foo", "bar",}', ValueError),
            # Invalid JSON.
            ('foo', ValueError),
            # Cannot convert to dict.
            ('"foo"', ValueError),
            # Ditto.
            ('4.2', TypeError),
        ):
            with make_dict(contents.encode('utf-8')) as filename:
                self.assertRaises(exception, JsonDictionary.load, filename)

    def test_save_dictionary(self):
        for contents, expected in (
            # Simple test.
            ({('S', ): 'a'},
             '{\n"S": "a"\n}'),
            # Check strokes format: '/' separated.
            ({('SAPL', '-PL'): 'sample'},
             '{\n"SAPL/-PL": "sample"\n}'),
            # Contents should be saved as UTF-8, no escaping.
            ({('S', ): 'café'},
             '{\n"S": "café"\n}'),
            # Check escaping of special characters.
            ({('S', ): '{^"\n\t"^}'},
             '{\n"S": "' + r'{^\"\n\t\"^}' + '"\n}'),
            # Keys are sorted on save.
            ({('B', ): 'bravo', ('A', ): 'alpha', ('C', ): 'charlie'},
             '{\n"A": "alpha",\n"B": "bravo",\n"C": "charlie"\n}'),
        ):
            with make_dict(b'foo') as filename:
                d = JsonDictionary.create(filename)
                d.update(contents)
                d.save()
                with open(filename, 'rb') as fp:
                    contents = fp.read().decode('utf-8')
                self.assertEqual(contents, expected)
