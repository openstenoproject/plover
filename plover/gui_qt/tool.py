
from PyQt5.QtWidgets import QDialog

from plover.gui_qt.utils import WindowState


class Tool(QDialog, WindowState):

    # Used for dialog window title, menu entry text.
    TITLE = None
    # Optional path to icon image.
    ICON = None
    # Optional shortcut (as a string).
    SHORTCUT = None
    # Note: the class documentation is automatically used as tooltip.

    def __init__(self, engine):
        super().__init__()
        self._update_title()
        self._engine = engine

    def _update_title(self):
        self.setWindowTitle('Plover: ' + self.TITLE)

    def setupUi(self, widget):
        super().setupUi(widget)
        self._update_title()
