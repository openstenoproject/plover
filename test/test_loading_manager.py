# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Tests for loading_manager.py."""

from collections import defaultdict
import os
import tempfile
import unittest

# Python 2/3 compatibility.
from six import assertCountEqual

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
                self.timestamp = os.path.getmtime(self.tf.name)

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
                return FakeDictionaryContents(d.contents, d.timestamp)

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
            self.assertEqual(results[1].path, df('e'))
            self.assertIsInstance(results[1].exception, Exception)
            self.assertIsInstance(results[3], DictionaryLoaderException)
            self.assertEqual(results[3].path, df('f'))
            self.assertIsInstance(results[3].exception, Exception)
            # Only loaded the files once.
            self.assertTrue(all(x == 1 for x in loader.load_counts.values()))
            # No reload if timestamp is unchanged, or more recent.
            # (use case: dictionary edited with Plover and saved back)
            dictionaries['c'].contents = 'CCCCC'
            dictionaries['c'].timestamp += 1
            results = manager.load([df('c')])
            self.assertEqual(results, ['ccccc'])
            self.assertEqual(loader.load_counts[df('c')], 1)
            # Check files are reloaded when modified.
            # Note: do not try to "touch" the file using os.utime
            # as it's not reliable without sleeping to account
            # for operating system resolution.
            mtime = os.path.getmtime(df('c'))
            def getmtime(path):
                assert path == df('c')
                return mtime + 1
            with patch('os.path.getmtime', getmtime):
                results = manager.load([df('c')])
            self.assertEqual(results, ['CCCCC'])
            self.assertEqual(loader.load_counts[df('c')], 2)
