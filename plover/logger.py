# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""A module to handle logging."""

import logging
from logging.handlers import RotatingFileHandler

LOGGER_NAME = 'plover_logger'
LOG_FORMAT = '%(asctime)s %(message)s'
LOG_MAX_BYTES = 10000000
LOG_COUNT = 9

class Logger(object):
    def __init__(self):
        self._logger = logging.getLogger(LOGGER_NAME)
        self._logger.setLevel(logging.DEBUG)
        self._handler = None
        self._log_strokes = False
        self._log_translations = False

    def set_filename(self, filename):
        if self._handler:
            self._logger.removeHandler(self._handler)
        handler = None
        if filename:
            handler = RotatingFileHandler(filename, maxBytes=LOG_MAX_BYTES,
                                          backupCount=LOG_COUNT,)
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            self._logger.addHandler(handler)
        self._handler = handler

    def enable_stroke_logging(self, b):
        self._log_strokes = b

    def enable_translation_logging(self, b):
        self._log_translations = b

    def log_stroke(self, steno_keys):
        if self._log_strokes and self._handler:
            self._logger.info('Stroke(%s)' % ' '.join(steno_keys))

    def log_translation(self, undo, do, prev):
        if self._log_translations and self._handler:
            # TODO: Figure out what to actually log here.
            for u in undo:
                self._logger.info('*%s', u)
            for d in do:
                self._logger.info(d)
