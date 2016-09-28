import re
from operator import attrgetter, itemgetter
from collections import namedtuple
from itertools import chain

# Python 2/3 compatibility.
from six import iteritems

from PyQt5.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QPoint)
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QStyledItemDelegate,
    QMenu,
    QToolTip,
    QAction)

from plover.translation import escape_translation, unescape_translation
from plover.misc import expand_path, shorten_path
from plover.steno import (
    filter_entry,
    normalize_steno,
    normalized_steno_to_indexes
)

from plover.gui_qt.dictionary_editor_ui import Ui_DictionaryEditor
from plover.gui_qt.utils import ToolBar, WindowState


_COL_STENO, _COL_TRANS, _COL_DICT, _COL_NUM_STROKES, _COL_NUM_WORDS, _COL_COUNT = range(5 + 1)


class DictionaryItem(namedtuple('DictionaryItem', 'strokes translation dictionary')):

    @property
    def dictionary_path(self):
        return self.dictionary.get_path()


class DictionaryItemDelegate(QStyledItemDelegate):

    def __init__(self, dictionary_list):
        super(DictionaryItemDelegate, self).__init__()
        self._dictionary_list = dictionary_list

    def createEditor(self, parent, option, index):
        if index.column() == _COL_DICT:
            dictionary_paths = [
                shorten_path(dictionary.get_path())
                for dictionary in self._dictionary_list
                if not dictionary.readonly
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

    def _update_entries(self, strokes_filter=None, translation_filter=None,
                        case_sensitive=False, regex=None):
        self._entries = []
        for dictionary in self._dictionary_list:
            for strokes, translation in iteritems(dictionary):
                if filter_entry(strokes, translation, strokes_filter,
                                translation_filter, case_sensitive, regex):
                    self._entries.append(
                        DictionaryItem(strokes, translation, dictionary)
                    )
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
            self.dataChanged.emit(self.index(row, _COL_STENO),
                                  self.index(row, _COL_TRANS))

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
        return _COL_COUNT

    def headerData(self, section, orientation, role):
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return None
        if section == _COL_STENO:
            return _('Strokes')
        if section == _COL_TRANS:
            return _('Translation')
        if section == _COL_DICT:
            return _('Dictionary')
        if section == _COL_NUM_STROKES:
            return _('# Strokes')
        if section == _COL_NUM_WORDS:
            return _('# Words')

    def data(self, index, role):
        if not index.isValid() or role not in (Qt.EditRole, Qt.DisplayRole):
            return None
        item = self._entries[index.row()]
        column = index.column()
        if column == _COL_STENO:
            return '/'.join(item.strokes)
        if column == _COL_TRANS:
            return escape_translation(item.translation)
        if column == _COL_DICT:
            return shorten_path(item.dictionary.get_path())
        if column == _COL_NUM_STROKES:
            return len(item.strokes)
        if column == _COL_NUM_WORDS:
            return len(item.translation.split(' '))

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        editable = Qt.ItemIsEditable if index.column() <= 2 else 0
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable | editable
        item = self._entries[index.row()]
        if not item.dictionary.readonly:
            f |= Qt.ItemIsEditable
        return f

    def filter(self, strokes_filter=None, translation_filter=None,
               case_sensitive=False, regex=None):
        self.modelAboutToBeReset.emit()
        self._update_entries(
            strokes_filter, translation_filter, case_sensitive, regex
        )
        self.modelReset.emit()

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        if column == _COL_STENO:
            key = lambda entry: normalized_steno_to_indexes(entry.strokes)
        elif column == _COL_DICT:
            key = attrgetter('dictionary_path')
        elif column == _COL_NUM_STROKES:
            key = lambda entry: len(entry.strokes)
        elif column == _COL_NUM_WORDS:
            key = lambda entry: len(entry.translation.split(' '))
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
        if column == _COL_STENO:
            strokes = normalize_steno(value.strip())
            if not strokes or strokes == old_item.strokes:
                return False
        elif column == _COL_TRANS:
            translation = unescape_translation(value.strip())
            if translation == old_item.translation:
                return False
        elif column == _COL_DICT:
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
        sort_column, sort_order = _COL_STENO, Qt.AscendingOrder
        self._model = DictionaryItemModel(dictionary_list,
                                          sort_column,
                                          sort_order)
        self._model.rowsInserted.connect(self.on_row_changed)
        self._model.rowsRemoved.connect(self.on_row_changed)
        self._model.dataChanged.connect(self.on_data_changed)
        self.table.sortByColumn(sort_column, sort_order)
        self.table.setModel(self._model)
        self.table.setSortingEnabled(True)
        self._reflow_columns()
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 200)
        self.table.resizeColumnToContents(3)
        self.table.resizeColumnToContents(4)
        self.table.setItemDelegate(DictionaryItemDelegate(dictionary_list))
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        headers = self.table.horizontalHeader()
        headers.setContextMenuPolicy(Qt.CustomContextMenu)
        headers.customContextMenuRequested.connect(self._column_selector)
        self.table.horizontalHeader().setSectionsMovable(True)
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

    def _reflow_columns(self):
        # For each column, we want to:
        #  Resize it to its contents
        #  If the resize brings it over 200px, bring it back
        self.table.resizeColumnsToContents()
        # Temporarily disable the final column's stretch.
        self.table.horizontalHeader().setStretchLastSection(False)
        columns = self._model.columnCount(self.table)
        for index in range(columns):
            if self.table.columnWidth(index) > 200:
                self.table.setColumnWidth(index, 200)
        self.table.horizontalHeader().setStretchLastSection(True)

    def _column_selector(self, position):
        headers = self.table.horizontalHeader()
        position = headers.mapToGlobal(position)

        menu = QMenu()

        header_count = headers.count()
        for section in range(header_count):
            title = self._model.headerData(
                section, Qt.Horizontal, Qt.DisplayRole
            )
            header_action = QAction(title, self)
            visible = (not headers.isSectionHidden(section))
            header_action.setData((section, visible))
            header_action.setCheckable(True)
            header_action.setChecked(visible)
            menu.addAction(header_action)
        selection = menu.exec(position)
        if selection:
            section, visible = selection.data()
            # Don't let the user hide the last column.
            visible_headers = header_count - headers.hiddenSectionCount()
            if visible and visible_headers == 1:
                return
            headers.setSectionHidden(section, visible)
            self._reflow_columns()

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
        translation_filter = self.translation_filter.text()
        unescaped_translation_filter = unescape_translation(translation_filter)
        case_sensitive = self.case_checkbox.checkState()
        is_regex = self.regex_checkbox.checkState()
        try:
            regex = re.compile(
                translation_filter, flags=0 if case_sensitive else re.I
            ) if is_regex else None
        except re.error as e:
            # Invalid regex, don't apply filter.
            QToolTip.showText(
                self.translation_filter.mapToGlobal(QPoint(0,0)),
                'RegEx did not compile: %s' % str(e)
            )
            return
        else:
            # Regex overrides some other filter criteria
            if regex:
                unescaped_translation_filter=None
                strokes_filter=None
                case_sensitive=None
        self._model.filter(strokes_filter, unescaped_translation_filter,
                           case_sensitive, regex)

    def on_clear_filter(self):
        self.strokes_filter.setText('')
        self.translation_filter.setText('')
        self.case_checkbox.setChecked(False)
        self.regex_checkbox.setChecked(False)
        self._model.filter()

    def on_finished(self, result):
        with self._engine:
            self._engine.dictionaries.save(dictionary.get_path()
                                           for dictionary
                                           in self._model.modified)
