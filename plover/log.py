# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""A module to handle logging."""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from logging import DEBUG, INFO, WARNING, ERROR
from plover.oslayer.config import CONFIG_DIR

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
LOG_FILENAME = os.path.join(CONFIG_DIR, 'plover.log')
LOG_MAX_BYTES = 10000000
LOG_COUNT = 9

STROKE_LOG_FORMAT = '%(asctime)s %(message)s'

class FileHandler(RotatingFileHandler):

    def __init__(self, filename=LOG_FILENAME, format=LOG_FORMAT):
        super(FileHandler, self).__init__(filename,
                                          maxBytes=LOG_MAX_BYTES,
                                          backupCount=LOG_COUNT)
        self.setFormatter(logging.Formatter(format))


class PrintHandler(logging.StreamHandler):
    """ Handler using L{print_} to output messages. """

    def __init__(self, format=LOG_FORMAT):
        super(PrintHandler, self).__init__(sys.stderr)
        self.setFormatter(logging.Formatter(format))


class Logger(object):

    def __init__(self):
        self._print_handler = PrintHandler()
        self._print_handler.setLevel(WARNING)
        self._file_handler = FileHandler()
        self._file_handler.setLevel(INFO)
        self._logger = logging.getLogger('plover')
        self._logger.addHandler(self._print_handler)
        self._logger.addHandler(self._file_handler)
        self._logger.setLevel(INFO)
        self._stroke_logger = logging.getLogger('plover-strokes')
        self._stroke_logger.setLevel(INFO)
        self._stroke_handler = None
        self._log_strokes = False
        self._log_translations = False

    def set_stroke_filename(self, filename=None):
        self.info('set_stroke_filename(%s)', filename)
        if self._stroke_handler is not None:
            self._stroke_logger.removeHandler(self._stroke_handler)
            self._stroke_handler = None
        if filename is None:
            return
        assert filename != LOG_FILENAME
        filename = os.path.abspath(filename)
        self._stroke_handler = FileHandler(filename=filename,
                                           format=STROKE_LOG_FORMAT)
        self._stroke_logger.addHandler(self._stroke_handler)

    def enable_stroke_logging(self, b):
        self.info('enable_stroke_logging(%s)', b)
        self._log_strokes = b

    def enable_translation_logging(self, b):
        self.info('enable_translation_logging(%s)', b)
        self._log_translations = b

    def log_stroke(self, steno_keys):
        if not self._log_strokes or self._stroke_handler is None:
            return
        self._stroke_logger.info('Stroke(%s)' % ' '.join(steno_keys))

    def log_translation(self, undo, do, prev):
        if not self._log_strokes or self._stroke_handler is None:
            return
        # TODO: Figure out what to actually log here.
        for u in undo:
            self._stroke_logger.info('*%s', u)
        for d in do:
            self._stroke_logger.info(d)

    # Delegate calls to _logger.
    def __getattr__(self, name):
        return getattr(self._logger, name)


# Set up default logger.
__logger = Logger()

# The following functions direct all input to __logger.
debug = __logger.debug
info = __logger.info
warning = __logger.warning
error = __logger.error
set_level = __logger.setLevel
add_handler = __logger.addHandler
remove_handler = __logger.removeHandler
# Strokes/translation logging.
set_stroke_filename = __logger.set_stroke_filename
stroke = __logger.log_stroke
translation = __logger.log_translation
enable_stroke_logging = __logger.enable_stroke_logging
enable_translation_logging = __logger.enable_translation_logging

