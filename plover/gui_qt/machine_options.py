from copy import copy
from pathlib import Path

from PyQt5.QtCore import Qt, QVariant, pyqtSignal
from PyQt5.QtGui import (
    QTextCharFormat,
    QTextFrameFormat,
    QTextListFormat,
    QTextCursor,
    QTextDocument,
)
from PyQt5.QtWidgets import (
    QGroupBox,
    QStyledItemDelegate,
    QStyle,
    QToolTip,
)

from serial import Serial
from serial.tools.list_ports import comports

from plover import _
from plover.oslayer.serial import patch_ports_info

from plover.gui_qt.config_keyboard_widget_ui import Ui_KeyboardWidget
from plover.gui_qt.config_serial_widget_ui import Ui_SerialWidget


def serial_port_details(port_info):
    parts = []
    global_ignore = {None, 'n/a', Path(port_info.device).name}
    local_ignore = set(global_ignore)
    for attr, fmt in (
        ('product', _('product: {value}')),
        ('manufacturer', _('manufacturer: {value}')),
        ('serial_number', _('serial number: {value}')),
    ):
        value = getattr(port_info, attr)
        if value not in global_ignore:
            parts.append(fmt.format(value=value))
            local_ignore.add(value)
    description = getattr(port_info, 'description')
    if description not in local_ignore:
        parts.insert(0, _('description: {value}').format(value=description))
    if not parts:
        return None
    return parts


class SerialOption(QGroupBox, Ui_SerialWidget):

    class PortDelegate(QStyledItemDelegate):

        def __init__(self):
            super().__init__()
            self._doc = QTextDocument()
            doc_margin = self._doc.documentMargin()
            self._doc.setIndentWidth(doc_margin * 3)
            background = QToolTip.palette().toolTipBase()
            foreground = QToolTip.palette().toolTipText()
            self._device_format = QTextCharFormat()
            self._details_char_format = QTextCharFormat()
            self._details_char_format.setFont(QToolTip.font())
            self._details_char_format.setBackground(background)
            self._details_char_format.setForeground(foreground)
            self._details_frame_format = QTextFrameFormat()
            self._details_frame_format.setBackground(background)
            self._details_frame_format.setForeground(foreground)
            self._details_frame_format.setTopMargin(doc_margin)
            self._details_frame_format.setBottomMargin(-3 * doc_margin)
            self._details_frame_format.setBorderStyle(QTextFrameFormat.BorderStyle_Solid)
            self._details_frame_format.setBorder(doc_margin / 2)
            self._details_frame_format.setPadding(doc_margin)
            self._details_list_format = QTextListFormat()
            self._details_list_format.setStyle(QTextListFormat.ListSquare)

        def _format_port(self, index):
            self._doc.clear()
            cursor = QTextCursor(self._doc)
            cursor.setCharFormat(self._device_format)
            port_info = index.data(Qt.UserRole)
            if port_info is None:
                cursor.insertText(index.data(Qt.DisplayRole))
                return
            cursor.insertText(port_info.device)
            details = serial_port_details(port_info)
            if not details:
                return
            cursor.insertFrame(self._details_frame_format)
            details_list = cursor.createList(self._details_list_format)
            for n, part in enumerate(details):
                if n:
                    cursor.insertBlock()
                cursor.insertText(part, self._details_char_format)

        def paint(self, painter, option, index):
            painter.save()
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
                text_color = option.palette.highlightedText()
            else:
                text_color = option.palette.text()
            self._device_format.setForeground(text_color)
            doc_margin = self._doc.documentMargin()
            self._details_frame_format.setWidth(option.rect.width() - doc_margin * 2)
            self._format_port(index)
            painter.translate(option.rect.topLeft())
            self._doc.drawContents(painter)
            painter.restore()

        def sizeHint(self, option, index):
            self._format_port(index)
            return self._doc.size().toSize()

    valueChanged = pyqtSignal(QVariant)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.port.setItemDelegate(self.PortDelegate())
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
        for port_info in sorted(patch_ports_info(comports())):
            self.port.addItem(port_info.device, port_info)

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


class KeyboardOption(QGroupBox, Ui_KeyboardWidget):

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
        self.first_up_chord_send.setChecked(value['first_up_chord_send'])

    def on_arpeggiate_changed(self, value):
        self._value['arpeggiate'] = value
        self.valueChanged.emit(self._value)

    def on_first_up_chord_send_changed(self, value):
        self._value['first_up_chord_send'] = value
        self.valueChanged.emit(self._value)
