
import os
import logging

import dbus

from plover import log, __name__ as __software_name__
from plover.oslayer.config import ASSETS_DIR


APPNAME = __software_name__.capitalize()
APPICON = os.path.join(ASSETS_DIR, 'plover.png')
SERVICE = 'org.freedesktop.Notifications'
INTERFACE = '/org/freedesktop/Notifications'


class DbusNotificationHandler(logging.Handler):
    """ Handler using DBus notifications to show messages. """

    def __init__(self):
        super().__init__()
        self._bus = dbus.SessionBus()
        self._proxy = self._bus.get_object(SERVICE, INTERFACE)
        self._notify = dbus.Interface(self._proxy, SERVICE)
        self.setLevel(log.WARNING)
        self.setFormatter(log.NoExceptionTracebackFormatter('<b>%(levelname)s:</b> %(message)s'))

    def emit(self, record):
        level = record.levelno
        message = self.format(record)
        if message.endswith('\n'):
            message = message[:-1]
        if level <= log.INFO:
            timeout = 10
            urgency = 0
        elif level <= log.WARNING:
            timeout = 15
            urgency = 1
        else:
            timeout = 0
            urgency = 2
        self._notify.Notify(APPNAME, 0, APPICON,  # app_name, replaces_id, app_icon
                            APPNAME, message, '', # actions
                            { 'urgency': dbus.Byte(urgency) },
                            timeout * 1000)

