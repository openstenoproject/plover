# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for steno.py."""

import unittest
from steno import normalize_steno, Stroke

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
        )
        
        for arg, expected in cases:
            self.assertEqual('/'.join(normalize_steno(arg)), expected)
            
    def test_steno(self):
        self.assertEqual(Stroke(['S-']).rtfcre, 'S')
        self.assertEqual(Stroke(['S-', 'T-']).rtfcre, 'ST')
        self.assertEqual(Stroke(['T-', 'S-']).rtfcre, 'ST')
        self.assertEqual(Stroke(['-P', '-P']).rtfcre, '-P')
        self.assertEqual(Stroke(['-P', 'X-']).rtfcre, 'X-P')

if __name__ == '__main__':
    unittest.main()