from PyQt5.QtGui import QValidator

import pytest

from plover.gui_qt.steno_validator import StenoValidator


@pytest.mark.parametrize(('text', 'state'), (
    # Acceptable.
    ('ST', QValidator.Acceptable),
    ('TEFT', QValidator.Acceptable),
    ('TEFT/-G', QValidator.Acceptable),
    ('/ST', QValidator.Acceptable),
    ('-F', QValidator.Acceptable),
    # Intermediate.
    ('-', QValidator.Intermediate),
    ('/', QValidator.Intermediate),
    ('/-', QValidator.Intermediate),
    ('ST/', QValidator.Intermediate),
    ('ST/-', QValidator.Intermediate),
    ('ST//', QValidator.Intermediate),
    # Invalid.
    ('WK', QValidator.Invalid),
    ('PLOVER', QValidator.Invalid),
))
def test_steno_validator_validate(text, state):
    validator = StenoValidator()
    assert validator.validate(text, len(text)) == (state, text, len(text))
