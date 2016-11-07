
from functools import partial

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import (
    QMainWindow,
    QMenu,
)

from plover import log
from plover.oslayer import wmctrl

from plover.gui_qt.log_qt import NotificationHandler
from plover.gui_qt.main_window_ui import Ui_MainWindow
from plover.gui_qt.config_window import ConfigWindow
from plover.gui_qt.dictionaries_widget import DictionariesWidget
from plover.gui_qt.add_translation import AddTranslation
from plover.gui_qt.lookup_dialog import LookupDialog
from plover.gui_qt.suggestions_dialog import SuggestionsDialog
from plover.gui_qt.about_dialog import AboutDialog
from plover.gui_qt.paper_tape import PaperTape
from plover.gui_qt.trayicon import TrayIcon
from plover.gui_qt.utils import WindowState, find_menu_actions


class MainWindow(QMainWindow, Ui_MainWindow, WindowState):

    ROLE = 'main'

    def __init__(self, engine, use_qt_notifications):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        if hasattr(self, 'setUnifiedTitleAndToolBarOnMac'):
            self.setUnifiedTitleAndToolBarOnMac(True)
        self._engine = engine
        self._active_dialogs = {}
        self._dialog_class = {
            'about'             : AboutDialog,
            'add_translation'   : AddTranslation,
            'configuration'     : ConfigWindow,
            'lookup'            : LookupDialog,
            'paper_tape'        : PaperTape,
            'suggestions'       : SuggestionsDialog,
        }
        self.action_Quit.triggered.connect(QCoreApplication.quit)
        all_actions = find_menu_actions(self.menubar)
        # Dictionaries.
        self.dictionaries = DictionariesWidget(engine)
        self.dictionaries.add_translation.connect(self._add_translation)
        self.scroll_area.setWidget(self.dictionaries)
        self.dictionaries.setFocus()
        edit_menu = all_actions['menu_Edit'].menu()
        edit_menu.addAction(self.dictionaries.action_Undo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.dictionaries.action_AddDictionaries)
        edit_menu.addAction(self.dictionaries.action_EditDictionaries)
        edit_menu.addAction(self.dictionaries.action_RemoveDictionaries)
        edit_menu.addSeparator()
        edit_menu.addAction(self.dictionaries.action_MoveDictionariesUp)
        edit_menu.addAction(self.dictionaries.action_MoveDictionariesDown)
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
        engine.signal_connect('output_changed', self.on_output_changed)
        # Machine.
        self.machine_type.addItems(
            _(machine)
            for machine in engine.list_plugins('machine')
        )
        engine.signal_connect('config_changed', self.on_config_changed)
        engine.signal_connect('machine_state_changed',
            lambda machine, state:
            self.machine_state.setText(_(state.capitalize()))
        )
        self.restore_state()
        # Commands.
        engine.signal_connect('add_translation', partial(self._add_translation, manage_windows=True))
        engine.signal_connect('focus', self._focus)
        engine.signal_connect('configure', partial(self._configure, manage_windows=True))
        engine.signal_connect('lookup', partial(self._lookup, manage_windows=True))
        # Load the configuration (but do not start the engine yet).
        if not engine.load_config():
            self.on_configure()
        # Apply configuration settings.
        config = self._engine.config
        self._configured = False
        self.dictionaries.on_config_changed(config)
        self.set_visible(not config['start_minimized'])
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

    def _activate_dialog(self, name, args=(), manage_windows=False):
        if manage_windows:
            previous_window = wmctrl.GetForegroundWindow()
        dialog = self._active_dialogs.get(name)
        if dialog is None:
            dialog_class = self._dialog_class[name]
            dialog = self._active_dialogs[name] = dialog_class(self._engine, *args)
            def on_finished():
                del self._active_dialogs[name]
                dialog.destroy()
                if manage_windows:
                    wmctrl.SetForegroundWindow(previous_window)
            dialog.finished.connect(on_finished)
        dialog.show()
        dialog.activateWindow()
        dialog.raise_()

    def _add_translation(self, dictionary=None, manage_windows=False):
        if not dictionary:
            dictionary = None
        self._activate_dialog('add_translation', args=(dictionary,),
                              manage_windows=manage_windows)

    def _focus(self):
        self.set_visible(True)
        self.activateWindow()
        self.raise_()

    def _configure(self, manage_windows=False):
        self._activate_dialog('configuration', manage_windows=manage_windows)

    def _lookup(self, manage_windows=False):
        self._activate_dialog('lookup', manage_windows=manage_windows)

    def on_config_changed(self, config_update):
        if 'machine_type' in config_update:
            self.machine_type.setCurrentText(config_update['machine_type'])
        if not self._configured:
            self._configured = True
            if config_update.get('show_suggestions_display', False):
                self.on_suggestions()
            if config_update.get('show_stroke_display', False):
                self.on_paper_tape()

    def on_machine_changed(self, machine_type):
        self._engine.config = { 'machine_type': machine_type }

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

    def on_reconnect(self):
        self._engine.reset_machine()

    def on_manage_dictionaries(self):
        self._activate_dialog('dictionary_manager')

    def on_add_translation(self):
        self._add_translation()

    def on_lookup(self):
        self._lookup()

    def on_suggestions(self):
        self._activate_dialog('suggestions')

    def on_paper_tape(self):
        self._activate_dialog('paper_tape')

    def on_about(self):
        self._activate_dialog('about')

    def on_quit(self):
        for dialog in list(self._active_dialogs.values()):
            dialog.close()
        self.save_state()
        self._trayicon.disable()
        self.hide()

    def on_show(self):
        self._focus()

    def closeEvent(self, event):
        if self._trayicon.is_enabled():
            self.hide()
            event.ignore()
        else:
            QCoreApplication.quit()
            event.accept()
