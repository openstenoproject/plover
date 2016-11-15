
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
        super(Tool, self).__init__()
        self.setWindowTitle('Plover: ' + self.TITLE)
        self._engine = engine
