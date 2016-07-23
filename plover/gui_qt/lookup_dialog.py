
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import (
    QDialog,
)

from plover.translation import unescape_translation

from plover.gui_qt.lookup_dialog_ui import Ui_LookupDialog
from plover.gui_qt.suggestions_widget import SuggestionsWidget
from plover.gui_qt.utils import WindowState


class LookupDialog(QDialog, Ui_LookupDialog, WindowState):

    ROLE = 'lookup'

    def __init__(self, engine):
        super(LookupDialog, self).__init__()
        self.setupUi(self)
        suggestions = SuggestionsWidget()
        self.layout().replaceWidget(self.suggestions, suggestions)
        self.suggestions = suggestions
        self._engine = engine
        self.pattern.installEventFilter(self)
        self.suggestions.installEventFilter(self)
        self.pattern.setFocus()
        self.restore_state()
        self.finished.connect(self.save_state)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and \
           event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return True
        return False

    def _update_suggestions(self, suggestion_list):
        self.suggestions.clear()
        self.suggestions.prepend(suggestion_list)

    def on_lookup(self, pattern):
        translation = unescape_translation(pattern.strip())
        suggestion_list = self._engine.get_suggestions(translation)
        self._update_suggestions(suggestion_list)
