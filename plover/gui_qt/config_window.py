
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
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from serial import Serial
from serial.tools.list_ports import comports

from plover.config import MINIMUM_OUTPUT_CONFIG_UNDO_LEVELS
from plover.machine.base import SerialStenotypeBase
from plover.machine.keyboard import Keyboard
from plover.misc import expand_path, shorten_path
from plover.registry import registry

from plover.gui_qt.config_window_ui import Ui_ConfigWindow
from plover.gui_qt.config_file_widget_ui import Ui_FileWidget
from plover.gui_qt.config_keyboard_widget_ui import Ui_KeyboardWidget
from plover.gui_qt.config_serial_widget_ui import Ui_SerialWidget
from plover.gui_qt.utils import WindowState


class NopeOption(QLabel):

    valueChanged = pyqtSignal(bool)

    def __init__(self):
        super(NopeOption, self).__init__()
        self.setText(_('Nothing to see here!'))

    def setValue(self, value):
        pass


class BooleanOption(QCheckBox):

    valueChanged = pyqtSignal(bool)

    def __init__(self):
        super(BooleanOption, self).__init__()
        self.stateChanged.connect(lambda: self.valueChanged.emit(self.isChecked()))

    def setValue(self, value):
        self.setChecked(value)


class IntOption(QSpinBox):

    def __init__(self, maximum=None, minimum=None):
        super(IntOption, self).__init__()
        if maximum is not None:
            self.setMaximum(maximum)
        if minimum is not None:
            self.setMinimum(minimum)


class ChoiceOption(QComboBox):

    valueChanged = pyqtSignal(str)

    def __init__(self, choices=None):
        super(ChoiceOption, self).__init__()
        self._choices = {} if choices is None else choices
        self._reversed_choices = {
            translation: choice
            for choice, translation in choices.items()
        }
        self.addItems(sorted(choices.values()))
        self.activated.connect(self.on_activated)

    def setValue(self, value):
        translation = self._choices[value]
        self.setCurrentText(translation)

    def on_activated(self):
        choice = self._reversed_choices[self.currentText()]
        self.valueChanged.emit(choice)


class FileOption(QWidget, Ui_FileWidget):

    valueChanged = pyqtSignal(str)

    def __init__(self, dialog_title, dialog_filter):
        super(FileOption, self).__init__()
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


class KeyboardOption(QWidget, Ui_KeyboardWidget):

    valueChanged = pyqtSignal(QVariant)

    def __init__(self):
        super(KeyboardOption, self).__init__()
        self.setupUi(self)
        self.arpeggiate.setToolTip(_(
            'Arpeggiate allows using non-NKRO keyboards.\n'
            '\n'
            'Each key can be pressed separately and the\n'
            'space bar is pressed to send the stroke.'
        ))
        self._value = {}

    def setValue(self, value):
        self._value = value
        self.arpeggiate.setChecked(value['arpeggiate'])

    def on_arpeggiate_changed(self, value):
        self._value['arpeggiate'] = value
        self.valueChanged.emit(self._value)


class SerialOption(QWidget, Ui_SerialWidget):

    valueChanged = pyqtSignal(QVariant)

    def __init__(self):
        super(SerialOption, self).__init__()
        self.setupUi(self)
        self._value = {}

    def setValue(self, value):
        self._value = value
        port = value['port']
        if port is None or port == 'None':
            self.on_scan()
        else:
            self.port.setCurrentText(port)
        self.baudrate.addItems(map(str, Serial.BAUDRATES))
        self.baudrate.setCurrentText(str(value['baudrate']))
        self.bytesize.addItems(map(str, Serial.BYTESIZES))
        self.bytesize.setCurrentText(str(value['bytesize']))
        self.parity.addItems(Serial.PARITIES)
        self.parity.setCurrentText(value['parity'])
        self.stopbits.addItems(map(str, Serial.STOPBITS))
        self.stopbits.setCurrentText(str(value['stopbits']))
        timeout = value['timeout']
        if timeout is None:
            self.use_timeout.setChecked(False)
            self.timeout.setValue(0.0)
            self.timeout.setEnabled(False)
        else:
            self.use_timeout.setChecked(True)
            self.timeout.setValue(timeout)
            self.timeout.setEnabled(True)
        self.xonxoff.setChecked(value['xonxoff'])
        self.rtscts.setChecked(value['rtscts'])

    def _update(self, field, value):
        self._value[field] = value
        self.valueChanged.emit(self._value)

    def on_scan(self):
        self.port.clear()
        self.port.addItems(sorted(x[0] for x in comports()))

    def on_port_changed(self, value):
        self._update('port', value)

    def on_baudrate_changed(self, value):
        self._update('baudrate', int(value))

    def on_bytesize_changed(self, value):
        self._update('baudrate', int(value))

    def on_parity_changed(self, value):
        self._update('parity', value)

    def on_stopbits_changed(self, value):
        self._update('stopbits', float(value))

    def on_timeout_changed(self, value):
        self._update('timeout', value)

    def on_use_timeout_changed(self, value):
        if value:
            timeout = self.timeout.value()
        else:
            timeout = None
        self.timeout.setEnabled(value)
        self._update('timeout', timeout)

    def on_xonxoff_changed(self, value):
        self._update('xonxoff', value)

    def on_rtscts_changed(self, value):
        self._update('rtscts', value)


