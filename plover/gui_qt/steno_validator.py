from PySide6.QtGui import QValidator

from plover.steno import normalize_steno


class StenoValidator(QValidator):

    def validate(self, text, pos):
        if not text.strip('-/'):
            state = QValidator.State.Intermediate
        else:
            prefix = text.rstrip('-/')
            if text == prefix:
                state = QValidator.State.Acceptable
                steno = text
            else:
                state = QValidator.State.Intermediate
                steno = prefix
            try:
                normalize_steno(steno)
            except ValueError:
                state = QValidator.State.Invalid
        return state, text, pos
