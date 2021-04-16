
from collections import ChainMap
from copy import copy
from functools import partial

from PyQt5.QtCore import (
    Qt,
    QVariant,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QLabel,
    QScrollArea,
    QSpinBox,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from plover.config import MINIMUM_UNDO_LEVELS
from plover.misc import expand_path, shorten_path
from plover.registry import registry

from plover.gui_qt.config_window_ui import _, Ui_ConfigWindow
from plover.gui_qt.config_file_widget_ui import Ui_FileWidget
from plover.gui_qt.utils import WindowState


class NopeOption(QLabel):

    valueChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        # i18n: Widget: “NopeOption” (empty config option message,
        # e.g. the machine option when selecting the Treal machine).
        self.setText(_('Nothing to see here!'))

    def setValue(self, value):
        pass


class BooleanOption(QCheckBox):

    valueChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.stateChanged.connect(lambda: self.valueChanged.emit(self.isChecked()))

    def setValue(self, value):
        self.setChecked(value)


class IntOption(QSpinBox):

    def __init__(self, maximum=None, minimum=None):
        super().__init__()
        if maximum is not None:
            self.setMaximum(maximum)
        if minimum is not None:
            self.setMinimum(minimum)


class ChoiceOption(QComboBox):

    valueChanged = pyqtSignal(str)

    def __init__(self, choices=None):
        super().__init__()
        choices = {} if choices is None else choices
        for value, label in sorted(choices.items()):
            self.addItem(label, value)
        self.activated.connect(self.on_activated)

    def setValue(self, value):
        self.setCurrentIndex(self.findData(value))

    def on_activated(self, index):
        self.valueChanged.emit(self.itemData(index))


class FileOption(QWidget, Ui_FileWidget):

    valueChanged = pyqtSignal(str)

    def __init__(self, dialog_title, dialog_filter):
        super().__init__()
        self._dialog_title = dialog_title
        self._dialog_filter = dialog_filter
        self.setupUi(self)

    def setValue(self, value):
        self.path.setText(shorten_path(value))

    def on_browse(self):
        filename_suggestion = self.path.text()
        filename = QFileDialog.getSaveFileName(
            self, self._dialog_title,
            filename_suggestion,
            self._dialog_filter,
        )[0]
        if not filename:
            return
        self.path.setText(shorten_path(filename))
        self.valueChanged.emit(filename)

    def on_path_edited(self):
        self.valueChanged.emit(expand_path(self.path.text()))


class KeymapOption(QTableWidget):

    valueChanged = pyqtSignal(QVariant)

    class ItemDelegate(QStyledItemDelegate):

        def __init__(self, action_list):
            super().__init__()
            self._action_list = action_list

        def createEditor(self, parent, option, index):
            if index.column() == 1:
                combo = QComboBox(parent)
                combo.addItem('')
                combo.addItems(self._action_list)
                return combo
            return super().createEditor(parent, option, index)

    def __init__(self):
        super().__init__()
        self._value = []
        self._updating = False
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels((
            # i18n: Widget: “KeymapOption”.
            _('Key'),
            # i18n: Widget: “KeymapOption”.
            _('Action'),
        ))
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().hide()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cellChanged.connect(self._on_cell_changed)

    def setValue(self, value):
        self._updating = True
        self._value = copy(value)
        self.setRowCount(0)
        if value is not None:
            row = -1
            for key in value.get_keys():
                action = value.get_action(key)
                if action is None:
                    action = ''
                row += 1
                self.insertRow(row)
                item = QTableWidgetItem(key)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.setItem(row, 0, item)
                item = QTableWidgetItem(action)
                self.setItem(row, 1, item)
        self.resizeColumnsToContents()
        self.setMinimumSize(self.viewportSizeHint())
        self.setItemDelegate(KeymapOption.ItemDelegate(value.get_actions()))
        self._updating = False

    def _on_cell_changed(self, row, column):
        if self._updating:
            return
        key = self.item(row, 0).data(Qt.DisplayRole)
        action = self.item(row, 1).data(Qt.DisplayRole)
        bindings = self._value.get_bindings()
        if action:
            bindings[key] = action
        else:
            bindings.pop(key, None)
        self._value.set_bindings(bindings)
        self.valueChanged.emit(self._value)


class MultipleChoicesOption(QTableWidget):

    valueChanged = pyqtSignal(QVariant)

    LABELS = (
        # i18n: Widget: “MultipleChoicesOption”.
        _('Choice'),
        # i18n: Widget: “MultipleChoicesOption”.
        _('Selected'),
    )

    # i18n: Widget: “MultipleChoicesOption”.
    def __init__(self, choices=None, labels=None):
        super().__init__()
        if labels is None:
            labels = self.LABELS
        self._value = {}
        self._updating = False
        self._choices = {} if choices is None else choices
        self._reversed_choices = {
            translation: choice
            for choice, translation in choices.items()
        }
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(labels)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().hide()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cellChanged.connect(self._on_cell_changed)

    def setValue(self, value):
        self._updating = True
        self.resizeColumnsToContents()
        self.setMinimumSize(self.viewportSizeHint())
        self.setRowCount(0)
        if value is None:
            value = set()
        else:
            # Don't mutate the original value.
            value = set(value)
        self._value = value
        row = -1
        for choice in sorted(self._reversed_choices):
            row += 1
            self.insertRow(row)
            item = QTableWidgetItem(self._choices[choice])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 0, item)
            item = QTableWidgetItem()
            item.setFlags((item.flags() & ~Qt.ItemIsEditable) | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if choice in value else Qt.Unchecked)
            self.setItem(row, 1, item)
        self.resizeColumnsToContents()
        self.setMinimumSize(self.viewportSizeHint())
        self._updating = False

    def _on_cell_changed(self, row, column):
        if self._updating:
            return
        assert column == 1
        choice = self._reversed_choices[self.item(row, 0).data(Qt.DisplayRole)]
        if self.item(row, 1).checkState():
            self._value.add(choice)
        else:
            self._value.discard(choice)
        self.valueChanged.emit(self._value)


