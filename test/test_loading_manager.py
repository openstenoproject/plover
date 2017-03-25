# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Tests for loading_manager.py."""

from collections import defaultdict
import tempfile
import unittest

# Python 2/3 compatibility.
from six import assertCountEqual

from mock import patch

from plover.exception import DictionaryLoaderException
import plover.dictionary.loading_manager as loading_manager


class DictionaryLoadingManagerTestCase(unittest.TestCase):

    def test_loading(self):

        class FakeDictionary(object):

            def __init__(self, name, contents):
                self.name = name
                self.contents = contents
                self.tf = tempfile.NamedTemporaryFile()

            def __hash__(self):
                return hash(self.name)

            def __repr__(self):
                return 'FakeDictionary(%r, %r)' % (self.name, self.contents)

        class MockLoader(object):
            def __init__(self, files):
                self.files = files
                self.load_counts = defaultdict(int)

            def __call__(self, filename):
                self.load_counts[filename] += 1
                contents = self.files[filename].contents
                if isinstance(contents, Exception):
                    raise contents
                return contents

        dictionaries = {}
        for i in range(8):
            c = chr(ord('a') + i)
            contents = c * 5
            if i >= 4:
                contents = Exception(contents)
            d = FakeDictionary(c, contents)
            assert d.tf.name not in dictionaries
            dictionaries[d.tf.name] = d
            assert c not in dictionaries
            dictionaries[c] = d

        def df(name):
            return dictionaries[name].tf.name

        loader = MockLoader(dictionaries)
        with patch('plover.dictionary.loading_manager.load_dictionary', loader):
            manager = loading_manager.DictionaryLoadingManager()
            manager.start_loading(df('a'))
            manager.start_loading(df('b'))
            results = manager.load([df('c'), df('b')])
            # Returns the right values in the right order.
            self.assertEqual(results, ['ccccc', 'bbbbb'])
            # Dropped superfluous files.
            assertCountEqual(self, [df('b'), df('c')], manager.dictionaries.keys())
            # Return a DictionaryLoaderException for load errors.
            results = manager.load([df('c'), df('e'), df('b'), df('f')])
            self.assertEqual(len(results), 4)
            self.assertEqual(results[0], 'ccccc')
            self.assertEqual(results[2], 'bbbbb')
            self.assertIsInstance(results[1], DictionaryLoaderException)
            self.assertEqual(results[1].filename, df('e'))
            self.assertIsInstance(results[1].exception, Exception)
            self.assertIsInstance(results[3], DictionaryLoaderException)
            self.assertEqual(results[3].filename, df('f'))
            self.assertIsInstance(results[3].exception, Exception)
            # Only loaded the files once.
            self.assertTrue(all(x == 1 for x in loader.load_counts.values()))
