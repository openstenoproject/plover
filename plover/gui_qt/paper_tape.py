
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFileDialog,
    QFontDialog,
    QMessageBox,
)

from wcwidth import wcwidth

from plover import system

from plover.gui_qt.paper_tape_ui import _, Ui_PaperTape
from plover.gui_qt.utils import ToolBar
from plover.gui_qt.tool import Tool


class PaperTape(Tool, Ui_PaperTape):

    ''' Paper tape display of strokes. '''

    TITLE = _('Paper Tape')
    ICON = ':/tape.svg'
    ROLE = 'paper_tape'
    SHORTCUT = 'Ctrl+T'

    STYLE_PAPER, STYLE_RAW = (
        # i18n: Paper tape style.
        _('Paper'),
        # i18n: Paper tape style.
        _('Raw'),
    )
    STYLES = (STYLE_PAPER, STYLE_RAW)

    def __init__(self, engine):
        super().__init__(engine)
        self.setupUi(self)
        self._strokes = []
        self._all_keys = None
        self._all_keys_filler = None
        self._formatter = None
        self._history_size = 2000000
        self.styles.addItems(self.STYLES)
        # Toolbar.
        self.layout().addWidget(ToolBar(
            self.action_ToggleOnTop,
            self.action_SelectFont,
            self.action_Clear,
            self.action_Save,
        ))
        self.action_Clear.setEnabled(False)
        self.action_Save.setEnabled(False)
        engine.signal_connect('config_changed', self.on_config_changed)
        self.on_config_changed(engine.config)
        engine.signal_connect('stroked', self.on_stroke)
        self.tape.setFocus()
        self.restore_state()
        self.finished.connect(self.save_state)

    def _restore_state(self, settings):
        style = settings.value('style', None, int)
        if style is not None:
            self.styles.setCurrentText(self.STYLES[style])
            self.on_style_changed(self.STYLES[style])
        font_string = settings.value('font')
        if font_string is not None:
            font = QFont()
            if font.fromString(font_string):
                self.header.setFont(font)
                self.tape.setFont(font)
        ontop = settings.value('ontop', None, bool)
        if ontop is not None:
            self.action_ToggleOnTop.setChecked(ontop)
            self.on_toggle_ontop(ontop)

    def _save_state(self, settings):
        settings.setValue('style', self.STYLES.index(self._style))
        settings.setValue('font', self.header.font().toString())
        ontop = bool(self.windowFlags() & Qt.WindowStaysOnTopHint)
        settings.setValue('ontop', ontop)

    def on_config_changed(self, config):
        if 'system_name' in config:
            self._strokes = []
            self._all_keys = ''.join(key.strip('-') for key in system.KEYS)
            self._all_keys_filler = [
                ' ' * wcwidth(k)
                for k in self._all_keys
            ]
            self._numbers = set(system.NUMBERS.values())
            self.header.setText(self._all_keys)
            self.on_style_changed(self._style)

    @property
    def _style(self):
        return self.styles.currentText()

    def _paper_format(self, stroke):
        text = self._all_keys_filler * 1
        keys = stroke.steno_keys[:]
        if any(key in self._numbers for key in keys):
            keys.append('#')
        for key in keys:
            index = system.KEY_ORDER[key]
            text[index] = self._all_keys[index]
        return ''.join(text)

    def _raw_format(self, stroke):
        return stroke.rtfcre

    def _show_stroke(self, stroke):
        text = self._formatter(stroke)
        self.tape.appendPlainText(text)

    def on_stroke(self, stroke):
        assert len(self._strokes) <= self._history_size
        if len(self._strokes) == self._history_size:
            self._strokes.pop(0)
        self._strokes.append(stroke)
        self._show_stroke(stroke)
        self.action_Clear.setEnabled(True)
        self.action_Save.setEnabled(True)

    def on_style_changed(self, style):
        assert style in self.STYLES
        if style == self.STYLE_PAPER:
            self.header.show()
            self._formatter = self._paper_format
        elif style == self.STYLE_RAW:
            self.header.hide()
            self._formatter = self._raw_format
        self.tape.clear()
        for stroke in self._strokes:
            self._show_stroke(stroke)

    def on_select_font(self):
        font, ok = QFontDialog.getFont(self.header.font(), self, '',
                                       QFontDialog.MonospacedFonts)
        if ok:
            self.header.setFont(font)
            self.tape.setFont(font)

    def on_toggle_ontop(self, ontop):
        flags = self.windowFlags()
        if ontop:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def on_clear(self):
        flags = self.windowFlags()
        msgbox = QMessageBox()
        msgbox.setText(_('Do you want to clear the paper tape?'))
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        # Make sure the message box ends up above the paper tape!
        msgbox.setWindowFlags(msgbox.windowFlags() | (flags & Qt.WindowStaysOnTopHint))
        if QMessageBox.Yes != msgbox.exec_():
            return
        self._strokes = []
        self.action_Clear.setEnabled(False)
        self.action_Save.setEnabled(False)
        self.tape.clear()

    def on_save(self):
        filename_suggestion = 'steno-notes-%s.txt' % time.strftime('%Y-%m-%d-%H-%M')
        filename = QFileDialog.getSaveFileName(
            self, _('Save Paper Tape'), filename_suggestion,
            # i18n: Paper tape, "save" file picker.
            _('Text files (*.txt)'),
        )[0]
        if not filename:
            return
        with open(filename, 'w') as fp:
            fp.write(self.tape.toPlainText())
