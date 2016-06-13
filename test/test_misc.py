# -*- coding: utf-8 -*-
# Copyright (c) 2016 Open Steno Project
# See LICENSE.txt for details.

"""Tests for misc.py."""

import unittest

import plover.misc as misc


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
