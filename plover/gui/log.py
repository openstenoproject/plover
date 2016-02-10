import sys
from plover import log


handler = None

try:
    if sys.platform.startswith('linux'):
        from plover.gui.log_dbus import DbusNotificationHandler
        handler = DbusNotificationHandler
    elif sys.platform.startswith('darwin'):
        from plover.gui.log_osx import OSXNotificationHandler
        handler = OSXNotificationHandler
except Exception as e:
    log.info('could not import platform gui log', exc_info=e)

if handler is None:
    from plover.gui.log_wx import WxNotificationHandler
    handler = WxNotificationHandler

log.add_handler(handler())
