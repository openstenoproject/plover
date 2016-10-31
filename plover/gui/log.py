import sys
from plover import log


handler_class = handler = None

try:
    if sys.platform.startswith('linux'):
        from plover.oslayer.log_dbus import DbusNotificationHandler
        handler_class = DbusNotificationHandler
    elif sys.platform.startswith('darwin'):
        from plover.oslayer.log_osx import OSXNotificationHandler
        handler_class = OSXNotificationHandler
except Exception:
    log.warning('could not import platform gui log', exc_info=True)
else:
    try:
        handler = handler_class()
    except Exception:
        log.error('could not initialize platform gui log', exc_info=True)

if handler is None:
    from plover.gui.log_wx import WxNotificationHandler
    handler = WxNotificationHandler()

log.add_handler(handler)
