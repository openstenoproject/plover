from PyQt5.QtGui import (
    QFont,
    QTextCursor,
    QTextCharFormat,
)
from PyQt5.QtWidgets import QTextEdit

from plover import _
from plover.translation import escape_translation


class SuggestionsWidget(QTextEdit):

    STYLE_TRANSLATION, STYLE_STROKES = range(2)

    # Anatomy of the text document:
    # - "root":
    #  - 0+ "suggestions" blocks
    #   - 1+ "translation" blocks
    #    - 1-10 "strokes" blocks

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self._translation_char_format = QTextCharFormat()
        self._strokes_char_format = QTextCharFormat()
        self._strokes_char_format.font().setStyleHint(QFont.Monospace)

    def append(self, suggestion_list):
        scrollbar = self.verticalScrollBar()
        scroll_at_end = scrollbar.value() == scrollbar.maximum()
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        for suggestion in suggestion_list:
            cursor.insertBlock()
            cursor.setCharFormat(self._translation_char_format)
            cursor.block().setUserState(self.STYLE_TRANSLATION)
            cursor.insertText(escape_translation(suggestion.text) + ':')
            if not suggestion.steno_list:
                # i18n: Widget: “SuggestionsWidget”.
                cursor.insertText(' ' + _('no suggestions'))
                continue
            for strokes_list in suggestion.steno_list[:10]:
                cursor.insertBlock()
                cursor.setCharFormat(self._strokes_char_format)
                cursor.block().setUserState(self.STYLE_STROKES)
                cursor.insertText('   ' + '/'.join(strokes_list))
        cursor.insertText('\n')
        # Keep current position when not at the end of the document.
        if scroll_at_end:
            scrollbar.setValue(scrollbar.maximum())

    def _reformat(self):
        document = self.document()
        cursor = self.textCursor()
        block = document.begin()
        style_format = {
            self.STYLE_TRANSLATION: self._translation_char_format,
            self.STYLE_STROKES: self._strokes_char_format,
        }
        while block != document.end():
            style = block.userState()
            fmt = style_format.get(style)
            if fmt is not None:
                cursor.setPosition(block.position())
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.setCharFormat(fmt)
            block = block.next()

    @property
    def text_font(self):
        return self._translation_char_format.font()

    @text_font.setter
    def text_font(self, font):
        self._translation_char_format.setFont(font)
        self._reformat()

    @property
    def strokes_font(self):
        return self._strokes_char_format.font()

    @strokes_font.setter
    def strokes_font(self, font):
        self._strokes_char_format.setFont(font)
        self._reformat()