class BooleanAsDualChoiceOption(ChoiceOption):

    valueChanged = pyqtSignal(bool)

    def __init__(self, choice_false, choice_true):
        choices = { False: choice_false, True: choice_true }
        super().__init__(choices)


class ConfigOption:

    def __init__(self, display_name, option_name, widget_class,
                 help_text='', dependents=()):
        self.display_name = display_name
        self.option_name = option_name
        self.help_text = help_text
        self.widget_class = widget_class
        self.dependents = dependents
        self.layout = None
        self.widget = None


class ConfigWindow(QDialog, Ui_ConfigWindow, WindowState):

    ROLE = 'configuration'

    def __init__(self, engine):
        super().__init__()
        self.setupUi(self)
        self._engine = engine
        machines = {
            plugin.name: _(plugin.name)
            for plugin in registry.list_plugins('machine')
        }
        mappings = (
            # i18n: Widget: “ConfigWindow”.
            (_('Interface'), (
                ConfigOption(_('Start minimized:'), 'start_minimized', BooleanOption,
                             _('Minimize the main window to systray on startup.')),
                ConfigOption(_('Show paper tape:'), 'show_stroke_display', BooleanOption,
                             _('Open the paper tape on startup.')),
                ConfigOption(_('Show suggestions:'), 'show_suggestions_display', BooleanOption,
                             _('Open the suggestions dialog on startup.')),
                ConfigOption(_('Add translation dialog opacity:'), 'translation_frame_opacity',
                             partial(IntOption, maximum=100, minimum=0),
                             _('Set the translation dialog opacity:\n'
                               '- 0 makes the dialog invisible\n'
                               '- 100 is fully opaque')),
                ConfigOption(_('Dictionaries display order:'), 'classic_dictionaries_display_order',
                             partial(BooleanAsDualChoiceOption,
                                     _('top-down'), _('bottom-up')),
                             _('Set the display order for dictionaries:\n'
                               '- top-down: match the search order; highest priority first\n'
                               '- bottom-up: reverse search order; lowest priority first\n')),
            )),
            # i18n: Widget: “ConfigWindow”.
            (_('Logging'), (
                ConfigOption(_('Log file:'), 'log_file_name',
                             partial(FileOption,
                                     _('Select a log file'),
                                     _('Log files (*.log)')),
                             _('File to use for logging strokes/translations.')),
                ConfigOption(_('Log strokes:'), 'enable_stroke_logging', BooleanOption,
                             _('Save strokes to the logfile.')),
                ConfigOption(_('Log translations:'), 'enable_translation_logging', BooleanOption,
                             _('Save translations to the logfile.')),
            )),
            # i18n: Widget: “ConfigWindow”.
            (_('Machine'), (
                ConfigOption(_('Machine:'), 'machine_type', partial(ChoiceOption, choices=machines),
                             dependents=(
                                 ('machine_specific_options', self._update_machine_options),
                                 ('system_keymap', lambda v: self._update_keymap(machine_type=v)),
                             )),
                ConfigOption(_('Options:'), 'machine_specific_options', self._machine_option),
                ConfigOption(_('Keymap:'), 'system_keymap', KeymapOption),
            )),
            # i18n: Widget: “ConfigWindow”.
            (_('Output'), (
                ConfigOption(_('Enable at start:'), 'auto_start', BooleanOption,
                             _('Enable output on startup.')),
                ConfigOption(_('Start attached:'), 'start_attached', BooleanOption,
                             _('Disable preceding space on first output.\n'
                               '\n'
                               'This option is only applicable when spaces are placed before.')),
                ConfigOption(_('Start capitalized:'), 'start_capitalized', BooleanOption,
                             _('Capitalize the first word.')),
                ConfigOption(_('Space placement:'), 'space_placement',
                             partial(ChoiceOption, choices={
                                 'Before Output': _('Before Output'),
                                 'After Output': _('After Output'),
                             }),
                             _('Set automatic space placement: before or after each word.')),
                ConfigOption(_('Undo levels:'), 'undo_levels',
                             partial(IntOption,
                                     maximum=10000,
                                     minimum=MINIMUM_UNDO_LEVELS),
                             _('Set how many preceding strokes can be undone.\n'
                               '\n'
                               'Note: the effective value will take into account the\n'
                               'dictionaries entry with the maximum number of strokes.')),
            )),
            # i18n: Widget: “ConfigWindow”.
            (_('Plugins'), (
                ConfigOption(_('Extension:'), 'enabled_extensions',
                             partial(MultipleChoicesOption, choices={
                                 plugin.name: plugin.name
                                 for plugin in registry.list_plugins('extension')
                             }, labels=(_('Name'), _('Enabled'))),
                             _('Configure enabled plugin extensions.')),
            )),
            # i18n: Widget: “ConfigWindow”.
            (_('System'), (
                ConfigOption(_('System:'), 'system_name',
                             partial(ChoiceOption, choices={
                                 plugin.name: plugin.name
                                 for plugin in registry.list_plugins('system')
                             }),
                             dependents=(
                                 ('system_keymap', lambda v: self._update_keymap(system_name=v)),
                             )),
            )),
        )
        # Only keep supported options, to avoid messing with things like
        # dictionaries, that are handled by another (possibly concurrent)
        # dialog.
        self._supported_options = set()
        for section, option_list in mappings:
            self._supported_options.update(option.option_name for option in option_list)
        self._update_config()
        # Create and fill tabs.
        options = {}
        for section, option_list in mappings:
            layout = QFormLayout()
            for option in option_list:
                widget = self._create_option_widget(option)
                options[option.option_name] = option
                option.tab_index = self.tabs.count()
                option.layout = layout
                option.widget = widget
                label = QLabel(option.display_name)
                label.setToolTip(option.help_text)
                layout.addRow(label, widget)
            frame = QFrame()
            frame.setLayout(layout)
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(frame)
            self.tabs.addTab(scroll_area, section)
        # Update dependents.
        for option in options.values():
            option.dependents = [
                (options[option_name], update_fn)
                for option_name, update_fn in option.dependents
            ]
        buttons = self.findChild(QWidget, 'buttons')
        buttons.button(QDialogButtonBox.Ok).clicked.connect(self.on_apply)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self.on_apply)
        self.restore_state()
        self.finished.connect(self.save_state)

    def _update_config(self, save=False):
        with self._engine:
            if save:
                self._engine.config = self._config.maps[0]
            self._config = ChainMap({}, {
                name: value
                for name, value in self._engine.config.items()
                if name in self._supported_options
            })

    def _machine_option(self, *args):
        machine_options = {
            plugin.name: plugin.obj
            for plugin in registry.list_plugins('gui.qt.machine_option')
        }
        machine_type = self._config['machine_type']
        machine_class = registry.get_plugin('machine', machine_type).obj
        for klass in machine_class.mro():
            # Look for `module_name:class_name` before `class_name`.
            for name in (
                '%s:%s' % (klass.__module__, klass.__name__),
                klass.__name__,
            ):
                opt_class = machine_options.get(name)
                if opt_class is not None:
                    return opt_class(*args)
        return NopeOption(*args)

    def _update_machine_options(self, machine_type=None):
        return self._engine[('machine_specific_options',
                             machine_type or self._config['machine_type'])]

    def _update_keymap(self, system_name=None, machine_type=None):
        return self._engine[('system_keymap',
                             system_name or self._config['system_name'],
                             machine_type or self._config['machine_type'])]

    def _create_option_widget(self, option):
        widget = option.widget_class()
        widget.setToolTip(option.help_text)
        widget.valueChanged.connect(partial(self.on_option_changed, option))
        widget.setValue(self._config[option.option_name])
        return widget

    def keyPressEvent(self, event):
        # Disable Enter/Return key to trigger "OK".
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return
        super().keyPressEvent(event)

    def on_option_changed(self, option, value):
        self._config[option.option_name] = value
        for dependent, update_fn in option.dependents:
            # Ensure unsaved changes are discarded.
            if dependent.option_name in self._config.maps[0]:
                del self._config.maps[0][dependent.option_name]
            self._config.maps[1][dependent.option_name] = update_fn(value)
            widget = self._create_option_widget(dependent)
            dependent.layout.replaceWidget(dependent.widget, widget)
            dependent.widget.deleteLater()
            dependent.widget = widget

    def on_apply(self):
        self._update_config(save=True)
