
from operator import attrgetter, itemgetter
from collections import namedtuple
from itertools import chain

# Python 2/3 compatibility.
from six import iteritems

from PyQt5.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
)
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QStyledItemDelegate,
)

from plover.translation import escape_translation, unescape_translation
from plover.misc import expand_path, shorten_path
from plover.steno import normalize_steno

from plover.gui_qt.dictionary_editor_ui import Ui_DictionaryEditor
from plover.gui_qt.utils import ToolBar, WindowState


class DictionaryItem(namedtuple('DictionaryItem', 'strokes translation dictionary')):

    @property
    def dictionary_path(self):
        return self.dictionary.get_path()


class DictionaryItemDelegate(QStyledItemDelegate):

    def __init__(self, dictionary_list):
        super(DictionaryItemDelegate, self).__init__()
        self._dictionary_list = dictionary_list

    def createEditor(self, parent, option, index):
        if index.column() == 2:
            dictionary_paths = [
                shorten_path(dictionary.get_path())
                for dictionary in self._dictionary_list
            ]
            combo = QComboBox(parent)
            combo.addItems(dictionary_paths)
            return combo
        return super(DictionaryItemDelegate, self).createEditor(parent, option, index)


class DictionaryItemModel(QAbstractTableModel):

    def __init__(self, dictionary_list, sort_column, sort_order):
        super(DictionaryItemModel, self).__init__()
        self._dictionary_list = dictionary_list
        self._operations = []
        self._entries = []
        self._sort_column = sort_column
        self._sort_order = sort_order
        self._update_entries()

    def _update_entries(self, strokes_filter=None, translation_filter=None):
        self._entries = []
        for dictionary in self._dictionary_list:
            for strokes, translation in iteritems(dictionary):
                if strokes_filter is not None and \
                   not '/'.join(strokes).startswith(strokes_filter):
                    continue
                if translation_filter is not None and \
                   not translation.startswith(translation_filter):
                    continue
                item = DictionaryItem(strokes, translation, dictionary)
                self._entries.append(item)
        self.sort(self._sort_column, self._sort_order)

    @property
    def has_undo(self):
        return bool(self._operations)

    @property
    def modified(self):
        paths = set()
        dictionary_list = []
        for op_list in self._operations:
            if not isinstance(op_list, list):
                op_list = (op_list,)
            for item in chain(*op_list):
                if item is None:
                    continue
                dictionary = item.dictionary
                if dictionary.get_path() in paths:
                    continue
                paths.add(dictionary.get_path())
                dictionary_list.append(dictionary)
        return dictionary_list

    # Note:
    # - since switching from a dictionary to a table does not enforce the
    #   unicity of keys, a deletion can fail when one of the duplicate has
    #   already been deleted.
    # - when undoing an operation at the table level, the item may have
    #   been filtered-out and not present

    def _undo(self, old_item, new_item):
        if old_item is None:
            # Undo addition.
            try:
                del new_item.dictionary[new_item.strokes]
            except KeyError:
                pass
            try:
                row = self._entries.index(new_item)
            except ValueError:
                # Happen if the item is filtered-out.
                pass
            else:
                self.remove_rows([row], record=False)
            return
        if new_item is None:
            # Undo deletion.
            self.new_row(0, item=old_item, record=False)
            return
        # Undo update.
        try:
            del new_item.dictionary[new_item.strokes]
        except KeyError:
            pass
        try:
            row = self._entries.index(new_item)
        except ValueError:
            # Happen if the item is filtered-out,
            # "create" a new row so the user see
            # the result of the undo.
            self.new_row(0, item=old_item, record=False)
        else:
            old_item.dictionary[old_item.strokes] = old_item.translation
            self._entries[row] = old_item
            self.dataChanged.emit(self.index(row, 0),
                                  self.index(row, 1))

    def undo(self, op=None):
        op = self._operations.pop()
        if isinstance(op, list):
            for old_item, new_item in op:
                self._undo(old_item, new_item)
        else:
            self._undo(*op)

    def rowCount(self, parent):
        return 0 if parent.isValid() else len(self._entries)

    def columnCount(self, parent):
        return 3

    def headerData(self, section, orientation, role):
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return None
        if section == 0:
            return _('Strokes')
        if section == 1:
            return _('Translation')
        if section == 2:
            return _('Dictionary')

    def data(self, index, role):
        if not index.isValid() or role not in (Qt.EditRole, Qt.DisplayRole):
            return None
        item = self._entries[index.row()]
        column = index.column()
        if column == 0:
            return '/'.join(item.strokes)
        if column == 1:
            return escape_translation(item.translation)
        if column == 2:
            return shorten_path(item.dictionary.get_path())

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def filter(self, strokes_filter=None, translation_filter=None):
        self.modelAboutToBeReset.emit()
        self._update_entries(strokes_filter, translation_filter)
        self.modelReset.emit()

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        if column == 2:
            key = attrgetter('dictionary_path')
        else:
            key = itemgetter(column)
        self._entries.sort(key=key,
                           reverse=(order == Qt.DescendingOrder))
        self._sort_column = column
        self._sort_order = order
        self.layoutChanged.emit()

    def setData(self, index, value, role=Qt.EditRole, record=True):
        assert role == Qt.EditRole
        row = index.row()
        column = index.column()
        old_item = self._entries[row]
        strokes, translation, dictionary = old_item
        if column == 0:
            strokes = normalize_steno(value.strip())
            if not strokes or strokes == old_item.strokes:
                return False
        elif column == 1:
            translation = unescape_translation(value.strip())
            if translation == old_item.translation:
                return False
        elif column == 2:
            path = expand_path(value)
            for dictionary in self._dictionary_list:
                if dictionary.get_path() == path:
                    break
            if dictionary == old_item.dictionary:
                return False
        try:
            del old_item.dictionary[old_item.strokes]
        except KeyError:
            pass
        if not old_item.strokes and not old_item.translation:
            # Merge operations when editing a newly added row.
            if self._operations and self._operations[-1] == [(None, old_item)]:
                self._operations.pop()
                old_item = None
        new_item = DictionaryItem(strokes, translation, dictionary)
        self._entries[row] = new_item
        dictionary[strokes] = translation
        if record:
            self._operations.append((old_item, new_item))
        self.dataChanged.emit(index, index)
        return True

    def new_row(self, row, item=None, record=True):
        if item is None:
            if row == 0 and not self._entries:
                dictionary = self._dictionary_list[0]
            else:
                dictionary = self._entries[row].dictionary
            item = DictionaryItem((), '', dictionary)
        self.beginInsertRows(QModelIndex(), row, row)
        self._entries.insert(row, item)
        if record:
            self._operations.append((None, item))
        self.endInsertRows()

    def remove_rows(self, row_list, record=True):
        assert row_list
        operations = []
        for row in sorted(row_list, reverse=True):
            self.beginRemoveRows(QModelIndex(), row, row)
            item = self._entries.pop(row)
            self.endRemoveRows()
            try:
                del item.dictionary[item.strokes]
            except KeyError:
                pass
            else:
                operations.append((item, None))
        if record:
            self._operations.append(operations)


