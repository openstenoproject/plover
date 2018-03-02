
import logging

from PyQt5.QtCore import QObject, pyqtSignal

from plover import log


class NotificationHandler(QObject, logging.Handler):

    emitSignal = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.setLevel(log.WARNING)
        self.setFormatter(log.NoExceptionTracebackFormatter('%(levelname)s: %(message)s'))

    def emit(self, record):
        level = record.levelno
        message = self.format(record)
        self.emitSignal.emit(level, message)
