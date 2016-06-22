# Copyright (c) 2011 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for passport.py."""

from operator import eq
from itertools import starmap
import time
import unittest

from mock import patch

from plover.machine.passport import Passport
from plover import system


class MockSerial(object):
    
    inputs = []
    index = 0
    
    def __init__(self, **params):
      MockSerial.index = 0

    def isOpen(self):
        return True

    def _get(self):
        if len(MockSerial.inputs) > MockSerial.index:
            return MockSerial.inputs[MockSerial.index]
        return ''

    def inWaiting(self):
        return len(self._get())

    def read(self, size=1):
        assert size == self.inWaiting()
        result = [ord(x) for x in self._get()]
        MockSerial.index += 1
        return result
        
    def close(self):
        pass


def cmp_keys(a, b):
    return all(starmap(eq, zip(a, b)))

class TestCase(unittest.TestCase):
    def test_passport(self):
        
        def p(s):
            return '<123/%s/something>' % s
        
        cases = (
            # Test all keys
            (('!f#f+f*fAfCfBfEfDfGfFfHfKfLfOfNfQfPfSfRfUfTfWfYfXfZf^f~f',),
            [['#', '*', 'A-', 'S-', '-B', '-E', '-D', '-G', '-F', 'H-', 'K-', 
              '-L', 'O-', '-P', '-R', 'P-', 'S-', 'R-', '-U', 'T-', 'W-', '-T', 
              '-S', '-Z', '*'],]),
            # Anything below 8 is not registered
            (('S9T8A7',), [['S-', 'T-'],]),
            # Sequence of strokes
            (('SfTf', 'Zf', 'QfLf'), [['S-', 'T-'], ['-Z',], ['-R', '-L']]),
        )

        params = {k: v[0] for k, v in Passport.get_option_info().items()}
        with patch('plover.machine.base.serial.Serial', MockSerial) as mock:
            for inputs, expected in cases:
                mock.inputs = list(map(p, inputs))
                actual = []
                m = Passport(params)
                m.add_stroke_callback(actual.append)
                m.set_mappings(system.KEYMAPS['Passport'])
                m.start_capture()
                while mock.index < len(mock.inputs):
                    time.sleep(0.00001)
                m.stop_capture()
                self.assertEqual(actual, expected)
