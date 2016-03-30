# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Tests for loading_manager.py."""

from collections import defaultdict
import unittest

from mock import patch

import plover.dictionary.loading_manager as loading_manager


class DictionaryLoadingManagerTestCase(unittest.TestCase):

    def test_loading(self):
        class MockLoader(object):
            def __init__(self, files):
                self.files = files
                self.load_counts = defaultdict(int)
                
            def __call__(self, filename):
                self.load_counts[filename] += 1
                return self.files[filename]
                
        files = {c: c * 5 for c in [chr(ord('a') + i) for i in range(10)]}
        loader = MockLoader(files)
        with patch('plover.dictionary.loading_manager.load_dictionary', loader):
            manager = loading_manager.DictionaryLoadingManager()
            manager.start_loading('a')
            manager.start_loading('b')
            results = manager.load(['c', 'b'])
            # Returns the right values in the right order.
            self.assertEqual(results, ['ccccc', 'bbbbb'])
            # Only loaded the files once.
            self.assertTrue(all(x == 1 for x in loader.load_counts.values()))
            # Dropped superfluous files.
            self.assertEqual(['b', 'c'], sorted(manager.dictionaries.keys()))
