from plover.steno import normalize_steno
from plover.gui.util import shorten_unicode
from plover.translation import escape_translation, unescape_translation

STROKE = "STROKE"
TRANSLATION = "TRANSLATION"
DICTIONARY = "DICTIONARY"
SPACER = "SPACER"

# GUI will respect the order here:
COLUMNS = [STROKE,
           TRANSLATION,
           DICTIONARY,
           SPACER]

COL_STROKE = COLUMNS.index(STROKE)
COL_TRANSLATION = COLUMNS.index(TRANSLATION)
COL_DICTIONARY = COLUMNS.index(DICTIONARY)
COL_SPACER = COLUMNS.index(SPACER)


class DictionaryItem(object):

    def __init__(self, stroke, translation, dictionary, id):

        if translation is None:
            translation = ''

        self.stroke = stroke
        self.translation = translation
        self.dictionary = dictionary
        self.id = id


class DictionaryEditorStore(object):

    def __init__(self, engine, config):

        self.config = config
        self.engine = engine

        self.all_keys = []
        self.filtered_keys = []
        self.sorted_keys = []

        self.modified_items = []
        self.added_items = []
        self.deleted_items = []

        self.sorting_column = -1
        self.sorting_mode = None

        item_id = 0
        self.new_id = -1

        self.pending_changes = False

        for dictionary in reversed(self.engine.get_dictionary().dicts):
            for dk, translation in dictionary.iteritems():
                joined = '/'.join(dk)
                item = DictionaryItem(joined,
                                      escape_translation(translation),
                                      dictionary,
                                      item_id)
                self.all_keys.append(item)
                item_id += 1
        self.filtered_keys = self.all_keys[:]
        self.sorted_keys = self.filtered_keys[:]

    def is_row_read_only(self, row):
        item = self.sorted_keys[row]
        return item.dictionary.save is None

    def GetNumberOfRows(self):
        return len(self.sorted_keys)

    def GetValue(self, row, col):
        item = self.sorted_keys[row]
        result = ""

        if col is COL_STROKE:
            result = item.stroke
        elif col is COL_TRANSLATION:
            result = shorten_unicode(item.translation)
        elif col is COL_DICTIONARY:
            result = item.dictionary.get_path()
        return result

    def SetValue(self, row, col, value):
        self.pending_changes = True
        item = self.sorted_keys[row]
        if item.id < 0:
            editing_item = self._getAddedItem(item.id)
        else:
            editing_item = self.all_keys[item.id]
        if col is COL_STROKE:
            editing_item.stroke = value
        elif col is COL_TRANSLATION:
            editing_item.translation = value
        if item.id >= 0:
            if item.id not in self.modified_items:
                self.modified_items.append(item.id)

    def GetSortColumn(self):
        return self.sorting_column

    def GetSortMode(self):
        return self.sorting_mode

    def ApplyFilter(self, stroke_filter, translation_filter):
        stroke_filter = '/'.join(normalize_steno(stroke_filter))
        self.filtered_keys = []
        self.sorted_keys = []
        for di in self.added_items:
            if self._itemMatchesFilter(di, stroke_filter, translation_filter):
                self.filtered_keys.append(di)
        for di in self.all_keys:
            if di not in self.deleted_items:
                if self._itemMatchesFilter(di,
                                           stroke_filter,
                                           translation_filter):
                    self.filtered_keys.append(di)
        self._applySort()

    def InsertNew(self, row):
        self.pending_changes = True
        selected_item = self.sorted_keys[row]
        item = DictionaryItem('', '', selected_item.dictionary, self.new_id)
        self.added_items.append(item)
        self.sorted_keys.insert(row, item)
        self.new_id -= 1

    def DeleteSelected(self, row):
        self.pending_changes = True
        item = self.sorted_keys[row]
        if item.id < 0:
            self.added_items.remove(item)
        else:
            self.deleted_items.append(item)
        self.sorted_keys.remove(item)

    def SaveChanges(self):
        self.pending_changes = False

        # Set of dictionaries (paths) that needs saving.
        needs_saving = set()

        # Creates
        for item in self.added_items:
            item.dictionary[normalize_steno(item.stroke)] = unescape_translation(item.translation)
            needs_saving.add(item.dictionary.get_path())

        # Updates
        for item_id in self.modified_items:
            item = self.all_keys[item_id]
            item.dictionary[normalize_steno(item.stroke)] = unescape_translation(item.translation)
            needs_saving.add(item.dictionary.get_path())

        # Deletes
        for item in self.deleted_items:
            del item.dictionary[normalize_steno(item.stroke)]
            needs_saving.add(item.dictionary.get_path())

        self.engine.get_dictionary().save(needs_saving)

    def Sort(self, column):
        if column is not COL_STROKE and column is not COL_TRANSLATION:
            return

        if self.sorting_column == column:
            # Already sorting on this column
            # Next sorting mode
            self.sorting_mode = self._cycleNextSortMode(self.sorting_mode)
        else:
            # Different column than the one currently being sorted
            self.sorting_column = column
            # First sorting mode
            self.sorting_mode = True
        self._applySort()

    def _getAddedItem(self, id):
        for di in self.added_items:
            if di.id == id:
                return di
        return None

    def _itemMatchesFilter(self, di, stroke_filter, translation_filter):
        stroke_add = False
        translation_add = False
        if stroke_filter:
            stroke = di.stroke
            if stroke:
                if stroke.lower().startswith(stroke_filter.lower()):
                    stroke_add = True
        else:
            stroke_add = True
        if translation_filter:
            translation = di.translation
            if translation:
                if translation.lower().startswith(translation_filter.lower()):
                    translation_add = True
        else:
            translation_add = True
        if stroke_add is True:
            if translation_add is True:
                return True
        return False

    def _cycleNextSortMode(self, sort_mode):
        if sort_mode is None:
            return True
        elif sort_mode is True:
            return False
        else:
            return None

    def _applySort(self):
        if self.sorting_mode is not None:
            reverse_sort = not self.sorting_mode
            if self.sorting_column is COL_STROKE:
                self.sorted_keys = sorted(self.filtered_keys,
                                          key=lambda x: x.stroke.lower(),
                                          reverse=reverse_sort)
            elif self.sorting_column is COL_TRANSLATION:
                self.sorted_keys = sorted(self.filtered_keys,
                                          key=lambda x: x.translation.lower(),
                                          reverse=reverse_sort)
        else:
            self.sorted_keys = self.filtered_keys[:]