class KeymapOption(QTableWidget):

    valueChanged = pyqtSignal(QVariant)

    def __init__(self):
        super(KeymapOption, self).__init__()
        self._value = []
        self._updating = False
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels((_('Action'), _('Keys')))
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().hide()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cellChanged.connect(self._on_cell_changed)

    def setValue(self, value):
        self._updating = True
        self._value = value
        self.setRowCount(0)
        if value is not None:
            row = -1
            for action, keys in value.get_mappings().items():
                if not isinstance(keys, (tuple, list)):
                    keys = (keys,)
                row += 1
                self.insertRow(row)
                item = QTableWidgetItem(action)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.setItem(row, 0, item)
                item = QTableWidgetItem(' '.join(sorted(keys)))
                self.setItem(row, 1, item)
        self.resizeColumnsToContents()
        self.setMinimumSize(self.viewportSizeHint())
        self._updating = False

    def _on_cell_changed(self, row, column):
        if self._updating:
            return
        action = self.item(row, 0).data(Qt.DisplayRole)
        keys = self.item(row, 1).data(Qt.DisplayRole)
        self._value[action] = keys.split()
        new_keys = self._value[action]
        if new_keys != keys:
            self._updating = True
            self.item(row, 1).setData(Qt.DisplayRole, ' '.join(sorted(new_keys)))
            self._updating = False
        self.valueChanged.emit(self._value)


class MultipleChoicesOption(QTableWidget):

    valueChanged = pyqtSignal(QVariant)

    def __init__(self, choices=None, labels=(_('Choice'), _('Selected'))):
        super(MultipleChoicesOption, self).__init__()
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
        assert (row, column) == (0, 1)
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
        super(BooleanAsDualChoiceOption, self).__init__(choices)


class ConfigOption(object):

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
        super(ConfigWindow, self).__init__()
        self.setupUi(self)
        self._engine = engine
        machines = {
            plugin.name: _(plugin.name)
            for plugin in registry.list_plugins('machine')
        }
        mappings = (
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
            (_('Logging'), (
                ConfigOption(_('Log file:'), 'log_file_name',
                             partial(FileOption,
                                     _('Select a log file'),
                                     _('Log files') + ' (*.log)'),
                             _('File to use for logging strokes/translations.')),
                ConfigOption(_('Log strokes:'), 'enable_stroke_logging', BooleanOption,
                             _('Save strokes to the logfile.')),
                ConfigOption(_('Log translations:'), 'enable_translation_logging', BooleanOption,
                             _('Save translations to the logfile.')),
            )),
            (_('Machine'), (
                ConfigOption(_('Machine:'), 'machine_type', partial(ChoiceOption, choices=machines),
                             dependents=(
                                 ('machine_specific_options', engine.machine_specific_options),
                                 ('system_keymap', lambda v: self._update_keymap(machine_type=v)),
                             )),
                ConfigOption(_('Options:'), 'machine_specific_options', self._machine_option),
                ConfigOption(_('Keymap:'), 'system_keymap', KeymapOption),
            )),
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
                                     minimum=MINIMUM_OUTPUT_CONFIG_UNDO_LEVELS),
                             _('Set how many preceding strokes can be undone.\n'
                               '\n'
                               'Note: the effective value will take into account the\n'
                               'dictionaries entry with the maximum number of strokes.')),
            )),
            (_('Plugins'), (
                ConfigOption(_('Extension:'), 'enabled_extensions',
                             partial(MultipleChoicesOption, choices={
                                 plugin.name: plugin.name
                                 for plugin in registry.list_plugins('extension')
                             }, labels=(_('Name'), _('Enabled'))),
                             _('Configure enabled plugin extensions.')),
            )),
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
        supported_options = set()
        for section, option_list in mappings:
            supported_options.update(option.option_name for option in option_list)
        self._config = {
            name: value
            for name, value in engine.config.items()
            if name in supported_options
        }
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

    def _machine_option(self, *args):
        machine_type = self._config['machine_type']
        machine_class = registry.get_plugin('machine', machine_type).obj
        if issubclass(machine_class, Keyboard):
            opt_class = KeyboardOption
        elif issubclass(machine_class, SerialStenotypeBase):
            opt_class = SerialOption
        else:
            opt_class = NopeOption
        return opt_class(*args)

    def _update_keymap(self, machine_type=None, system_name=None):
        if machine_type is None:
            machine_type = self._config['machine_type']
        if system_name is None:
            system_name = self._config['system_name']
        keymap = self._engine.system_keymap(machine_type=machine_type,
                                            system_name=system_name)
        return keymap

    def _create_option_widget(self, option):
        widget = option.widget_class()
        widget.setToolTip(option.help_text)
        widget.setValue(self._config[option.option_name])
        widget.valueChanged.connect(partial(self.on_option_changed, option))
        return widget

    def keyPressEvent(self, event):
        # Disable Enter/Return key to trigger "OK".
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return
        super(ConfigWindow, self).keyPressEvent(event)

    def on_option_changed(self, option, value):
        self._config[option.option_name] = value
        for dependent, update_fn in option.dependents:
            self._config[dependent.option_name] = update_fn(value)
            widget = self._create_option_widget(dependent)
            dependent.layout.replaceWidget(dependent.widget, widget)
            dependent.widget.deleteLater()
            dependent.widget = widget

    def on_apply(self):
        self._engine.config = self._config
