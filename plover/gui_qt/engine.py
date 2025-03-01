from PySide6.QtCore import (
    QThread,
    Signal,
)

from plover.engine import StenoEngine
from plover.oslayer.config import PLATFORM


class Engine(StenoEngine, QThread):

    # Signals.
    signal_stroked = Signal(object)
    signal_translated = Signal(object, object)
    signal_machine_state_changed = Signal(str, str)
    signal_output_changed = Signal(bool)
    signal_config_changed = Signal(object)
    signal_dictionaries_loaded = Signal(object)
    signal_send_string = Signal(str)
    signal_send_backspaces = Signal(int)
    signal_send_key_combination = Signal(str)
    signal_add_translation = Signal()
    signal_focus = Signal()
    signal_configure = Signal()
    signal_lookup = Signal()
    signal_suggestions = Signal()
    signal_quit = Signal()

    def __init__(self, config, controller, keyboard_emulation):
        StenoEngine.__init__(self, config, controller, keyboard_emulation)
        QThread.__init__(self)
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

    def join(self):
        QThread.wait(self)
        return self.code

    def run(self):
        if PLATFORM == 'mac':
            import appnope
            appnope.nope()
        super().run()

    def signal_connect(self, name, callback):
        self._signals[name].connect(callback)
