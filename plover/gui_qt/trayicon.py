import sys

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QSystemTrayIcon

from plover import __name__ as __software_name__
from plover import log


class TrayIcon(QObject):

    def __init__(self):
        super(TrayIcon, self).__init__()
        self._supported = QSystemTrayIcon.isSystemTrayAvailable()
        self._context_menu = None
        self._enabled = False
        self._trayicon = None
        self._state_icons = {}
        for state in (
            'disconnected',
            'disabled',
            'enabled',
        ):
            icon = QIcon(':/state-%s.svg' % state)
            if hasattr(icon, 'setIsMask'):
                icon.setIsMask(True)
            self._state_icons[state] = icon
        self._machine = None
        self._machine_state = 'disconnected'
        self._is_running = False
        self._update_state()

    def set_menu(self, menu):
        self._context_menu = menu
        if self._enabled:
            self._trayicon.setContextMenu(menu)

    def log(self, level, message):
        if self._enabled:
            if level <= log.INFO:
                icon = QSystemTrayIcon.Information
                timeout = 10
            elif level <= log.WARNING:
                icon = QSystemTrayIcon.Warning
                timeout = 15
            else:
                icon = QSystemTrayIcon.Critical
                timeout = 25
            self._trayicon.showMessage(__software_name__.capitalize(),
                                       message, icon, timeout * 1000)
        else:
            if level <= log.INFO:
                icon = QMessageBox.Information
            elif level <= log.WARNING:
                icon = QMessageBox.Warning
            else:
                icon = QMessageBox.Critical
            msgbox = QMessageBox()
            msgbox.setText(message)
            msgbox.setIcon(icon)
            msgbox.exec_()

    def is_supported(self):
        return self._supported

    def enable(self):
        if not self._supported:
            return
        self._trayicon = QSystemTrayIcon()
        # On OS X, the context menu is activated with either mouse buttons,
        # and activation messages are still sent, so ignore those...
        if not sys.platform.startswith('darwin'):
            self._trayicon.activated.connect(self._on_activated)
        if self._context_menu is not None:
            self._trayicon.setContextMenu(self._context_menu)
        self._enabled = True
        self._update_state()
        self._trayicon.show()

    def disable(self):
        if not self._enabled:
            return
        self._trayicon.hide()
        self._trayicon = None
        self._enabled = False

    def is_enabled(self):
        return self._enabled

    def update_machine_state(self, machine, state):
        self._machine = machine
        self._machine_state = state
        self._update_state()

    def update_output(self, enabled):
        self._is_running = enabled
        self._update_state()

    clicked = pyqtSignal()

    def _update_state(self):
        if self._machine_state not in ('initializing', 'connected'):
            state = 'disconnected'
        else:
            state = 'enabled' if self._is_running else 'disabled'
        icon = self._state_icons[state]
        if not self._enabled:
            return
        machine_state = _('{machine} is {state}').format(
            machine=_(self._machine),
            state=_(self._machine_state),
        )
        if self._is_running:
            output_state = _('output is enabled')
        else:
            output_state = _('output is disabled')
        self._trayicon.setIcon(icon)
        self._trayicon.setToolTip(
            'Plover:\n- %s\n- %s' % (output_state, machine_state)
        )

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.clicked.emit()
