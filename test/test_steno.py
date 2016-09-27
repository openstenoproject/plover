# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for steno.py."""
import re
import unittest

from plover.steno import normalize_steno, Stroke, filter_entry


class StenoTestCase(unittest.TestCase):
    def test_normalize_steno(self):
        cases = (
            # TODO: More cases
            ('S', 'S'),
            ('S-', 'S'),
            ('-S', '-S'),
            ('ES', 'ES'),
            ('-ES', 'ES'),
            ('TW-EPBL', 'TWEPBL'),
            ('TWEPBL', 'TWEPBL'),
            ('19', '1-9'),
            ('14', '14'),
            ('146', '14-6'),
            ('67', '-67'),
            ('6', '-6'),
            ('9', '-9'),
            ('5', '5'),
            ('0', '0'),
            ('456', '456'),
            ('46', '4-6'),
            ('4*6', '4*6'),
            ('456', '456'),
            ('S46', 'S4-6'),
            # Number key.
            ('#S', '#S'),
            ('#A', '#A'),
            ('#0', '0'),
            ('#6', '-6'),
            # Implicit hyphens.
            ('SA-', 'SA'),
            ('SA-R', 'SAR'),
            ('-O', 'O'),
            ('S*-R', 'S*R'),
            ('S-*R', 'S*R'),
        )

        for arg, expected in cases:
            result = '/'.join(normalize_steno(arg))
            msg = 'normalize_steno(%r)=%r != %r' % (
                arg, result, expected,
            )
            self.assertEqual(result, expected, msg=msg)

    def test_steno(self):
        self.assertEqual(Stroke(['S-']).rtfcre, 'S')
        self.assertEqual(Stroke(['S-', 'T-']).rtfcre, 'ST')
        self.assertEqual(Stroke(['T-', 'S-']).rtfcre, 'ST')
        self.assertEqual(Stroke(['-P', '-P']).rtfcre, '-P')
        self.assertEqual(Stroke(['-P', 'X-']).rtfcre, 'X-P')
        self.assertEqual(Stroke(['#', 'S-', '-T']).rtfcre, '1-9')

    def test_filter_by_strokes(self):
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', strokes_filter=''
        ))
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', strokes_filter='T'
        ))
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', strokes_filter='TKOG'
        ))

        # Must start with
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', strokes_filter='KOG'
        ))
        # Must contain all of the filter
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', strokes_filter='TKOGS'
        ))
        # Must contain all strokes (partially)
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', strokes_filter='TKOG/S'
        ))
        self.assertTrue(filter_entry(
            ('TKOG', 'SAEUD'), 'dog said', strokes_filter='TKOG/S'
        ))
        self.assertTrue(filter_entry(
            ('TKOG', 'S',), 'dogs', strokes_filter='TKOG/S'
        ))

        # Can be in a phrase
        self.assertTrue(filter_entry(
            ('URP', 'TPHU', 'KWRORBG', 'STAEUT'),
            'Upper New York State',
            strokes_filter='TPHU/KWRORBG'
        ))

        # Interesting edge case: trailing slash.
        self.assertTrue(filter_entry(
            ('TKOG', 'S',), 'dogs', strokes_filter='TKOG/'
        ))
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', strokes_filter='TKOG/'
        ))

    def test_filter_by_translation_plain(self):
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter=''
        ))
        # Starts with
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter='d'
        ))
        # Contains
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter='o'
        ))
        # Ends with
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter='g'
        ))
        # Whole
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter='dog'
        ))
        # Case insensitive
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter='DOG'
        ))
        # Nothing more
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', translation_filter='dogs'
        ))

    def test_filter_by_translation_case_sensitive(self):
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter='', case_sensitive=True
        ))
        # Starts with
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter='d', case_sensitive=True
        ))
        # Contains
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter='o', case_sensitive=True
        ))
        # Ends with
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter='g', case_sensitive=True
        ))
        # Whole
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', translation_filter='dog', case_sensitive=True
        ))
        # Case sensitive
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', translation_filter='DOG', case_sensitive=True
        ))
        self.assertFalse(filter_entry(
            ('TKOG',), 'DOG', translation_filter='dog', case_sensitive=True
        ))
        # Nothing more
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', translation_filter='dogs', case_sensitive=True
        ))

    def test_filter_by_translation_regex(self):
        # Regex should be None if the checkbox isn't checked.
        def insensitive_regex(translation_filter):
            return re.compile(translation_filter, flags=re.I)

        def sensitive_regex(translation_filter):
            return re.compile(translation_filter)

        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('')
        ))
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('^$')
        ))
        # Starts with
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('^.*$')
        ))
        # Whole
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('^dog$')
        ))
        # Missing whole
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('^do$')
        ))
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('^og$')
        ))
        # Contains
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('d')
        ))
        # Ends with
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('d?g')
        ))
        # Whole
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('d[^0]g')
        ))
        # Case insensitive
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('DOG')
        ))
        # Case sensitive
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', regex=sensitive_regex('DOG')
        ))
        # Nothing more
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', regex=insensitive_regex('dog')
        ))
