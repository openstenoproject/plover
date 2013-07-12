# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for steno.py."""

import unittest
from steno import normalize_steno

class StenoTestCase(unittest.TestCase):
    def test_normalize_steno(self):
        cases = (
        
        # TODO: More cases
        ('S', 'S'),
        ('S-', 'S'),
        ('-S', '-S'),
        ('ES', 'ES'),
        ('-ES', 'ES')
        
        )
        
        for arg, expected in cases:
            self.assertEqual('/'.join(normalize_steno(arg)), expected)

if __name__ == '__main__':
    unittest.main()