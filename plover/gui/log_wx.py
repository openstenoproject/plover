
from plover import log, __name__ as __software_name__
import logging
import wx


def _notify(level, message):
    nm = wx.NotificationMessage()
    nm.SetTitle(__software_name__.capitalize())
    nm.SetMessage(message)
    if level <= log.INFO:
        flags = wx.ICON_INFORMATION
    elif level <= log.WARNING:
        flags = wx.ICON_WARNING
    else:
        flags = wx.ICON_ERROR
    nm.SetFlags(flags)
    nm.Show()

class WxNotificationHandler(logging.Handler):
    """ Handler using wx.NotificationMessage to show messages. """

    def __init__(self):
        super(WxNotificationHandler, self).__init__()
        self.setLevel(log.WARNING)
        self.setFormatter(log.NoExceptionTracebackFormatter('%(levelname)s: %(message)s'))

    def emit(self, record):
        level = record.levelno
        message = self.format(record)
        wx.CallAfter(_notify, level, message)

