from PyQt5.QtWidgets import QWidget, QMenu, QAction, QTableWidget

class DictionariesTable(QTableWidget):
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        saveAsAction = QAction("Save a Copy As...", self)
        row = self.rowAt(event.y())
        assert row >= 0
        saveAsAction.triggered.connect(lambda: self.parent().on_save_as(row))
        menu.addAction(saveAsAction)
        menu.popup(event.globalPos())

