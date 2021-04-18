import objc
NSUserNotification = objc.lookUpClass('NSUserNotification')
NSUserNotificationCenter = objc.lookUpClass('NSUserNotificationCenter')
NSObject = objc.lookUpClass('NSObject')

from plover import log, __name__ as __software_name__
import logging


class OSXNotificationHandler(logging.Handler):
    """ Handler using OS X Notification Center to show messages. """

    def __init__(self):
        super().__init__()
        self.setLevel(log.WARNING)
        self.setFormatter(log.NoExceptionTracebackFormatter('%(message)s'))

    def emit(self, record):
        # Notification Center has no levels or timeouts.
        notification = NSUserNotification.alloc().init()

        notification.setTitle_(record.levelname.title())
        notification.setInformativeText_(self.format(record))

        ns = NSUserNotificationCenter.defaultUserNotificationCenter()
        ns.setDelegate_(always_present_delegator)
        ns.deliverNotification_(notification)


class AlwaysPresentNSDelegator(NSObject):
    """
    Custom delegator to force presenting even if Plover is in the foreground.
    """
    def userNotificationCenter_didActivateNotification_(self, ns, note):
        # Do nothing
        return

    def userNotificationCenter_shouldPresentNotification_(self, ns, note):
        # Force notification, even if frontmost application.
        return True

always_present_delegator = AlwaysPresentNSDelegator.alloc().init()
