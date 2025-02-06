
from functools import partial
import json
import os
import subprocess

from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QCursor, QIcon, QKeySequence
from PyQt5.QtWidgets import (
    QMainWindow,
    QMenu,
    QApplication,
)

from plover import _, log
from plover.oslayer import wmctrl
from plover.oslayer.config import CONFIG_DIR, PLATFORM
from plover.registry import registry
from plover.resource import resource_filename

from plover.gui_qt.log_qt import NotificationHandler
from plover.gui_qt.main_window_ui import Ui_MainWindow
from plover.gui_qt.config_window import ConfigWindow
from plover.gui_qt.about_dialog import AboutDialog
from plover.gui_qt.trayicon import TrayIcon
from plover.gui_qt.utils import WindowState, find_menu_actions


class MainWindow(QMainWindow, Ui_MainWindow, WindowState):

    ROLE = 'main'

    def __init__(self, engine, use_qt_notifications):
        super().__init__()
        self.setupUi(self)
        if hasattr(self, 'setUnifiedTitleAndToolBarOnMac'):
            self.setUnifiedTitleAndToolBarOnMac(True)
        self._engine = engine
        self._active_dialogs = {}
        self._dialog_class = {
            'about'             : AboutDialog,
            'configuration'     : ConfigWindow,
        }
        all_actions = find_menu_actions(self.menubar)
        # Dictionaries.
        self.dictionaries.add_translation.connect(self._add_translation)
        self.dictionaries.setup(engine)
        # Populate edit menu from dictionaries' own.
        edit_menu = all_actions['menu_Edit'].menu()
        for action in self.dictionaries.edit_menu.actions():
            edit_menu.addAction(action)
        # Tray icon.
        self._trayicon = TrayIcon()
        self._trayicon.enable()
        self._trayicon.clicked.connect(self._engine.toggle_output)
        if use_qt_notifications:
            handler = NotificationHandler()
            handler.emitSignal.connect(self._trayicon.log)
            log.add_handler(handler)
        popup_menu = QMenu()
        for action_name in (
            'action_ToggleOutput',
            'action_Reconnect',
            '',
            'menu_Tools',
            '',
            'action_Configure',
            'action_OpenConfigFolder',
            '',
            'menu_Help',
            '',
            'action_Show',
            'action_Quit',
        ):
            if action_name:
                popup_menu.addAction(all_actions[action_name])
            else:
                popup_menu.addSeparator()
        self._trayicon.set_menu(popup_menu)
        engine.signal_connect('machine_state_changed', self._trayicon.update_machine_state)
        engine.signal_connect('quit', self.on_quit)
        self.action_Quit.triggered.connect(engine.quit)
        # Toolbar popup menu for selecting which tools are shown.
        self.toolbar_menu = QMenu()
        self.toolbar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.toolbar.customContextMenuRequested.connect(
            lambda: self.toolbar_menu.popup(QCursor.pos())
        )
        # Populate tools bar/menu.
        tools_menu = all_actions['menu_Tools'].menu()
        for tool_plugin in registry.list_plugins('gui.qt.tool'):
            tool = tool_plugin.obj
            menu_action = tools_menu.addAction(tool.TITLE)
            if tool.SHORTCUT is not None:
                menu_action.setShortcut(QKeySequence.fromString(tool.SHORTCUT))
            if tool.ICON is not None:
                icon = tool.ICON
                # Internal QT resources start with a `:`.
                if not icon.startswith(':'):
                    icon = resource_filename(icon)
                menu_action.setIcon(QIcon(icon))
            menu_action.triggered.connect(partial(self._activate_dialog, tool_plugin.name, args=()))
            toolbar_action = self.toolbar.addAction(menu_action.icon(), menu_action.text())
            if tool.__doc__ is not None:
                toolbar_action.setToolTip(tool.__doc__)
            toolbar_action.triggered.connect(menu_action.trigger)
            toggle_action = self.toolbar_menu.addAction(menu_action.icon(), menu_action.text())
            toggle_action.setObjectName(tool_plugin.name)
            toggle_action.setCheckable(True)
            toggle_action.setChecked(True)
            toggle_action.toggled.connect(toolbar_action.setVisible)
            self._dialog_class[tool_plugin.name] = tool
        engine.signal_connect('output_changed', self.on_output_changed)
        # Machine.
        for plugin in registry.list_plugins('machine'):
            self.machine_type.addItem(_(plugin.name), plugin.name)
        engine.signal_connect('config_changed', self.on_config_changed)
        engine.signal_connect('machine_state_changed',
            lambda machine, state:
            self.machine_state.setText(state.capitalize())
        )
        self.restore_state()
        # Commands.
        engine.signal_connect('add_translation', partial(self._add_translation, manage_windows=True))
        engine.signal_connect('focus', self._focus)
        engine.signal_connect('configure', partial(self._configure, manage_windows=True))
        engine.signal_connect('lookup', partial(self._activate_dialog, 'lookup',
                                                manage_windows=True))
        engine.signal_connect('suggestions', partial(self._activate_dialog, 'suggestions',
                                                     manage_windows=True))
        # Load the configuration (but do not start the engine yet).
        if not engine.load_config():
            self.on_configure()
        # Apply configuration settings.
        config = self._engine.config
        self._warn_on_hide_to_tray = not config['start_minimized']
        self._update_machine(config['machine_type'])
        self._configured = False
        self.set_visible(not config['start_minimized'])
        # Process events before starting the engine
        # (to avoid display lag at window creation).
        QCoreApplication.processEvents()
        # Start the engine.
        engine.start()

    def set_visible(self, visible):
        if visible:
            self.show()
        else:
            if self._trayicon.is_enabled():
                self.hide()
            else:
                self.showMinimized()

    def _is_wayland(self):
        return "wayland" in QApplication.platformName().lower()

    def _activate_dialog(self, name, args=(), manage_windows=False):
        if manage_windows:
            previous_window = wmctrl.GetForegroundWindow()
        dialog = self._active_dialogs.get(name)
        if dialog is None:
            dialog_class = self._dialog_class[name]
            dialog = self._active_dialogs[name] = dialog_class(self._engine, *args)
            dialog.setWindowIcon(self.windowIcon())
            def on_finished():
                del self._active_dialogs[name]
                dialog.deleteLater()
                if manage_windows and previous_window is not None:
                    wmctrl.SetForegroundWindow(previous_window)
            dialog.finished.connect(on_finished)
        dialog.showNormal()
        if not self._is_wayland():
            # Otherwise gives this warning:
            # Qt: Wayland does not support QWindow::requestActivate()
            dialog.activateWindow()
        dialog.raise_()

    def _add_translation(self, dictionary=None, manage_windows=False):
        if not dictionary:
            dictionary = None
        self._activate_dialog('add_translation', args=(dictionary,),
                              manage_windows=manage_windows)

    def _focus(self):
        self.showNormal()
        if not self._is_wayland():
            self.activateWindow()
        self.raise_()

    def _configure(self, manage_windows=False):
        self._activate_dialog('configuration', manage_windows=manage_windows)

    def _lookup(self, manage_windows=False):
        self._activate_dialog('lookup', manage_windows=manage_windows)

    def _restore_state(self, settings):
        if settings.contains('hidden_toolbar_tools'):
            hidden_toolbar_tools = json.loads(settings.value('hidden_toolbar_tools'))
            for action in self.toolbar_menu.actions():
                action.setChecked(action.objectName() not in hidden_toolbar_tools)

    def _save_state(self, settings):
        hidden_toolbar_tools = {
            action.objectName()
            for action in self.toolbar_menu.actions()
            if not action.isChecked()
        }
        settings.setValue('hidden_toolbar_tools', json.dumps(list(sorted(hidden_toolbar_tools))))

    def _update_machine(self, machine_type):
        self.machine_type.setCurrentIndex(self.machine_type.findData(machine_type))

    def on_config_changed(self, config_update):
        if 'machine_type' in config_update:
            self._update_machine(config_update['machine_type'])
        if not self._configured:
            self._configured = True
            if config_update.get('show_suggestions_display', False):
                self._activate_dialog('suggestions')
            if config_update.get('show_stroke_display', False):
                self._activate_dialog('paper_tape')

    def on_machine_changed(self, machine_index):
        self._engine.config = { 'machine_type': self.machine_type.itemData(machine_index) }

    def on_output_changed(self, enabled):
        self._trayicon.update_output(enabled)
        self.output_enable.setChecked(enabled)
        self.output_disable.setChecked(not enabled)
        self.action_ToggleOutput.setChecked(enabled)

    def on_toggle_output(self, enabled):
        self._engine.output = enabled

    def on_enable_output(self):
        self.on_toggle_output(True)

    def on_disable_output(self):
        self.on_toggle_output(False)

    def on_configure(self):
        self._configure()

    def on_open_config_folder(self):
        if PLATFORM == 'win':
            os.startfile(CONFIG_DIR)
        elif PLATFORM == 'linux':
            subprocess.call(['xdg-open', CONFIG_DIR])
        elif PLATFORM == 'mac':
            subprocess.call(['open', CONFIG_DIR])

    def on_reconnect(self):
        self._engine.reset_machine()

    def on_manage_dictionaries(self):
        self._activate_dialog('dictionary_manager')

    def on_about(self):
        self._activate_dialog('about')

    def on_quit(self):
        for dialog in list(self._active_dialogs.values()):
            dialog.close()
        self.save_state()
        self._trayicon.disable()
        self.hide()
        QCoreApplication.quit()

    def on_show(self):
        self._focus()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        if not self._trayicon.is_enabled():
            self._engine.quit()
            return
        if not self._warn_on_hide_to_tray:
            return
        self._trayicon.show_message(_('Application is still running.'))
        self._warn_on_hide_to_tray = False
