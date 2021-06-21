# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for steno.py."""

import inspect

import pytest

from plover.steno import normalize_steno, Stroke

from plover_build_utils.testing import parametrize


NORMALIZE_TESTS = (
    # TODO: More cases
    lambda: ('S', ('S',)),
    lambda: ('S-', ('S',)),
    lambda: ('-S', ('-S',)),
    lambda: ('ES', ('ES',)),
    lambda: ('-ES', ('ES',)),
    lambda: ('TW-EPBL', ('TWEPBL',)),
    lambda: ('TWEPBL', ('TWEPBL',)),
    lambda: ('RR', ('R-R',)),
    lambda: ('19', ('1-9',)),
    lambda: ('14', ('14',)),
    lambda: ('146', ('14-6',)),
    lambda: ('67', ('-67',)),
    lambda: ('120-7', ('1207',)),
    lambda: ('6', ('-6',)),
    lambda: ('9', ('-9',)),
    lambda: ('5', ('5',)),
    lambda: ('0', ('0',)),
    lambda: ('456', ('456',)),
    lambda: ('46', ('4-6',)),
    lambda: ('4*6', ('4*6',)),
    lambda: ('456', ('456',)),
    lambda: ('S46', ('14-6',)),
    lambda: ('T-EFT/-G', ('TEFT', '-G')),
    lambda: ('T-EFT/G', ('TEFT', '-G')),
    lambda: ('/PRE', ('', 'PRE')),
    lambda: ('S--T', ('S-T',)),
    # Number key.
    lambda: ('#', ('#',)),
    lambda: ('#S', ('1',)),
    lambda: ('#A', ('5',)),
    lambda: ('#0', ('0',)),
    lambda: ('#6', ('-6',)),
    # Implicit hyphens.
    lambda: ('SA-', ('SA',)),
    lambda: ('SA-R', ('SAR',)),
    lambda: ('O', ('O',)),
    lambda: ('O-', ('O',)),
    lambda: ('S*-R', ('S*R',)),
    # Invalid, no strict error checking.
    lambda: ('SRALD/invalid', ('SRALD', 'invalid')),
    lambda: ('SRALD//invalid', ('SRALD', '', 'invalid')),
    lambda: ('S-*R', ('S-*R',)),
    lambda: ('-O-', ('-O-',)),
    lambda: ('-O', ('-O',)),
    # Invalid, with strick error checking.
    lambda: ('SRALD/invalid', ValueError),
    lambda: ('SRALD//invalid', ValueError),
    lambda: ('S-*R', ValueError),
    lambda: ('-O-', ValueError),
    lambda: ('-O', ValueError),
)

@parametrize(NORMALIZE_TESTS)
def test_normalize_steno(steno, expected):
    if inspect.isclass(expected):
        with pytest.raises(expected):
            normalize_steno(steno, strict=True)
        return
    result = normalize_steno(steno)
    msg = 'normalize_steno(%r)=%r != %r' % (
        steno, result, expected,
    )
    assert result == expected, msg


STROKE_TESTS = (
    lambda: (['S-'], (['S-'], 'S')),
    lambda: (['S-', 'T-'], (['S-', 'T-'], 'ST')),
    lambda: (['T-', 'S-'], (['S-', 'T-'], 'ST')),
    lambda: (['-P', '-P'], (['-P'], '-P')),
    lambda: (['#', 'S-', '-T'], (['#', 'S-', '-T'], '1-9')),
    lambda: (['1-', '-9'], (['#', 'S-', '-T'], '1-9')),
    lambda: (['-P', 'X-'], ValueError),
)

@parametrize(STROKE_TESTS)
def test_stroke(keys, expected):
    if inspect.isclass(expected):
        with pytest.raises(expected):
            Stroke(keys)
    else:
        steno_keys, rtfcre = expected
        stroke = Stroke(keys)
        assert stroke.steno_keys == steno_keys
        assert stroke.rtfcre == rtfcre
