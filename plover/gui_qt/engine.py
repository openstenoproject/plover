
from PyQt5.QtCore import (
    QCoreApplication,
    QThread,
    QVariant,
    pyqtSignal,
)

from plover.engine import StenoEngine


class Engine(StenoEngine, QThread):

    # Signals.
    signal_stroked = pyqtSignal(QVariant)
    signal_translated = pyqtSignal(QVariant, QVariant)
    signal_machine_state_changed = pyqtSignal(str, str)
    signal_output_changed = pyqtSignal(bool)
    signal_config_changed = pyqtSignal(QVariant)
    signal_send_string = pyqtSignal(str)
    signal_send_backspaces = pyqtSignal(int)
    signal_send_key_combination = pyqtSignal(str)
    signal_add_translation = pyqtSignal()
    signal_focus = pyqtSignal()
    signal_configure = pyqtSignal()
    signal_lookup = pyqtSignal()
    signal_quit = pyqtSignal()

    def __init__(self, config, keyboard_emulation):
        StenoEngine.__init__(self, config, keyboard_emulation)
        QThread.__init__(self)
        self.hook_connect('quit', QCoreApplication.quit)
        self._signals = {}
        for hook in self.HOOKS:
            signal = getattr(self, 'signal_' + hook)
            self.hook_connect(hook, signal.emit)
            self._signals[hook] = signal

    def _in_engine_thread(self):
        return self.currentThread() == self

    def start(self):
        QThread.start(self)
        StenoEngine.start(self)

    def signal_connect(self, name, callback):
        self._signals[name].connect(callback)
