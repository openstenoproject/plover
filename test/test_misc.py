# -*- coding: utf-8 -*-
# Copyright (c) 2016 Open Steno Project
# See LICENSE.txt for details.

"""Tests for misc.py."""

import os
import unittest

import plover.misc as misc
import plover.oslayer.config as conf


class MiscTestCase(unittest.TestCase):
    def test_popcount_8(self):
        for n in range(256):
            self.assertEqual(misc.popcount_8(n),
                             format(n, 'b').count('1'))
        with self.assertRaises(AssertionError):
            misc.popcount_8(256)
        with self.assertRaises(AssertionError):
            misc.popcount_8(-1)

    def test_characters(self):
        self.assertEqual(list(misc.characters('STKPWHR')),
                         ['S', 'T', 'K', 'P', 'W', 'H', 'R'])
        self.assertEqual(list(misc.characters('')), [])
        self.assertEqual(list(misc.characters(u'✂⌨')), [u'✂', u'⌨'])

    def test_dictionary_path(self):
        for short_path, full_path in (
            # Absolute path, no change.
            (os.path.abspath('/foo/bar'),
             os.path.abspath('/foo/bar')),
            # Relative path, resolve relative to configuration directory.
            (os.path.normpath('foo/bar'),
             os.path.join(conf.CONFIG_DIR, 'foo', 'bar')),
            # Path below the user home directory.
            (os.path.normpath('~/foo/bar'),
             os.path.expanduser(os.path.normpath('~/foo/bar'))),
        ):
            for input, function, expected in (
                # Unchanged.
                (short_path, 'shorten', short_path),
                (full_path, 'expand', full_path),
                # Shorten.
                (full_path, 'shorten', short_path),
                # Expand.
                (short_path, 'expand', full_path),
            ):
                function = '%s_path' % function
                result = getattr(misc, function)(input)
                self.assertEqual(result, expected, msg='%s(%r)=%r != %r'
                                 % (function, input, result, expected))
