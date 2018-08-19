# -*- coding: utf-8 -*-
# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for json.py."""

import inspect

import pytest

from plover.dictionary.json_dict import JsonDictionary

from .utils import make_dict
from . import parametrize


LOAD_TESTS = (
    lambda: ('{"S": "a"}', {('S', ): 'a'}),
    # Default encoding is utf-8.
    lambda: ('{"S": "café"}', {('S', ): 'café'}),
    # But if that fails, the implementation
    # must automatically retry with latin-1.
    lambda: ('{"S": "café"}'.encode('latin-1'), {('S', ): 'café'}),
    # Invalid JSON.
    lambda: ('{"foo", "bar",}', ValueError),
    # Invalid JSON.
    lambda: ('foo', ValueError),
    # Cannot convert to dict.
    lambda: ('"foo"', ValueError),
    # Ditto.
    lambda: ('4.2', TypeError),
)

@parametrize(LOAD_TESTS)
def test_load_dictionary(contents, expected):
    if isinstance(contents, str):
        contents = contents.encode('utf-8')
    with make_dict(contents) as filename:
        if inspect.isclass(expected):
            with pytest.raises(expected):
                JsonDictionary.load(filename)
        else:
            d = JsonDictionary.load(filename)
            assert dict(d.items()) == expected


SAVE_TESTS = (
    # Simple test.
    lambda: ({('S', ): 'a'},
             '{\n"S": "a"\n}\n'),
    # Check strokes format: '/' separated.
    lambda: ({('SAPL', '-PL'): 'sample'},
             '{\n"SAPL/-PL": "sample"\n}\n'),
    # Contents should be saved as UTF-8, no escaping.
    lambda: ({('S', ): 'café'},
             '{\n"S": "café"\n}\n'),
    # Check escaping of special characters.
    lambda: ({('S', ): '{^"\n\t"^}'},
             '{\n"S": "' + r'{^\"\n\t\"^}' + '"\n}\n'),
    # Keys are sorted on save.
    lambda: ({('B', ): 'bravo', ('A', ): 'alpha', ('C', ): 'charlie'},
             '{\n"A": "alpha",\n"B": "bravo",\n"C": "charlie"\n}\n'),
)

@parametrize(SAVE_TESTS)
def test_save_dictionary(contents, expected):
    with make_dict(b'foo') as filename:
        d = JsonDictionary.create(filename)
        d.update(contents)
        d.save()
        with open(filename, 'rb') as fp:
            contents = fp.read().decode('utf-8')
        assert contents == expected
