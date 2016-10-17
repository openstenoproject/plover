# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for steno.py."""
import re
import unittest

from plover.steno import (
    filter_entry,
    normalize_steno,
    Stroke,
    normalized_stroke_to_indexes,
    normalized_steno_to_indexes,
    normalize_stroke,
)


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

    def test_stroke_to_indexes(self):
        cases = (
            ('STPH', (1, 2, 4, 6,)),
            ('#', (0,)),
            ('-T', (19,)),
            ('STPHA*T', (1, 2, 4, 6, 8, 10, 19,)),
            ('WUZ', (5, 12, 22,)),
            ('#KW*', (0, 3, 5, 10,)),
            ('#-Z', (0, 22,)),
            ('12K3W*', (1, 2, 3, 4, 5, 10,)),
            ('ED', (11, 21,)),
            ('*ED', (10, 11, 21,)),
            ('-Z', (22,)),
            ('-F', (13,)),
            ('-U', (12,)),
            ('A-', (8,)),
            ('*', (10,)),
            ('-FZ', (13, 22,)),
            ('S*EUPL', (1, 10, 11, 12, 15, 17,)),
            ('TPA*EUPBGS', (2, 4, 8, 10, 11, 12, 15, 16, 18, 20,)),
            ('AFPL', (8, 13, 15, 17,)),
            ('URPBLG', (12, 14, 15, 16, 17, 18,)),
            ('*US', (10, 12, 20,)),
            ('EUF', (11, 12, 13,)),
            ('HRAU', (6, 7, 8, 12,)),
            ('HRAR', (6, 7, 8, 14,)),
            ('S', (1,)),
            ('-S', (20,)),
            ('S-', (1,)),
            ('R', (7,)),
            ('-R', (14,)),
            ('R-', (7,))
        )
        for stroke, indexes in cases:
            self.assertEqual(indexes, normalized_stroke_to_indexes(normalize_stroke(stroke)))

    def test_steno_to_indexes(self):
        cases = (
                ('S', ((1,),)),
                ('12K3W*/WUZ/STPH/AFPL/*US', ((1, 2, 3, 4, 5, 10), (5, 12, 22), (1, 2, 4, 6,), (8, 13, 15, 17,), (10, 12, 20,),)),
                ('', ((),))
        )
        for steno, indexes in cases:
            self.assertEqual(indexes, normalized_steno_to_indexes(normalize_steno(steno)))

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
            ('TKOG',), 'dog', strokes_filter='/KOG'
        ))
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', strokes_filter='KOG'
        ))
        # Must contain all of the filter
        self.assertFalse(filter_entry(
            ('TKOG',), 'dog', strokes_filter='TKOGS'
        ))
        # Boundaries count as beginning / endings
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', strokes_filter='TKOG/'
        ))
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', strokes_filter='/TKOG/'
        ))
        self.assertTrue(filter_entry(
            ('TKOG',), 'dog', strokes_filter='/TKOG'
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

        # Trailing slash.
        self.assertTrue(filter_entry(
            ('TKOG', 'S',), 'dogs', strokes_filter='TKOG/'
        ))
        self.assertTrue(filter_entry(
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
