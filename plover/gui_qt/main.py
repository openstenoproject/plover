# Python 2/3 compatibility.
from __future__ import print_function

import locale
import sys
import signal

from PyQt5.QtCore import (
    QCoreApplication,
    QLibraryInfo,
    QTimer,
    QTranslator,
    Qt,
)
from PyQt5.QtWidgets import QApplication, QMessageBox

from plover import log
from plover import __name__ as __software_name__
from plover import __version__
from plover.oslayer.keyboardcontrol import KeyboardEmulation

from plover.gui_qt.engine import Engine
from plover.gui_qt.i18n import get_language, install_gettext


class Application(object):

    def __init__(self, config, use_qt_notifications):

        # This is done dynamically so localization
        # support can be configure beforehand.
        from plover.gui_qt.main_window import MainWindow

        self._app = None
        self._win = None
        self._engine = None
        self._translator = None

        QCoreApplication.setApplicationName(__software_name__.capitalize())
        QCoreApplication.setApplicationVersion(__version__)
        QCoreApplication.setOrganizationName('Open Steno Project')
        QCoreApplication.setOrganizationDomain('openstenoproject.org')

        self._app = QApplication([])
        self._app.setAttribute(Qt.AA_UseHighDpiPixmaps)

        # Enable localization of standard Qt controls.
        self._translator = QTranslator()
        translations_dir = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
        self._translator.load('qtbase_' + get_language(), translations_dir)
        self._app.installTranslator(self._translator)
        locale.setlocale(locale.LC_ALL, 'en_US')

        QApplication.setQuitOnLastWindowClosed(False)

        signal.signal(signal.SIGINT, lambda signum, stack: QCoreApplication.quit())

        # Make sure the Python interpreter runs at least every second,
        # so signals have a chance to be processed.
        self._timer = QTimer()
        self._timer.timeout.connect(lambda: None)
        self._timer.start(1000)

        self._engine = Engine(config, KeyboardEmulation())

        self._win = MainWindow(self._engine, use_qt_notifications)

        self._app.aboutToQuit.connect(self._win.on_quit)

    def __del__(self):
        del self._win
        del self._app
        del self._engine
        del self._translator

    def run(self):
        self._app.exec_()
        self._engine.quit()
        self._engine.wait()


def show_error(title, message):
    print('%s: %s' % (title, message))
    app = QApplication([])
    QMessageBox.critical(None, title, message)
    del app


def main(config):

    use_qt_notifications = True
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
            use_qt_notifications = False

    # Setup internationalization support.
    install_gettext()

    app = Application(config, use_qt_notifications)
    app.run()
    del app

    return 0
