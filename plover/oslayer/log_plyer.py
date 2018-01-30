import os
import sys
import logging

from plyer import notification

from plover import log, __name__ as __software_name__
from plover.oslayer.config import ASSETS_DIR


APPNAME = __software_name__.capitalize()

if sys.platform.startswith('win32'):
    APPICON = os.path.join(ASSETS_DIR, 'plover.ico')
else:
    APPICON = os.path.join(ASSETS_DIR, 'plover_32x32.png')


class PlyerNotificationHandler(logging.Handler):
    """ Handler using Plyer's notifications to show messages. """

    def __init__(self):
        super().__init__()
        self.setLevel(log.WARNING)
        self.setFormatter(log.NoExceptionTracebackFormatter('%(levelname)s: %(message)s'))

    def emit(self, record):
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
