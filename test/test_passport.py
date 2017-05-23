# Copyright (c) 2011 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for passport.py."""

import time
import unittest

from mock import patch

from plover.machine.passport import Passport


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
        result = self._get()
        MockSerial.index += 1
        return result
        
    def close(self):
        pass


class TestCase(unittest.TestCase):
    def test_passport(self):
        
        def p(s):
            return b'<123/' + s + b'/something>'
        
        cases = (
            # Test all keys
            ((b'!f#f+f*fAfCfBfEfDfGfFfHfKfLfOfNfQfPfSfRfUfTfWfYfXfZf^f~f',),
            [set(Passport.get_keys()),]),
            # Anything below 8 is not registered
            ((b'S9T8A7',), [['S', 'T'],]),
            # Sequence of strokes
            ((b'SfTf', b'Zf', b'QfLf'), [['S', 'T'], ['Z',], ['Q', 'L']]),
        )

        params = {k: v[0] for k, v in Passport.get_option_info().items()}
        with patch('plover.machine.base.serial.Serial', MockSerial) as mock:
            for inputs, expected in cases:
                mock.inputs = list(map(p, inputs))
                actual = []
                m = Passport(params)
                m.add_stroke_callback(actual.append)
                m.start_capture()
                while mock.index < len(mock.inputs):
                    time.sleep(0.00001)
                m.stop_capture()
                self.assertEqual(len(actual), len(expected))
                for actual_keys, expected_keys in zip(actual, expected):
                    self.assertCountEqual(actual_keys, expected_keys)