class DictionaryEditor(QDialog, Ui_DictionaryEditor, WindowState):

    ROLE = 'dictionary_editor'

    def __init__(self, engine, dictionary_paths, parent=None):
        super(DictionaryEditor, self).__init__(parent)
        self.setupUi(self)
        self._engine = engine
        with engine:
            dictionary_list = [
                dictionary
                for dictionary in engine.dictionaries.dicts
                if dictionary.get_path() in dictionary_paths
            ]
        sort_column, sort_order = 0, Qt.AscendingOrder
        self._model = DictionaryItemModel(dictionary_list,
                                          sort_column,
                                          sort_order)
        self._model.rowsInserted.connect(self.on_row_changed)
        self._model.rowsRemoved.connect(self.on_row_changed)
        self._model.dataChanged.connect(self.on_data_changed)
        self.table.sortByColumn(sort_column, sort_order)
        self.table.setModel(self._model)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.table.setItemDelegate(DictionaryItemDelegate(dictionary_list))
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        background = self.table.palette().highlightedText().color().name()
        text_color = self.table.palette().highlight().color().name()
        self.table.setStyleSheet('''
                                 QTableView::item:focus {
                                     background-color: %s;
                                     color: %s;
                                }''' % (background, text_color))
        self.table.setFocus()
        for action in (
            self.action_Undo,
            self.action_Delete,
        ):
            action.setEnabled(False)
        # Toolbar.
        self.layout().addWidget(ToolBar(
            self.action_Undo,
            self.action_Delete,
            self.action_New,
        ))
        self.restore_state()
        self.finished.connect(self.save_state)

    @property
    def _selection(self):
        return list(sorted(
            index.row() for index in
            self.table.selectionModel().selectedRows(0)
        ))

    def on_data_changed(self, top_left, bottom_right):
        self.table.setCurrentIndex(top_left)
        self.action_Undo.setEnabled(self._model.has_undo)

    def on_row_changed(self, parent, first, last):
        index = self._model.index(first, 0)
        self.table.setCurrentIndex(index)
        self.action_Undo.setEnabled(self._model.has_undo)

    def on_selection_changed(self):
        enabled = bool(self._selection)
        for action in (
            self.action_Delete,
        ):
            action.setEnabled(enabled)

    def on_undo(self):
        assert self._model.has_undo
        self._model.undo()
        self.action_Undo.setEnabled(self._model.has_undo)

    def on_delete(self):
        selection = self._selection
        assert selection
        self._model.remove_rows(selection)
        self.action_Undo.setEnabled(self._model.has_undo)

    def on_new(self):
        selection = self._selection
        if selection:
            row = self._selection[0]
        else:
            row = 0
        self._model.new_row(row)
        self.table.selectionModel().clearSelection()
        index = self._model.index(row, 0)
        self.table.setCurrentIndex(index)
        self.table.edit(index)

    def on_apply_filter(self):
        strokes_filter = '/'.join(normalize_steno(self.strokes_filter.text().strip()))
        translation_filter = unescape_translation(self.translation_filter.text().strip())
        self._model.filter(strokes_filter=strokes_filter,
                           translation_filter=translation_filter)

    def on_clear_filter(self):
        self.strokes_filter.setText('')
        self.translation_filter.setText('')
        self._model.filter(strokes_filter=None, translation_filter=None)

    def on_finished(self, result):
        with self._engine:
            self._engine.dictionaries.save(dictionary.get_path()
                                           for dictionary
                                           in self._model.modified)
