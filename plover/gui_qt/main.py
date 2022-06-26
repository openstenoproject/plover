from pathlib import Path
import signal
import sys

from qtpy.QtCore import (
    QCoreApplication,
    QDir,
    QLibraryInfo,
    QTimer,
    QTranslator,
    Qt,
)
from qtpy.QtWidgets import QApplication, QMessageBox
from qtpy import API as QT_API

from plover import _, __name__ as __software_name__, __version__, log
from plover.oslayer.keyboardcontrol import KeyboardEmulation

from plover.gui_qt.engine import Engine
from plover.gui_qt.utils import obj_exec


# Disable pyqtRemoveInputHook to avoid getting
# spammed when using the debugger.
if QT_API.startswith('pyqt'):
    from qtpy.QtCore import pyqtRemoveInputHook
    pyqtRemoveInputHook()


# Setup access to resources.
QDir.addSearchPath('plover', str(Path(__file__).parent / 'resources'))


class Application:

    def __init__(self, config, controller, use_qt_notifications):

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

        self._app = QApplication([sys.argv[0], '-name', 'plover'])
        # Not available on Qt6.
        attr = getattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps', None)
        if attr is not None:
            self._app.setAttribute(attr)

        # Enable localization of standard Qt controls.
        log.info('setting language to: %s', _.lang)
        self._translator = QTranslator()
        if hasattr(QLibraryInfo, 'LibraryPath'):
            # Qt6.
            translations_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        else:
            # Qt5.
            translations_dir = QLibraryInfo.location(QLibraryInfo.LibraryLocation.TranslationsPath)
        self._translator.load('qtbase_' + _.lang, translations_dir)
        self._app.installTranslator(self._translator)

        QApplication.setQuitOnLastWindowClosed(False)

        self._app.engine = self._engine = Engine(config, controller, KeyboardEmulation())
        # On macOS, quitting through the dock will result
        # in a direct call to `QCoreApplication.quit`.
        self._app.aboutToQuit.connect(self._app.engine.quit)

        signal.signal(signal.SIGINT, lambda signum, stack: self._engine.quit())

        # Make sure the Python interpreter runs at least every second,
        # so signals have a chance to be processed.
        self._timer = QTimer()
        self._timer.timeout.connect(lambda: None)
        self._timer.start(1000)

        self._win = MainWindow(self._engine, use_qt_notifications)

    def __del__(self):
        del self._win
        del self._app
        del self._engine
        del self._translator

    def run(self):
        obj_exec(self._app)
        return self._engine.join()


def show_error(title, message):
    print('%s: %s' % (title, message))
    app = QApplication([])
    QMessageBox.critical(None, title, message)
    del app


def default_excepthook(*exc_info):
    log.error('Qt GUI error', exc_info=exc_info)


def main(config, controller):
    log.info('using the `%s` API', QT_API)
    # Setup internationalization support.
    use_qt_notifications = not log.has_platform_handler()
    # Log GUI exceptions that make it back to the event loop.
    if sys.excepthook is sys.__excepthook__:
        sys.excepthook = default_excepthook
    app = Application(config, controller, use_qt_notifications)
    code = app.run()
    del app
    return code
