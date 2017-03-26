
import os

from PyQt5.QtCore import (
    QItemSelection,
    QItemSelectionModel,
    QVariant,
    Qt,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QFileDialog,
    QTableWidgetItem,
    QWidget,
)

from plover.misc import shorten_path
from plover.registry import registry
from plover.config import DictionaryConfig

from plover.gui_qt.dictionaries_widget_ui import Ui_DictionariesWidget
from plover.gui_qt.dictionary_editor import DictionaryEditor
from plover.gui_qt.utils import ToolBar


def _dictionary_formats():
    return set(plugin.name for plugin in registry.list_plugins('dictionary'))


class DictionariesWidget(QWidget, Ui_DictionariesWidget):

    add_translation = pyqtSignal(QVariant)

    def __init__(self, engine):
        super(DictionariesWidget, self).__init__()
        self.setupUi(self)
        self._engine = engine
        self._states = []
        self._updating = False
        self._dictionaries = []
        self._reverse_order = False
        for action in (
            self.action_Undo,
            self.action_EditDictionaries,
            self.action_RemoveDictionaries,
            self.action_MoveDictionariesUp,
            self.action_MoveDictionariesDown,
        ):
            action.setEnabled(False)
        # Toolbar.
        self.layout().addWidget(ToolBar(
            self.action_Undo,
            None,
            self.action_EditDictionaries,
            self.action_RemoveDictionaries,
            self.action_AddDictionaries,
            self.action_AddTranslation,
            None,
            self.action_MoveDictionariesUp,
            self.action_MoveDictionariesDown,
        ))
        self.table.supportedDropActions = self._supported_drop_actions
        self.table.dragEnterEvent = self._drag_enter_event
        self.table.dragMoveEvent = self._drag_move_event
        self.table.dropEvent = self._drop_event
        engine.signal_connect('config_changed', self.on_config_changed)

    def setFocus(self):
        self.table.setFocus()

    def on_config_changed(self, config_update):
        update_kwargs = {}
        if 'dictionaries' in config_update:
            update_kwargs.update(
                dictionaries=config_update['dictionaries'],
                record=False, save=False, reset_undo=True
            )
        if 'classic_dictionaries_display_order' in config_update:
            update_kwargs.update(
                reverse_order=config_update['classic_dictionaries_display_order'],
                record=False, save=False,
            )
        if update_kwargs:
            self._update_dictionaries(**update_kwargs)

    def _update_dictionaries(self, dictionaries=None, reverse_order=None,
                             record=True, save=True, reset_undo=False,
                             keep_selection=True):
        if reverse_order is None:
            reverse_order = self._reverse_order
        if dictionaries is None:
            dictionaries = self._dictionaries
        if dictionaries == self._dictionaries and \
           reverse_order == self._reverse_order:
            return
        if save:
            self._engine.config = { 'dictionaries': dictionaries }
        if record:
            self._states.append(self._dictionaries)
            self.action_Undo.setEnabled(True)
        if keep_selection:
            selected = [
                self._dictionaries[row].path
                for row in self._get_selection()
            ]
        self._dictionaries = dictionaries
        self._reverse_order = reverse_order
        self._updating = True
        self.table.setRowCount(len(dictionaries))
        for n, dictionary in enumerate(dictionaries):
            item = QTableWidgetItem(dictionary.short_path)
            item.setFlags((item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsEditable)
            item.setCheckState(Qt.Checked if dictionary.enabled else Qt.Unchecked)
            row = n
            if self._reverse_order:
                row = len(dictionaries) - row - 1
            self.table.setItem(row, 0, item)
            item = QTableWidgetItem(str(n + 1))
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setVerticalHeaderItem(row, item)
        if keep_selection:
            row_list = []
            for path in selected:
                for n, d in enumerate(dictionaries):
                    if d.path == path:
                        row_list.append(n)
                        break
            self._set_selection(row_list)
        if reset_undo:
            self.action_Undo.setEnabled(False)
            self._states = []
        self._updating = False

    @staticmethod
    def _supported_drop_actions():
        return Qt.CopyAction | Qt.LinkAction | Qt.MoveAction

    def is_accepted_drag_event(self, event):
        if event.source() == self.table:
            return True
        mime = event.mimeData()
        if mime.hasUrls():
            for url in mime.urls():
                # Only support local files.
                if not url.isLocalFile():
                    break
                # And only allow supported extensions.
                filename = url.toLocalFile()
                extension = os.path.splitext(filename)[1].lower()[1:]
                if extension not in _dictionary_formats():
                    break
            else:
                return True
        return False

    def _drag_enter_event(self, event):
        if self.is_accepted_drag_event(event):
            event.accept()

    def _drag_move_event(self, event):
        if self.is_accepted_drag_event(event):
            event.accept()

    def _drop_event(self, event):
        if not self.is_accepted_drag_event(event):
            return
        dictionaries = self._dictionaries[:]
        dest_item = self.table.itemAt(event.pos())
        if dest_item is None:
            if self._reverse_order:
                dest_index = 0
            else:
                dest_index = len(self._dictionaries)
        else:
            dest_index = dest_item.row()
            if self._reverse_order:
                dest_index = len(self._dictionaries) - dest_index - 1
        if event.source() == self.table:
            sources = [
                dictionaries[row]
                for row in self._get_selection()
            ]
        else:
            sources = [
                DictionaryConfig(url.toLocalFile())
                for url in event.mimeData().urls()
            ]
        for dictionary in sources:
            try:
                source_index = [d.path for d in dictionaries].index(dictionary.path)
            except ValueError:
                pass
            else:
                if source_index == dest_index:
                    dest_index += 1
                    continue
                del dictionaries[source_index]
                if source_index < dest_index:
                    dest_index -= 1
            dictionaries.insert(dest_index, dictionary)
            dest_index += 1
        self._update_dictionaries(dictionaries, keep_selection=False)

    def _get_selection(self):
        row_list = [item.row() for item in self.table.selectedItems()]
        if self._reverse_order:
            row_count = len(self._dictionaries)
            row_list = [row_count - row - 1 for row in row_list]
        row_list.sort()
        return row_list

    def _set_selection(self, row_list):
        selection = QItemSelection()
        model = self.table.model()
        for row in row_list:
            if self._reverse_order:
                row = len(self._dictionaries) - row - 1
            index = model.index(row, 0)
            selection.select(index, index)
        self.table.selectionModel().select(selection, QItemSelectionModel.Rows |
                                           QItemSelectionModel.ClearAndSelect |
                                           QItemSelectionModel.Current)

    def on_selection_changed(self):
        if self._updating:
            return
        enabled = bool(self.table.selectedItems())
        for action in (
            self.action_RemoveDictionaries,
            self.action_EditDictionaries,
            self.action_MoveDictionariesUp,
            self.action_MoveDictionariesDown,
        ):
            action.setEnabled(enabled)

    def on_dictionary_changed(self, item):
        if self._updating:
            return
        row = item.row()
        if self._reverse_order:
            row = len(self._dictionaries) - row - 1
        dictionaries = self._dictionaries[:]
        dictionaries[row] = dictionaries[row].replace(
            enabled=bool(item.checkState() == Qt.Checked)
        )
        self._update_dictionaries(dictionaries)

    def on_undo(self):
        assert self._states
        dictionaries = self._states.pop()
        self.action_Undo.setEnabled(bool(self._states))
        self._update_dictionaries(dictionaries, record=False)

    def _edit(self, dictionaries):
        editor = DictionaryEditor(self._engine, [d.path for d in dictionaries])
        editor.exec_()

    def on_activate_cell(self, row, col):
        self._edit([self._dictionaries[row]])

    def on_edit_dictionaries(self):
        selection = self._get_selection()
        assert selection
        self._edit([self._dictionaries[row] for row in selection])

    def on_remove_dictionaries(self):
        selection = self._get_selection()
        assert selection
        dictionaries = self._dictionaries[:]
        for row in sorted(selection, reverse=True):
            del dictionaries[row]
        self._update_dictionaries(dictionaries, keep_selection=False)

    def on_add_dictionaries(self):
        filters = ['*.' + ext for ext in sorted(_dictionary_formats())]
        new_filenames = QFileDialog.getOpenFileNames(
            self, _('Add dictionaries'), None,
            _('Dictionary Files') + ' (%s)' % ' '.join(filters),
        )[0]
        dictionaries = self._dictionaries[:]
        for filename in new_filenames:
            for d in dictionaries:
                if d.path == filename:
                    break
            else:
                dictionaries.insert(0, DictionaryConfig(filename))
        self._update_dictionaries(dictionaries, keep_selection=False)

    def on_add_translation(self):
        selection = self._get_selection()
        if selection:
            dictionary_path = self._dictionaries[selection[0]].path
        else:
            dictionary_path = None
        self.add_translation.emit(dictionary_path)

    def on_move_dictionaries_up(self):
        if self._reverse_order:
            self._decrease_dictionaries_priority()
        else:
            self._increase_dictionaries_priority()

    def on_move_dictionaries_down(self):
        if self._reverse_order:
            self._increase_dictionaries_priority()
        else:
            self._decrease_dictionaries_priority()

    def _increase_dictionaries_priority(self):
        dictionaries = self._dictionaries[:]
        selection = []
        min_row = 0
        for old_row in self._get_selection():
            new_row = max(min_row, old_row - 1)
            dictionaries.insert(new_row, dictionaries.pop(old_row))
            selection.append(new_row)
            min_row = new_row + 1
        if dictionaries == self._dictionaries:
            return
        self._update_dictionaries(dictionaries)

    def _decrease_dictionaries_priority(self):
        dictionaries = self._dictionaries[:]
        selection = []
        max_row = len(dictionaries) - 1
        for old_row in reversed(self._get_selection()):
            new_row = min(max_row, old_row + 1)
            dictionaries.insert(new_row, dictionaries.pop(old_row))
            selection.append(new_row)
            max_row = new_row - 1
        if dictionaries == self._dictionaries:
            return
        self._update_dictionaries(dictionaries)
