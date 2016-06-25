import wx
from wx.lib.utils import AdjustRectToScreen
import plover.gui.util as util
from plover.dictionary_editor_store import DictionaryEditorStore
from plover.dictionary_editor_store import COLUMNS
from plover.dictionary_editor_store import COL_STROKE
from plover.dictionary_editor_store import COL_TRANSLATION
from plover.dictionary_editor_store import COL_DICTIONARY
from plover.dictionary_editor_store import COL_SPACER
from wx.grid import EVT_GRID_LABEL_LEFT_CLICK, EVT_GRID_SELECT_CELL, EVT_GRID_RANGE_SELECT
from wx.grid import PyGridTableBase

TITLE = 'Plover: Dictionary Editor'

FILTER_BY_STROKE_TEXT = 'Filter by stroke:'
FILTER_BY_TRANSLATION_TEXT = 'Filter by translation:'
DO_FILTER_BUTTON_NAME = 'Filter'
INSERT_BUTTON_NAME = 'New Entry'
DELETE_BUTTON_NAME = 'Delete Selected'
SAVE_BUTTON_NAME = 'Save and Close'
CANCEL_BUTTON_NAME = 'Close'

NUM_COLS = len(COLUMNS)


class DictionaryEditor(wx.Dialog):

    BORDER = 3

    def __init__(self, parent, engine, config, on_exit):
        pos = (config.get_dictionary_editor_frame_x(),
               config.get_dictionary_editor_frame_y())
        wx.Dialog.__init__(self, parent, title=TITLE, pos=pos,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.config = config
        self.on_exit = on_exit

        # layout
        global_sizer = wx.BoxSizer(wx.VERTICAL)

        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)

        filter_left_sizer = wx.FlexGridSizer(2, 2, 4, 10)

        label = wx.StaticText(self, label=FILTER_BY_STROKE_TEXT)
        filter_left_sizer.Add(label,
                              flag=wx.ALIGN_CENTER_VERTICAL,
                              border=self.BORDER)

        self.filter_by_stroke = wx.TextCtrl(self,
                                            style=wx.TE_PROCESS_ENTER,
                                            size=wx.Size(200, 20))
        self.Bind(wx.EVT_TEXT_ENTER, self._do_filter, self.filter_by_stroke)
        filter_left_sizer.Add(self.filter_by_stroke)

        label = wx.StaticText(self, label=FILTER_BY_TRANSLATION_TEXT)
        filter_left_sizer.Add(label,
                              flag=wx.ALIGN_CENTER_VERTICAL,
                              border=self.BORDER)

        self.filter_by_translation = wx.TextCtrl(self,
                                                 style=wx.TE_PROCESS_ENTER,
                                                 size=wx.Size(200, 20))
        self.Bind(wx.EVT_TEXT_ENTER,
                  self._do_filter,
                  self.filter_by_translation)
        filter_left_sizer.Add(self.filter_by_translation)

        filter_sizer.Add(filter_left_sizer, flag=wx.ALL, border=self.BORDER)

        do_filter_button = wx.Button(self, label=DO_FILTER_BUTTON_NAME)
        self.Bind(wx.EVT_BUTTON, self._do_filter, do_filter_button)

        filter_sizer.Add(do_filter_button,
                         flag=wx.EXPAND | wx.ALL,
                         border=self.BORDER)

        global_sizer.Add(filter_sizer, flag=wx.ALL, border=self.BORDER)

        self.store = DictionaryEditorStore(engine, config)

        # Grid
        self.grid = DictionaryEditorGrid(self, size=wx.Size(800, 600))
        self.grid.CreateGrid(self.store, 0, NUM_COLS)

        self.grid.SetRowLabelSize(wx.grid.GRID_AUTOSIZE)

        self.grid.SetColSize(COL_STROKE, 250)
        self.grid.SetColSize(COL_TRANSLATION, 250)
        self.grid.SetColSize(COL_DICTIONARY, 150)

        global_sizer.Add(self.grid, 1, wx.EXPAND)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        insert_button = wx.Button(self, label=INSERT_BUTTON_NAME)
        self.Bind(wx.EVT_BUTTON, self._insert_new, insert_button)

        buttons_sizer.Add(insert_button, flag=wx.ALL, border=self.BORDER)

        delete_button = wx.Button(self, label=DELETE_BUTTON_NAME)
        self.Bind(wx.EVT_BUTTON, self._delete, delete_button)

        buttons_sizer.Add(delete_button, flag=wx.ALL, border=self.BORDER)

        buttons_sizer.Add((0, 0), 1, wx.EXPAND)

        save_button = wx.Button(self, label=SAVE_BUTTON_NAME)
        self.Bind(wx.EVT_BUTTON, self._save_close, save_button)

        buttons_sizer.Add(save_button, flag=wx.ALL, border=self.BORDER)

        cancel_button = wx.Button(self, label=CANCEL_BUTTON_NAME)
        self.Bind(wx.EVT_BUTTON, self._cancel_close, cancel_button)

        buttons_sizer.Add(cancel_button, flag=wx.ALL, border=self.BORDER)

        global_sizer.Add(buttons_sizer,
                         0,
                         flag=wx.EXPAND | wx.ALL,
                         border=self.BORDER)

        self.Bind(wx.EVT_MOVE, self._on_move)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        self.SetAutoLayout(True)
        self.SetSizer(global_sizer)
        global_sizer.Fit(self)
        global_sizer.SetSizeHints(self)
        self.Layout()
        self.SetRect(AdjustRectToScreen(self.GetRect()))

        self.last_window = util.GetForegroundWindow()

    def _do_filter(self, event=None):
        self.store.ApplyFilter(self.filter_by_stroke.GetValue(),
                               self.filter_by_translation.GetValue())
        self.grid.RefreshView()

    def _insert_new(self, event=None):
        self.grid.InsertNew()

    def _delete(self, event=None):
        self.grid.DeleteSelected()

    def _save_close(self, event=None):
        self.store.SaveChanges()
        self.Close()

    def _cancel_close(self, event=None):
        self.Close()

    def _on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_dictionary_editor_frame_x(pos[0])
        self.config.set_dictionary_editor_frame_y(pos[1])
        event.Skip()

    def _on_close(self, event=None):
        result = wx.ID_YES
        if self.store.pending_changes:
            dlg = wx.MessageDialog(self,
                                   "You will lose your changes. Are you sure?",
                                   "Cancel",
                                   wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
        if result == wx.ID_YES:
            try:
                util.SetForegroundWindow(self.last_window)
            except:
                pass
            self.on_exit()
            self.Destroy()


class DictionaryEditorGrid(wx.grid.Grid):
    """ Dictionary Manager's grid """
    GRID_LABEL_STROKE = "Stroke"
    GRID_LABEL_TRANSLATION = "Translation"
    GRID_LABEL_DICTIONARY = "Dictionary"
    GRID_LABEL_SPACER = " "
    sorted_labels = sorted([[COL_STROKE, GRID_LABEL_STROKE],
                            [COL_TRANSLATION, GRID_LABEL_TRANSLATION],
                            [COL_SPACER, GRID_LABEL_SPACER],
                            [COL_DICTIONARY, GRID_LABEL_DICTIONARY]])
    grid_labels = [pair[1] for pair in sorted_labels]

    def __init__(self, *args, **kwargs):
        wx.grid.Grid.__init__(self, *args, **kwargs)

        self.parent = args[0]

        self._changedRow = None

        # We need to keep track of the selection ourselves...
        self.Bind(EVT_GRID_SELECT_CELL, self._on_select_cell)
        self.Bind(EVT_GRID_RANGE_SELECT, self._on_select_range)
        self.selection = set()

    def CreateGrid(self, store, rows, cols):
        """ Create the grid """

        wx.grid.Grid.CreateGrid(self, rows, cols)
        wx.grid.Grid.DisableDragRowSize(self)
        # TODO: enable this when wx is fixed...
        # self.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)

        self.store = store

        # Set GridTable
        self._table = DictionaryEditorGridTable(self.store)
        self.SetTable(self._table)

        self._sortingColumn = 0
        self._sortingAsc = None

        self.Bind(EVT_GRID_LABEL_LEFT_CLICK, self._onLabelClick)

    def RefreshView(self):
        self._table.ResetView(self)

    def InsertNew(self):
        for row in self.selection:
            if not self.store.is_row_read_only(row):
                self.store.InsertNew(row)
                self._table.ResetView(self)
                self.SetFocus()
                self.ClearSelection()
                self.SelectRow(row)
                self.SetGridCursor(row, 0)
                self.MakeCellVisible(row, 0)
                break
        else:
            self.ClearSelection()

    def DeleteSelected(self):
        delete_selection = [row for row in self.selection
                            if not self.store.is_row_read_only(row)]
        if delete_selection:
            # Delete in reverse order, so row numbers are stable.
            for row in sorted(delete_selection, reverse=True):
                self.store.DeleteSelected(row)
            self._table.ResetView(self)
        self.ClearSelection()

    def _onLabelClick(self, evt):
        """ Handle Grid label click"""

        if evt.Row == -1:
            if evt.Col >= 0:
                self.store.Sort(evt.Col)
                sort_column = self.store.GetSortColumn()
                sort_mode = self.store.GetSortMode()
                self._updateGridLabel(sort_column, sort_mode)
                self._table.ResetView(self)

        if evt.Col == -1:
            if evt.Row >= 0:
                self.SelectRow(evt.Row)
                self.SetGridCursor(evt.Row, 0)

    def _updateGridLabel(self, column, mode):
        """ Change grid's column labels """

        directionLabel = ""
        if mode is not None:
            directionLabel = " (asc)" if mode else " (desc)"
        for i in range(len(self.grid_labels)):
            label = (self.grid_labels[i] +
                     (directionLabel if column == i else ""))
            self._table.SetColLabelValue(i, label)

    def _on_select_cell(self, evt):
        row = evt.GetRow()
        self.selection = set((row,))

    def _on_select_range(self, evt):
        select_range = set(range(evt.GetTopRow(), evt.GetBottomRow() + 1))
        if evt.Selecting():
            self.selection |= select_range
        else:
            self.selection -= select_range


class DictionaryEditorGridTable(PyGridTableBase):
    """
    A custom wx.Grid Table using user supplied data
    """
    def __init__(self, store):
        """ Init GridTableBase with a Store. """

        # The base class must be initialized *first*
        PyGridTableBase.__init__(self)
        self.store = store
        cols = sorted([[COL_STROKE, "Stroke"],
                       [COL_SPACER, ""],
                       [COL_TRANSLATION, "Translation"],
                       [COL_DICTIONARY, "Dictionary"]])
        self.col_names = [pair[1] for pair in cols]

        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()

    def GetNumberCols(self):
        return len(self.col_names)

    def GetNumberRows(self):
        return self.store.GetNumberOfRows()

    def GetColLabelValue(self, col):
        return self.col_names[col]

    def SetColLabelValue(self, col, name):
        self.col_names[col] = name

    def GetRowLabelValue(self, row):
        return str(row + 1)

    def GetValue(self, row, col):
        return self.store.GetValue(row, col)

    def SetValue(self, row, col, value):
        self.store.SetValue(row, col, value)

    def GetAttr(self, row, col, params):
        if col in (COL_DICTIONARY, COL_SPACER):
            attr = wx.grid.GridCellAttr()
            attr.SetReadOnly(True)
            attr.SetAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
            return attr
        if self.store.is_row_read_only(row):
            attr = wx.grid.GridCellAttr()
            attr.SetReadOnly(True)
            return attr
        return None

    def ResetView(self, grid):

        grid.BeginBatch()

        for current, new, delmsg, addmsg in [
            (self._rows, self.GetNumberRows(),
                wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
                wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
            (self._cols, self.GetNumberCols(),
                wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
                wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED)
        ]:
            if new < current:
                msg = wx.grid.GridTableMessage(self,
                                               delmsg,
                                               new,
                                               current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = wx.grid.GridTableMessage(self,
                                               addmsg,
                                               new-current)
                grid.ProcessTableMessage(msg)
                self.UpdateValues(grid)

        grid.EndBatch()

        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()

        grid.AdjustScrollbars()
        grid.ForceRefresh()

    def UpdateValues(self, grid):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = (wx.grid
               .GridTableMessage(self,
                                 wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES))
        grid.ProcessTableMessage(msg)


def Show(parent, engine, config):
    if 'dialog_instance' not in Show.__dict__:
        Show.dialog_instance = None

    def clear_instance():
        Show.dialog_instance = None

    if Show.dialog_instance is None:
        Show.dialog_instance = DictionaryEditor(parent,
                                                engine,
                                                config,
                                                clear_instance)
    Show.dialog_instance.Show()
    Show.dialog_instance.Raise()
    util.SetTopApp(Show.dialog_instance)
