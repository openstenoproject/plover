from contextlib import contextmanager
import functools
import os

from PyQt5.QtCore import (
    QItemSelection,
    QItemSelectionModel,
    QVariant,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QMenu,
    QTableWidgetItem,
    QWidget,
)

from plover.config import DictionaryConfig
from plover.dictionary.base import create_dictionary
from plover.engine import ErroredDictionary
from plover.misc import normalize_path
from plover.oslayer.config import CONFIG_DIR
from plover.registry import registry
from plover import log

from plover.gui_qt.dictionaries_widget_ui import _, Ui_DictionariesWidget
from plover.gui_qt.dictionary_editor import DictionaryEditor
from plover.gui_qt.utils import ToolBar


def _dictionary_formats(include_readonly=True):
    return {plugin.name
            for plugin in registry.list_plugins('dictionary')
            if include_readonly or not plugin.obj.readonly}

def _dictionary_filters(include_readonly=True):
    formats = sorted(_dictionary_formats(include_readonly=include_readonly))
    filters = ['*.' + ext for ext in formats]
    # i18n: Widget: “DictionariesWidget”, file picker.
    filters = [_('Dictionaries ({extensions})').format(extensions=' '.join(filters))]
    filters.extend(
        # i18n: Widget: “DictionariesWidget”, file picker.
        _('{format} dictionaries ({extensions})').format(
            format=ext.strip('.').upper(),
            extensions='*.' + ext,
        )
        for ext in formats
    )
    return ';; '.join(filters)

@contextmanager
def _new_dictionary(filename):
    try:
        d = create_dictionary(filename, threaded_save=False)
        yield d
        d.save()
    except Exception as e:
        raise Exception('creating dictionary %s failed. %s' % (filename, e)) from e


