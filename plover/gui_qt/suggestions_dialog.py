
import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QCursor,
    QFont,
)
from PyQt5.QtWidgets import (
    QAction,
    QFontDialog,
    QMenu,
)

from plover.suggestions import Suggestion

from plover.gui_qt.suggestions_dialog_ui import Ui_SuggestionsDialog
from plover.gui_qt.suggestions_widget import SuggestionsWidget
from plover.gui_qt.tool import Tool
from plover.gui_qt.utils import ToolBar


class SuggestionsDialog(Tool, Ui_SuggestionsDialog):

    ''' Suggest possible strokes for the last written words. '''

    TITLE = _('Suggestions')
    ICON = ':/suggestions.svg'
    ROLE = 'suggestions'
    SHORTCUT = 'Ctrl+J'

    WORDS_RX = re.compile(r'[-\'"\w]+|[^\w\s]')

    STYLE_TRANSLATION, STYLE_STROKES = range(2)

    # Anatomy of the text document:
    # - "root" frame:
    #  - 0+ "suggestions" frames
    #   - 1+ "translation" frames
    #    - 1-10 "strokes" frames

    def __init__(self, engine):
        super(SuggestionsDialog, self).__init__(engine)
        self.setupUi(self)
        suggestions = SuggestionsWidget()
        self.layout().replaceWidget(self.suggestions, suggestions)
        self.suggestions = suggestions
        self._words = u''
        self._last_suggestions = None
        # Toolbar.
        self.layout().addWidget(ToolBar(
            self.action_ToggleOnTop,
            self.action_SelectFont,
            self.action_Clear,
        ))
        self.action_Clear.setEnabled(False)
        # Font popup menu.
        self._font_menu = QMenu()
        self._font_menu_text = QAction(_('&Text'), self._font_menu)
        self._font_menu_strokes = QAction(_('&Strokes'), self._font_menu)
        self._font_menu.addActions([self._font_menu_text, self._font_menu_strokes])
        engine.signal_connect('translated', self.on_translation)
        self.suggestions.setFocus()
        self.restore_state()
        self.finished.connect(self.save_state)

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

    def _show_suggestions(self, suggestion_list):
        self.suggestions.prepend(suggestion_list)
        self.action_Clear.setEnabled(True)

    @staticmethod
    def tails(ls):
        ''' Return all tail combinations (a la Haskell)

            tails :: [x] -> [[x]]
            >>> tails('abcd')
            ['abcd', 'bcd', 'cd', d']

        '''

        for i in range(len(ls)):
            yield ls[i:]

    def on_translation(self, old, new):
        for action in old:
            remove = len(action.text)
            self._words = self._words[:-remove]
            self._words = self._words + action.replace

        for action in new:
            remove = len(action.replace)
            if remove > 0:
                self._words = self._words[:-remove]
            self._words = self._words + action.text

        # Limit phrasing memory to 100 characters, because most phrases probably
        # don't exceed this length
        self._words = self._words[-100:]

        suggestion_list = []
        split_words = self.WORDS_RX.findall(self._words)
        for phrase in self.tails(split_words):
            phrase = u' '.join(phrase)
            suggestion_list.extend(self._engine.get_suggestions(phrase))

        if not suggestion_list and split_words:
            suggestion_list = [Suggestion(split_words[-1], [])]

        if suggestion_list and suggestion_list != self._last_suggestions:
            self._last_suggestions = suggestion_list
            self._show_suggestions(suggestion_list)

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

    def on_toggle_ontop(self, ontop):
        flags = self.windowFlags()
        if ontop:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def on_clear(self):
        self.action_Clear.setEnabled(False)
        self._last_suggestions = None
        self.suggestions.clear()
