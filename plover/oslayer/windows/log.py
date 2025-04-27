from plyer import notification
import logging
import sys
import os

from plover import log, __name__ as __software_name__
from plover.oslayer.config import ASSETS_DIR

APPNAME = __software_name__.capitalize()
APPICON = os.path.join(ASSETS_DIR, 'plover.ico')


class NotificationHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.setLevel(log.WARNING)
        self.setFormatter(log.NoExceptionTracebackFormatter('%(levelname)s: %(message)s'))

    def handle(self, record):
        level = record.levelno
        message = self.format(record)
        if message.endswith('\n'):
            message = message[:-1]
        if level <= log.INFO:
            timeout = 10
        elif level <= log.WARNING:
            timeout = 15
        else:
            timeout = 60
        notification.notify(
            app_name=APPNAME,
            app_icon=APPICON,
            title=APPNAME,
            message=message,
            timeout=timeout,
        )
