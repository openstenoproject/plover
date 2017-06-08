# Copyright (c) 2017 Thomas Thurman
# See LICENSE.txt for details.

import os
import codecs
import unittest

EXPECTED = {
    ('U', 'SURP'): 'usurp',
    ('U', 'SKWRA*EU', 'AES'): "you Jay's",
    ('U', 'SPHAOEPB'): 'you mean so',
    ('U', 'SRA*E'): 'you have a',
    ('U', 'SRA*U'): 'you have a',
    ('U', 'STAEUGS'): 'eustachian',
    ('U', 'STRAOEUF', 'TO'): 'you strive to',
    ('U', 'SURP'): 'usurp',
    ('U', 'TKPWAOEUGS'): 'you guys',
    ('U', 'TKROUS', 'KWREU'): 'you drowsy',
    ('UD',): "you'd",
    ('UD', '*ER'): 'udder',
    ('UD', 'EL'): 'Udell',
    ('UD', 'ER'): 'udder',
    ('UD', 'ERS'): 'udders',
    ('UZ', 'PWEBG', 'STAPB'): 'Uzbekistan',
}

from plover.dictionary.eclipse_dict import EclipseDictionary

class TestCase(unittest.TestCase):

    def test_load_dictionary(self):

        filename = 'test/eclipse-test.dix'
        d = EclipseDictionary.load(filename)
        self.assertEqual(dict(d.items()), EXPECTED)
