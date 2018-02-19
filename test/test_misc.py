# -*- coding: utf-8 -*-
# Copyright (c) 2016 Open Steno Project
# See LICENSE.txt for details.

"""Tests for misc.py."""

import inspect
import os
import sys

import pytest

import plover.misc as misc
import plover.oslayer.config as conf
from plover.resource import ASSET_SCHEME


def test_popcount_8():
    for n in range(256):
        assert misc.popcount_8(n) == format(n, 'b').count('1')
    with pytest.raises(AssertionError):
        misc.popcount_8(256)
    with pytest.raises(AssertionError):
        misc.popcount_8(-1)


if sys.platform.startswith('win32'):
    ABS_PATH = os.path.normcase(r'c:\foo\bar')
else:
    ABS_PATH = '/foo/bar'

@pytest.mark.parametrize(('short_path', 'full_path'), (
    # Asset, no change.
    (ASSET_SCHEME + 'foo:bar',
     ASSET_SCHEME + 'foo:bar'),
    # Absolute path, no change.
    (ABS_PATH,
     ABS_PATH),
    # Relative path, resolve relative to configuration directory.
    (os.path.normcase(os.path.normpath('foo/bar')),
     os.path.normcase(os.path.join(os.path.realpath(conf.CONFIG_DIR),
                                   'foo', 'bar'))),
    # Path below the user home directory.
    (os.path.normcase(os.path.normpath('~/foo/bar')),
     os.path.normcase(os.path.expanduser(os.path.normpath('~/foo/bar')))),
))
def test_dictionary_path(short_path, full_path):
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
        assert result == expected, function

@pytest.mark.parametrize(('input', 'output'), (
    # Boolean.
    (False, False),
    (True, True),
    # True string values.
    ('1', True),
    ('yes', True),
    ('true', True),
    ('on', True),
    # False string values.
    ('0', False),
    ('no', False),
    ('false', False),
    ('off', False),
    # Invalid string values.
    ('yep', ValueError),
    ('nope', ValueError),
    # Other types.
    (0, False),
    (1, True),
    (42, True),
    (4.2, True),
    (0.0, False),
    (None, False),
))
def test_boolean(input, output):
    if inspect.isclass(output):
        with pytest.raises(output):
            misc.boolean(input)
    else:
        assert misc.boolean(input) == output
