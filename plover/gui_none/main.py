# Python 2/3 compatibility.
from __future__ import print_function

import sys
from threading import Event

from plover import log
from plover.oslayer.keyboardcontrol import KeyboardEmulation

from plover.gui_none.engine import Engine


def show_error(title, message):
    print('%s: %s' % (title, message))


def main(config):

    handler_class = None
    try:
        if sys.platform.startswith('linux'):
            from plover.oslayer.log_dbus import DbusNotificationHandler
            handler_class = DbusNotificationHandler
        elif sys.platform.startswith('darwin'):
            from plover.oslayer.log_osx import OSXNotificationHandler
            handler_class = OSXNotificationHandler
    except Exception:
        log.info('could not import platform gui log', exc_info=True)
    if handler_class is not None:
        try:
            handler = handler_class()
        except Exception:
            log.info('could not initialize platform gui log', exc_info=True)
        else:
            log.add_handler(handler)

    engine = Engine(config, KeyboardEmulation())
    if not engine.load_config():
        return 3
    quitting = Event()
    engine.hook_connect('quit', quitting.set)
    engine.start()
    try:
        quitting.wait()
    except KeyboardInterrupt:
        pass
    engine.quit()
    engine.join()

    return 0
