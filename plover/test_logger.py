# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import unittest
from mock import patch
from logging import Handler
from collections import defaultdict
from plover.logger import Logger

class FakeHandler(Handler):
    
    outputs = defaultdict(list)
    
    def __init__(self, filename, maxBytes=0, backupCount=0):
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
        self.patcher = patch('plover.logger.RotatingFileHandler', FakeHandler)
        self.patcher.start()
        self.logger = Logger()
            
    def tearDown(self):
        self.logger.set_filename(None)
        self.patcher.stop()

    def test_set_filename(self):
        self.logger.set_filename('fn1')
        self.logger.enable_stroke_logging(True)
        self.logger.log_stroke(('S',))
        self.logger.set_filename('fn2')
        self.logger.log_stroke(('T',))
        self.logger.set_filename(None)
        self.logger.log_stroke(('P',))
        self.assertEqual(FakeHandler.get_output(), {'fn1': ['Stroke(S)'], 
                                                    'fn2': ['Stroke(T)']})

    def test_log_stroke(self):
        self.logger.set_filename('fn')
        self.logger.enable_stroke_logging(True)
        self.logger.log_stroke(('ST', 'T'))
        self.assertEqual(FakeHandler.get_output(), {'fn': ['Stroke(ST T)']})

    def test_log_translation(self):
        self.logger.set_filename('fn')
        self.logger.enable_translation_logging(True)
        self.logger.log_translation(['a', 'b'], ['c', 'd'], None)
        self.assertEqual(FakeHandler.get_output(), 
                        {'fn': ['*a', '*b', 'c', 'd']})

    def test_enable_stroke_logging(self):
        self.logger.set_filename('fn')
        self.logger.log_stroke(('a',))
        self.logger.enable_stroke_logging(True)
        self.logger.log_stroke(('b',))
        self.logger.enable_stroke_logging(False)
        self.logger.log_stroke(('c',))
        self.assertEqual(FakeHandler.get_output(), {'fn': ['Stroke(b)']})

    def test_enable_translation_logging(self):
        self.logger.set_filename('fn')
        self.logger.log_translation(['a'], ['b'], None)
        self.logger.enable_translation_logging(True)
        self.logger.log_translation(['c'], ['d'], None)
        self.logger.enable_translation_logging(False)
        self.logger.log_translation(['e'], ['f'], None)
        self.assertEqual(FakeHandler.get_output(), {'fn': ['*c', 'd']})

if __name__ == '__main__':
    unittest.main()