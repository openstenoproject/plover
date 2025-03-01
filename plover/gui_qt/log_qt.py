import logging

from PySide6.QtCore import QObject, Signal

from plover import log


class NotificationHandler(QObject, logging.Handler):

    emitSignal = Signal(int, str)

    def __init__(self):
        super().__init__()
        self.setLevel(log.WARNING)
        self.setFormatter(log.NoExceptionTracebackFormatter('%(levelname)s: %(message)s'))

    def emit(self, record):
        level = record.levelno
        message = self.format(record)
        print(message)
        #TODO fix this...
        #self.emitSignal.emit(level, message)
