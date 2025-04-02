
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import (
    QCursor,
    QFont,
)
from PyQt5.QtWidgets import (
    QAction,
    QFontDialog,
    QMenu,
)

from plover import _
from plover.translation import unescape_translation

from plover.gui_qt.lookup_dialog_ui import Ui_LookupDialog
from plover.gui_qt.utils import ToolBar
from plover.gui_qt.tool import Tool


class LookupDialog(Tool, Ui_LookupDialog):

    # i18n: Widget: “LookupDialog”, tooltip.
    __doc__ = _('Search the dictionary for translations.')

    TITLE = _('Lookup')
    ICON = ':/lookup.svg'
    ROLE = 'lookup'
    SHORTCUT = 'Ctrl+L'

    def __init__(self, engine):
        super().__init__(engine)
        self.setupUi(self)
        self.pattern.installEventFilter(self)
        self.suggestions.installEventFilter(self)
        self.pattern.setFocus()
        self.restore_state()
        self.finished.connect(self.save_state)
        self.layout().addWidget(ToolBar(
            self.action_SelectFont,
        ))

        # Font popup menu.
        self._font_menu = QMenu()
        # i18n: Widget: “SuggestionsDialog”, “font” menu.
        self._font_menu_text = QAction(_('&Text'), self._font_menu)
        # i18n: Widget: “SuggestionsDialog”, “font” menu.
        self._font_menu_strokes = QAction(_('&Strokes'), self._font_menu)
        self._font_menu.addActions([self._font_menu_text, self._font_menu_strokes])

    def _get_font(self, name):
        return getattr(self.suggestions, name)

    def _set_font(self, name, font):
        setattr(self.suggestions, name, font)

    def _restore_state(self, settings):
        for name in (
            'text_font',
            'strokes_font',
        ):
            font_string = settings.value(name)
            if font_string is None:
                continue
            font = QFont()
            if not font.fromString(font_string):
                continue
            self._set_font(name, font)

    def _save_state(self, settings):
        for name in (
            'text_font',
            'strokes_font',
        ):
            font = self._get_font(name)
            font_string = font.toString()
            settings.setValue(name, font_string)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and \
           event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return True
        return False

    def _update_suggestions(self, suggestion_list):
        self.suggestions.clear()
        self.suggestions.append(suggestion_list)

    def on_lookup(self, pattern):
        translation = unescape_translation(pattern.strip())
        suggestion_list = self._engine.get_suggestions(translation)
        self._update_suggestions(suggestion_list)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.ActivationChange and self.isActiveWindow():
            self.pattern.setFocus()
            self.pattern.selectAll()

    def on_select_font(self):
        action = self._font_menu.exec_(QCursor.pos())
        if action is None:
            return
        if action == self._font_menu_text:
            name = 'text_font'
            font_options = ()
        elif action == self._font_menu_strokes:
            name = 'strokes_font'
            font_options = (QFontDialog.MonospacedFonts,)
        font = self._get_font(name)
        font, ok = QFontDialog.getFont(font, self, '', *font_options)
        if ok:
            self._set_font(name, font)
