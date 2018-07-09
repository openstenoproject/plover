
from PyQt5.QtCore import QEvent, Qt

from plover.translation import unescape_translation

from plover.gui_qt.lookup_dialog_ui import Ui_LookupDialog
from plover.gui_qt.i18n import get_gettext
from plover.gui_qt.tool import Tool

import re

_ = get_gettext()

matchStenoString = re.compile(r'[STKPWHRAO\*EUFBLGDZ\/-]')

class LookupDialog(Tool, Ui_LookupDialog):

    ''' Search the dictionary for translations. '''

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

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and \
           event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return True
        return False

    def _update_suggestions(self, suggestion_list):
        self.suggestions.replace(suggestion_list)

    def on_lookup(self, pattern):
        translation = unescape_translation(pattern.strip())
        # only bother if the search box has non-whitespace characters
        if translation:
            if self.regexCheck.isChecked():
                suggestion_list = self._engine.get_regex_suggestions(translation)
            else:
                suggestion_list = self._engine.get_suggestions(translation)
            if matchStenoString.match(translation):
                stroke_suggestion = self._engine.get_stroke_suggestion(translation)
                if stroke_suggestion is not None:
                    suggestion_list.append(stroke_suggestion) 
            self._update_suggestions(suggestion_list)
            
    def on_modeChange(self, state):
        self.on_lookup(self.pattern.text())
