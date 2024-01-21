from PyQt5.QtGui import QValidator

from plover.steno import normalize_steno


class StenoValidator(QValidator):

    def validate(self, text, pos):
        if not text.strip('-/'):
            state = QValidator.Intermediate
        else:
            prefix = text.rstrip('-/')
            if text == prefix:
                state = QValidator.Acceptable
                steno = text
            else:
                state = QValidator.Intermediate
                steno = prefix
            try:
                normalize_steno(steno)
            except ValueError:
                state = QValidator.Invalid
        return state, text, pos
