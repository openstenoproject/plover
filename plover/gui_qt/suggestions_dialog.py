
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

from plover.config import DEFAULT_SEARCH_WORD_LIMIT
from plover.suggestions import Suggestion
from plover.formatting import RetroFormatter

from plover.gui_qt.suggestions_dialog_ui import Ui_SuggestionsDialog
from plover.gui_qt.i18n import get_gettext
from plover.gui_qt.utils import ToolBar
from plover.gui_qt.tool import Tool


_ = get_gettext()


class SuggestionsDialog(Tool, Ui_SuggestionsDialog):

    ''' Suggest possible strokes for the last written words. '''

    TITLE = _('Suggestions')
    ICON = ':/lightbulb.svg'
    ROLE = 'suggestions'
    SHORTCUT = 'Ctrl+J'

    WORD_RX = re.compile(r'(?:\w+|[^\w\s]+)\s*')

    STYLE_TRANSLATION, STYLE_STROKES = range(2)

    # Anatomy of the text document:
    # - "root" frame:
    #  - 0+ "suggestions" frames
    #   - 1+ "translation" frames
    #    - 1-10 "strokes" frames

    def __init__(self, engine):
        super().__init__(engine)
        self.setupUi(self)
        self._last_suggestions = None
        self._word_limit = DEFAULT_SEARCH_WORD_LIMIT
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
        engine.signal_connect('config_changed', self.on_config_changed)
        self.on_config_changed(engine.config)
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
        ontop = settings.value('ontop', None, bool)
        if ontop is not None:
            self.action_ToggleOnTop.setChecked(ontop)
            self.on_toggle_ontop(ontop)

    def _save_state(self, settings):
        for name in (
            'text_font',
            'strokes_font',
        ):
            font = self._get_font(name)
            font_string = font.toString()
            settings.setValue(name, font_string)
        ontop = bool(self.windowFlags() & Qt.WindowStaysOnTopHint)
        settings.setValue('ontop', ontop)

    def _show_suggestions(self, suggestion_list):
        self.suggestions.append(suggestion_list)
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

        # Check for new output.
        for a in reversed(new):
            if a.text and not a.text.isspace():
                break
        else:
            return

        # Get previous words equal to the maximum possible search result count.
        with self._engine:
            last_translations = self._engine.translator_state.translations
            retro_formatter = RetroFormatter(last_translations)
            split_words = retro_formatter.last_words(self._search_limit, rx=self.WORD_RX)

        suggestion_list = []
        for phrase in self.tails(split_words):
            phrase = ''.join(phrase)
            suggestion_list.extend(self._engine.get_suggestions(phrase))

        if not suggestion_list and split_words:
            suggestion_list = [Suggestion(split_words[-1], [])]

        if suggestion_list and suggestion_list != self._last_suggestions:
            self._last_suggestions = suggestion_list
            self._show_suggestions(suggestion_list)

    def on_config_changed(self, config_update):
        if 'search_word_limit' in config_update:
            self._word_limit = config_update.get('search_word_limit')
        if 'search_stroke_limit' in config_update:
            self.suggestions.set_stroke_limit(config_update.get('search_stroke_limit'))

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
