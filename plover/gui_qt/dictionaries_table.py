from PyQt5.QtWidgets import QTableWidget

class DictionariesTable(QTableWidget):
    def contextMenuEvent(self, event):
        row = self.rowAt(event.y())
        self.parent().on_table_context_menu(row, event.globalPos())
