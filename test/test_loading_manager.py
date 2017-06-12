# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Tests for loading_manager.py."""

from collections import defaultdict
import os
import tempfile
import unittest

from mock import patch

from plover.exception import DictionaryLoaderException
import plover.dictionary.loading_manager as loading_manager


class DictionaryLoadingManagerTestCase(unittest.TestCase):

    def test_loading(self):

        class FakeDictionaryContents(object):

            def __init__(self, contents, timestamp):
                self.contents = contents
                self.timestamp = timestamp

            def __eq__(self, other):
                if isinstance(other, FakeDictionaryContents):
                    return self.contents == other.contents
                return self.contents == other

        class FakeDictionaryInfo(object):

            def __init__(self, name, contents):
                self.name = name
                self.contents = contents
                self.tf = tempfile.NamedTemporaryFile()

            def __repr__(self):
                return 'FakeDictionaryInfo(%r, %r)' % (self.name, self.contents)

        class MockLoader(object):
            def __init__(self, files):
                self.files = files
                self.load_counts = defaultdict(int)

            def __call__(self, filename):
                self.load_counts[filename] += 1
                d = self.files[filename]
                if isinstance(d.contents, Exception):
                    raise d.contents
                timestamp = os.path.getmtime(filename)
                return FakeDictionaryContents(d.contents, timestamp)

        dictionaries = {}
        for i in range(8):
            c = chr(ord('a') + i)
            contents = c * 5
            if i >= 4:
                contents = Exception(contents)
            d = FakeDictionaryInfo(c, contents)
            assert d.tf.name not in dictionaries
            dictionaries[d.tf.name] = d
            assert c not in dictionaries
            dictionaries[c] = d

        def df(name):
            return dictionaries[name].tf.name

        loader = MockLoader(dictionaries)
        with patch('plover.dictionary.loading_manager.load_dictionary', loader):
            manager = loading_manager.DictionaryLoadingManager()
            manager.start_loading(df('a')).get()
            manager.start_loading(df('b')).get()
            results = manager.load([df('c'), df('b')])
            # Returns the right values in the right order.
            self.assertEqual(results, ['ccccc', 'bbbbb'])
            # Dropped superfluous files.
            self.assertCountEqual([df('b'), df('c')], manager.dictionaries.keys())
            # Check dict like interface.
            self.assertEqual(len(manager), 2)
            self.assertFalse(df('a') in manager)
            with self.assertRaises(KeyError):
                manager[df('a')]
            self.assertTrue(df('b') in manager)
            self.assertTrue(df('c') in manager)
            self.assertEqual(results, [manager[df('c')], manager[df('b')]])
            # Return a DictionaryLoaderException for load errors.
            results = manager.load([df('c'), df('e'), df('b'), df('f')])
            self.assertEqual(len(results), 4)
            self.assertEqual(results[0], 'ccccc')
            self.assertEqual(results[2], 'bbbbb')
            self.assertIsInstance(results[1], DictionaryLoaderException)
            self.assertEqual(results[1].path, df('e'))
            self.assertIsInstance(results[1].exception, Exception)
            self.assertIsInstance(results[3], DictionaryLoaderException)
            self.assertEqual(results[3].path, df('f'))
            self.assertIsInstance(results[3].exception, Exception)
            # Only loaded the files once.
            self.assertTrue(all(x == 1 for x in loader.load_counts.values()))
            # No reload if file timestamp is unchanged, or the dictionary
            # timestamp is more recent. (use case: dictionary edited with
            # Plover and saved back)
            file_timestamp = results[0].timestamp
            results[0].timestamp = file_timestamp + 1
            dictionaries['c'].contents = 'CCCCC'
            results = manager.load([df('c')])
            self.assertEqual(results, ['ccccc'])
            self.assertEqual(loader.load_counts[df('c')], 1)
            # Check outdated dictionaries are reloaded.
            results[0].timestamp = file_timestamp - 1
            results = manager.load([df('c')])
            self.assertEqual(results, ['CCCCC'])
            self.assertEqual(loader.load_counts[df('c')], 2)
            # Check trimming of outdated dictionaries.
            results[0].timestamp = file_timestamp - 1
            manager.unload_outdated()
            self.assertEqual(len(manager), 0)
            self.assertFalse(df('c') in manager)