class DictionariesWidget(QWidget, Ui_DictionariesWidget):

    add_translation = pyqtSignal(QVariant)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        engine = QApplication.instance().engine
        self._engine = engine
        self._states = []
        self._updating = False
        self._config_dictionaries = {}
        self._loaded_dictionaries = {}
        self._reverse_order = False
        # The save/open/new dialogs will open on that directory.
        self._file_dialogs_directory = CONFIG_DIR
        for action in (
            self.action_Undo,
            self.action_EditDictionaries,
            self.action_SaveDictionaries,
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
        # Add menu.
        self.menu_AddDictionaries = QMenu(self.action_AddDictionaries.text())
        self.menu_AddDictionaries.setIcon(self.action_AddDictionaries.icon())
        self.menu_AddDictionaries.addAction(
            # i18n: Widget: “DictionariesWidget”, “add” menu.
            _('Open dictionaries'),
        ).triggered.connect(self._add_existing_dictionaries)
        self.menu_AddDictionaries.addAction(
            # i18n: Widget: “DictionariesWidget”, “add” menu.
            _('New dictionary'),
        ).triggered.connect(self._create_new_dictionary)
        # Save menu.
        self.menu_SaveDictionaries = QMenu(self.action_SaveDictionaries.text())
        self.menu_SaveDictionaries.setIcon(self.action_SaveDictionaries.icon())
        self.menu_SaveDictionaries.addAction(
            # i18n: Widget: “DictionariesWidget”, “save” menu.
            _('Create a copy of each dictionary'),
        ).triggered.connect(self._save_dictionaries)
        self.menu_SaveDictionaries.addAction(
            # i18n: Widget: “DictionariesWidget”, “save” menu.
            _('Merge dictionaries into a new one'),
        ).triggered.connect(functools.partial(self._save_dictionaries,
                                               merge=True))
        self.table.supportedDropActions = self._supported_drop_actions
        self.table.dragEnterEvent = self._drag_enter_event
        self.table.dragMoveEvent = self._drag_move_event
        self.table.dropEvent = self._drop_event
        engine.signal_connect('config_changed', self.on_config_changed)
        engine.signal_connect('dictionaries_loaded', self.on_dictionaries_loaded)

    def setFocus(self):
        self.table.setFocus()

    def on_dictionaries_loaded(self, loaded_dictionaries):
        self._update_dictionaries(loaded_dictionaries=loaded_dictionaries,
                                  record=False, save=False)

    def on_config_changed(self, config_update):
        update_kwargs = {}
        if 'dictionaries' in config_update:
            update_kwargs.update(
                config_dictionaries=config_update['dictionaries'],
                record=False, save=False, reset_undo=True
            )
        if 'classic_dictionaries_display_order' in config_update:
            update_kwargs.update(
                reverse_order=config_update['classic_dictionaries_display_order'],
                record=False, save=False,
            )
        if update_kwargs:
            self._update_dictionaries(**update_kwargs)

    def _update_dictionaries(self, config_dictionaries=None, loaded_dictionaries=None,
                             reverse_order=None, record=True, save=True,
                             reset_undo=False, keep_selection=True):
        if reverse_order is None:
            reverse_order = self._reverse_order
        if config_dictionaries is None:
            config_dictionaries = self._config_dictionaries
        if config_dictionaries == self._config_dictionaries and \
           reverse_order == self._reverse_order and \
           loaded_dictionaries is None:
            return
        if save:
            self._engine.config = { 'dictionaries': config_dictionaries }
        if record:
            self._states.append(self._config_dictionaries)
            self.action_Undo.setEnabled(True)
        if keep_selection:
            selected = [
                self._config_dictionaries[row].path
                for row in self._get_selection()
            ]
        self._config_dictionaries = config_dictionaries
        if loaded_dictionaries is None:
            loaded_dictionaries = self._loaded_dictionaries
        else:
            self._loaded_dictionaries = loaded_dictionaries
        self._reverse_order = reverse_order
        self._updating = True
        self.table.setRowCount(len(config_dictionaries))
        favorite_set = False
        for n, dictionary in enumerate(config_dictionaries):
            row = n
            if self._reverse_order:
                row = len(config_dictionaries) - row - 1
            item = QTableWidgetItem(dictionary.short_path)
            item.setFlags((item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsEditable)
            item.setCheckState(Qt.Checked if dictionary.enabled else Qt.Unchecked)
            item.setToolTip(dictionary.path)
            self.table.setItem(row, 0, item)
            item = QTableWidgetItem(str(n + 1))
            if dictionary.path not in loaded_dictionaries:
                icon = 'loading'
                # i18n: Widget: “DictionariesWidget”, tooltip.
                tooltip = _('This dictionary is being loaded.')
            else:
                d = loaded_dictionaries.get(dictionary.path)
                if isinstance(d, ErroredDictionary):
                    icon = 'error'
                    tooltip = str(d.exception)
                elif d.readonly:
                    icon = 'readonly'
                    # i18n: Widget: “DictionariesWidget”, tooltip.
                    tooltip = _('This dictionary is read-only.')
                elif not favorite_set and dictionary.enabled:
                    icon = 'favorite'
                    # i18n: Widget: “DictionariesWidget”, tooltip.
                    tooltip = _('This dictionary is marked as a favorite.')
                    favorite_set = True
                else:
                    icon = 'normal'
                    tooltip = ''
            item.setIcon(QIcon(':/dictionary_%s.svg' % icon))
            item.setToolTip(tooltip)
            self.table.setVerticalHeaderItem(row, item)
        if keep_selection:
            row_list = []
            for path in selected:
                for n, d in enumerate(config_dictionaries):
                    if d.path == path:
                        row_list.append(n)
                        break
            self._set_selection(row_list)
        if reset_undo:
            self.action_Undo.setEnabled(False)
            self._states = []
        self._updating = False
        self.on_selection_changed()

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
        dictionaries = self._config_dictionaries[:]
        dest_item = self.table.itemAt(event.pos())
        if dest_item is None:
            if self._reverse_order:
                dest_index = 0
            else:
                dest_index = len(self._config_dictionaries)
        else:
            dest_index = dest_item.row()
            if self._reverse_order:
                dest_index = len(self._config_dictionaries) - dest_index - 1
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
            row_count = len(self._config_dictionaries)
            row_list = [row_count - row - 1 for row in row_list]
        row_list.sort()
        return row_list

    def _set_selection(self, row_list):
        selection = QItemSelection()
        model = self.table.model()
        for row in row_list:
            if self._reverse_order:
                row = len(self._config_dictionaries) - row - 1
            index = model.index(row, 0)
            selection.select(index, index)
        self.table.selectionModel().select(selection, QItemSelectionModel.Rows |
                                           QItemSelectionModel.ClearAndSelect |
                                           QItemSelectionModel.Current)

    def on_selection_changed(self):
        if self._updating:
            return
        selection = self._get_selection()
        has_selection = bool(selection)
        for widget in (
            self.action_RemoveDictionaries,
            self.action_MoveDictionariesUp,
            self.action_MoveDictionariesDown,
        ):
            widget.setEnabled(has_selection)
        has_live_selection = any(
            self._config_dictionaries[row].path in self._loaded_dictionaries
            for row in selection
        )
        for widget in (
            self.action_EditDictionaries,
            self.action_SaveDictionaries,
            self.menu_SaveDictionaries,
        ):
            widget.setEnabled(has_live_selection)

    def on_dictionary_changed(self, item):
        if self._updating:
            return
        row = item.row()
        if self._reverse_order:
            row = len(self._config_dictionaries) - row - 1
        dictionaries = self._config_dictionaries[:]
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
        self._edit([self._config_dictionaries[row]])

    def on_edit_dictionaries(self):
        selection = self._get_selection()
        assert selection
        self._edit([self._config_dictionaries[row] for row in selection])

    def _get_dictionary_save_name(self, title, default_name=None,
                                  default_extensions=(), initial_filename=None):
        if default_name is not None:
            # Default to a writable dictionary format.
            writable_extensions = set(_dictionary_formats(include_readonly=False))
            default_name += '.' + next((e for e in default_extensions
                                        if e in writable_extensions),
                                       'json')
            default_name = os.path.join(self._file_dialogs_directory, default_name)
        else:
            default_name = self._file_dialogs_directory
        new_filename = QFileDialog.getSaveFileName(
            parent=self, caption=title, directory=default_name,
            filter=_dictionary_filters(include_readonly=False),
        )[0]
        if not new_filename:
            return None
        new_filename = normalize_path(new_filename)
        self._file_dialogs_directory = os.path.dirname(new_filename)
        if new_filename == initial_filename:
            return None
        return new_filename

    def _copy_dictionaries(self, dictionaries_list):
        need_reload = False
        # i18n: Widget: “DictionariesWidget”, “save as copy” file picker.
        title_template = _('Save a copy of {name} as...')
        # i18n: Widget: “DictionariesWidget”, “save as copy” file picker.
        default_name_template = _('{name} - Copy')
        for dictionary in dictionaries_list:
            title = title_template.format(name=dictionary.short_path)
            name, ext = os.path.splitext(os.path.basename(dictionary.path))
            default_name = default_name_template.format(name=name)
            new_filename = self._get_dictionary_save_name(title, default_name, [ext[1:]],
                                                          initial_filename=dictionary.path)
            if new_filename is None:
                continue
            with _new_dictionary(new_filename) as d:
                d.update(self._loaded_dictionaries[dictionary.path])
            need_reload = True
        return need_reload

    def _merge_dictionaries(self, dictionaries_list):
        names, exts = zip(*(
            os.path.splitext(os.path.basename(d.path))
            for d in dictionaries_list))
        default_name = ' + '.join(names)
        default_exts = list(dict.fromkeys(e[1:] for e in exts))
        # i18n: Widget: “DictionariesWidget”, “save as merge” file picker.
        title = _('Merge {names} as...').format(names=default_name)
        new_filename = self._get_dictionary_save_name(title, default_name, default_exts)
        if new_filename is None:
            return False
        with _new_dictionary(new_filename) as d:
            # Merge in reverse priority order, so higher
            # priority entries overwrite lower ones.
            for dictionary in reversed(dictionaries_list):
                d.update(self._loaded_dictionaries[dictionary.path])
        return True

    def _save_dictionaries(self, merge=False):
        selection = self._get_selection()
        assert selection
        dictionaries_list = [self._config_dictionaries[row]
                             for row in selection]
        # Ignore dictionaries that are not loaded.
        dictionaries_list = [dictionary
                             for dictionary in dictionaries_list
                             if dictionary.path in self._loaded_dictionaries]
        if not dictionaries_list:
            return
        if merge:
            save_fn = self._merge_dictionaries
        else:
            save_fn = self._copy_dictionaries
        if save_fn(dictionaries_list):
            # This will trigger a reload of any modified dictionary.
            self._engine.config = {}

    def on_remove_dictionaries(self):
        selection = self._get_selection()
        assert selection
        dictionaries = self._config_dictionaries[:]
        for row in sorted(selection, reverse=True):
            del dictionaries[row]
        self._update_dictionaries(dictionaries, keep_selection=False)

    def on_add_dictionaries(self):
        self.menu_AddDictionaries.exec_(QCursor.pos())

    def _add_existing_dictionaries(self):
        new_filenames = QFileDialog.getOpenFileNames(
            # i18n: Widget: “DictionariesWidget”, “add” file picker.
            parent=self, caption=_('Add dictionaries'),
            directory=self._file_dialogs_directory,
            filter=_dictionary_filters(),
        )[0]
        dictionaries = self._config_dictionaries[:]
        for filename in new_filenames:
            filename = normalize_path(filename)
            self._file_dialogs_directory = os.path.dirname(filename)
            for d in dictionaries:
                if d.path == filename:
                    break
            else:
                dictionaries.insert(0, DictionaryConfig(filename))
        self._update_dictionaries(dictionaries, keep_selection=False)

    def _create_new_dictionary(self):
        # i18n: Widget: “DictionariesWidget”, “new” file picker.
        new_filename = self._get_dictionary_save_name(_('New dictionary'))
        if new_filename is None:
            return
        with _new_dictionary(new_filename) as d:
            pass
        dictionaries = self._config_dictionaries[:]
        for d in dictionaries:
            if d.path == new_filename:
                break
        else:
            dictionaries.insert(0, DictionaryConfig(new_filename))
        # Note: pass in `loaded_dictionaries` to force update (use case:
        # the user decided to overwrite an already loaded dictionary).
        self._update_dictionaries(dictionaries, keep_selection=False,
                                  loaded_dictionaries=self._loaded_dictionaries)

    def on_add_translation(self):
        selection = self._get_selection()
        if selection:
            dictionary_path = self._config_dictionaries[selection[0]].path
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
        dictionaries = self._config_dictionaries[:]
        selection = []
        min_row = 0
        for old_row in self._get_selection():
            new_row = max(min_row, old_row - 1)
            dictionaries.insert(new_row, dictionaries.pop(old_row))
            selection.append(new_row)
            min_row = new_row + 1
        if dictionaries == self._config_dictionaries:
            return
        self._update_dictionaries(dictionaries)

    def _decrease_dictionaries_priority(self):
        dictionaries = self._config_dictionaries[:]
        selection = []
        max_row = len(dictionaries) - 1
        for old_row in reversed(self._get_selection()):
            new_row = min(max_row, old_row + 1)
            dictionaries.insert(new_row, dictionaries.pop(old_row))
            selection.append(new_row)
            max_row = new_row - 1
        if dictionaries == self._config_dictionaries:
            return
        self._update_dictionaries(dictionaries)
