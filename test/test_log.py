# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import os
import unittest
from logging import Handler
from collections import defaultdict

from mock import patch

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

    def _stroke_filename(self, path):
        return os.path.abspath(path)

    def test_set_filename(self):
        stroke_filename1 = self._stroke_filename('/fn1')
        self.logger.set_stroke_filename('/fn1')
        self.logger.enable_stroke_logging(True)
        self.logger.stroke(('S-',))
        stroke_filename2 = self._stroke_filename('/fn2')
        self.logger.set_stroke_filename('/fn2')
        self.logger.stroke(('-T',))
        self.logger.set_stroke_filename(None)
        self.logger.stroke(('P-',))
        self.assertEqual(FakeHandler.get_output(),
                         {stroke_filename1: ["Stroke(S : ['S-'])"],
                          stroke_filename2: ["Stroke(-T : ['-T'])"]
                          }
                         )

    def test_stroke(self):
        stroke_filename = self._stroke_filename('/fn')
        self.logger.set_stroke_filename(stroke_filename)
        self.logger.enable_stroke_logging(True)
        self.logger.stroke(('S-', '-T', 'T-'))
        self.logger.stroke(('#', 'S-', '-T'))
        self.assertEqual(FakeHandler.get_output(),
                         {stroke_filename: ["Stroke(ST-T : ['S-', 'T-', '-T'])",
                                            "Stroke(1-9 : ['1-', '-9'])"
                                            ]
                          }
                         )

    def test_log_translation(self):
        stroke_filename = self._stroke_filename('/fn')
        self.logger.set_stroke_filename(stroke_filename)
        self.logger.enable_translation_logging(True)
        self.logger.translation(['a', 'b'], ['c', 'd'], None)
        self.assertEqual(FakeHandler.get_output(), 
                        {stroke_filename: ['*a', '*b', 'c', 'd']})

    def test_enable_stroke_logging(self):
        stroke_filename = self._stroke_filename('/fn')
        self.logger.set_stroke_filename(stroke_filename)
        self.logger.stroke(('S-',))
        self.logger.enable_stroke_logging(True)
        self.logger.stroke(('T-',))
        self.logger.enable_stroke_logging(False)
        self.logger.stroke(('K-',))
        self.assertEqual(FakeHandler.get_output(),
                         {stroke_filename: ["Stroke(T : ['T-'])"]}
                         )

    def test_enable_translation_logging(self):
        stroke_filename = self._stroke_filename('/fn')
        self.logger.set_stroke_filename(stroke_filename)
        self.logger.translation(['a'], ['b'], None)
        self.logger.enable_translation_logging(True)
        self.logger.translation(['c'], ['d'], None)
        self.logger.enable_translation_logging(False)
        self.logger.translation(['e'], ['f'], None)
        self.assertEqual(FakeHandler.get_output(), {stroke_filename: ['*c', 'd']})
