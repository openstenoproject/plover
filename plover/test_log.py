# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import unittest
from mock import patch
from logging import Handler
from collections import defaultdict
from plover import log

class FakeHandler(Handler):
    
    outputs = defaultdict(list)
    
    def __init__(self, filename, format=log.STROKE_LOG_FORMAT):
        Handler.__init__(self)
        self.filename = filename
        
    def emit(self, record):
        FakeHandler.outputs[self.filename].append(record.getMessage())
        
    @staticmethod
    def get_output():
        d = dict(FakeHandler.outputs)
        FakeHandler.outputs.clear()
        return d

class LoggerTestCase(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('plover.log.FileHandler', FakeHandler)
        self.patcher.start()
        self.logger = log
            
    def tearDown(self):
        self.logger.set_stroke_filename(None)
        self.patcher.stop()

    def test_set_filename(self):
        self.logger.set_stroke_filename('/fn1')
        self.logger.enable_stroke_logging(True)
        self.logger.stroke(('S',))
        self.logger.set_stroke_filename('/fn2')
        self.logger.stroke(('T',))
        self.logger.set_stroke_filename(None)
        self.logger.stroke(('P',))
        self.assertEqual(FakeHandler.get_output(), {'/fn1': ['Stroke(S)'], 
                                                    '/fn2': ['Stroke(T)']})

    def test_stroke(self):
        self.logger.set_stroke_filename('/fn')
        self.logger.enable_stroke_logging(True)
        self.logger.stroke(('ST', 'T'))
        self.assertEqual(FakeHandler.get_output(), {'/fn': ['Stroke(ST T)']})

    def test_log_translation(self):
        self.logger.set_stroke_filename('/fn')
        self.logger.enable_translation_logging(True)
        self.logger.translation(['a', 'b'], ['c', 'd'], None)
        self.assertEqual(FakeHandler.get_output(), 
                        {'/fn': ['*a', '*b', 'c', 'd']})

    def test_enable_stroke_logging(self):
        self.logger.set_stroke_filename('/fn')
        self.logger.stroke(('a',))
        self.logger.enable_stroke_logging(True)
        self.logger.stroke(('b',))
        self.logger.enable_stroke_logging(False)
        self.logger.stroke(('c',))
        self.assertEqual(FakeHandler.get_output(), {'/fn': ['Stroke(b)']})

    def test_enable_translation_logging(self):
        self.logger.set_stroke_filename('/fn')
        self.logger.translation(['a'], ['b'], None)
        self.logger.enable_translation_logging(True)
        self.logger.translation(['c'], ['d'], None)
        self.logger.enable_translation_logging(False)
        self.logger.translation(['e'], ['f'], None)
        self.assertEqual(FakeHandler.get_output(), {'/fn': ['*c', 'd']})

if __name__ == '__main__':
    unittest.main()
