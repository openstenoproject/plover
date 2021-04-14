from copy import copy

from PyQt5.QtCore import QVariant, pyqtSignal
from PyQt5.QtWidgets import QWidget

from serial import Serial
from serial.tools.list_ports import comports

from plover.gui_qt.config_keyboard_widget_ui import _, Ui_KeyboardWidget
from plover.gui_qt.config_serial_widget_ui import Ui_SerialWidget


class SerialOption(QWidget, Ui_SerialWidget):

    valueChanged = pyqtSignal(QVariant)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._value = {}

    def setValue(self, value):
        self._value = copy(value)
        self.on_scan()
        port = value['port']
        if port is not None and port != 'None':
            port_index = self.port.findText(port)
            if port_index != -1:
                self.port.setCurrentIndex(port_index)
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
        for setting in ('xonxoff', 'rtscts'):
            widget = getattr(self, setting)
            if setting in value:
                widget.setChecked(value[setting])
            else:
                widget.setEnabled(False)

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


class KeyboardOption(QWidget, Ui_KeyboardWidget):

    valueChanged = pyqtSignal(QVariant)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.arpeggiate.setToolTip(_(
            'Arpeggiate allows using non-NKRO keyboards.\n'
            '\n'
            'Each key can be pressed separately and the\n'
            'space bar is pressed to send the stroke.'
        ))
        self._value = {}

    def setValue(self, value):
        self._value = copy(value)
        self.arpeggiate.setChecked(value['arpeggiate'])

    def on_arpeggiate_changed(self, value):
        self._value['arpeggiate'] = value
        self.valueChanged.emit(self._value)
