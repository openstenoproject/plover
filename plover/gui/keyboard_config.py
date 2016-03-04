# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import wx
from wx.lib.utils import AdjustRectToScreen
import wx.lib.mixins.listctrl as listmix
from plover.oslayer.keyboardcontrol import KeyboardCapture

DIALOG_TITLE = 'Keyboard Configuration'
ARPEGGIATE_LABEL = "Arpeggiate"
ARPEGGIATE_INSTRUCTIONS = """Arpeggiate allows using non-NKRO keyboards.
Each key can be pressed separately and the space bar
is pressed to send the stroke."""
UI_BORDER = 4

class EditKeysDialog(wx.Dialog):

    def __init__(self, parent, action, keys):
        super(EditKeysDialog, self).__init__(parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        instructions = wx.StaticText(self, label='Press on the key you want to add/remove.')
        self.sizer.Add(instructions, border=UI_BORDER, flag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL)
        self.message = wx.StaticText(self)
        self.sizer.Add(self.message, border=UI_BORDER, flag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL)
        buttons = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        self.sizer.Add(buttons, border=UI_BORDER, flag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.action = action
        self.keys = set(keys)
        self.original_keys = self.keys.copy()
        self.capture = KeyboardCapture()
        self.capture.key_down = lambda key: wx.CallAfter(self.on_capture_key, key)

    def ShowModal(self):
        self.update_message()
        self.capture.start()
        try:
            # Prevent dialog from stealing some key events.
            self.capture.suppress_keyboard(('space', 'Escape', 'Return', 'Tab'))
            code = super(EditKeysDialog, self).ShowModal()
        finally:
            self.capture.cancel()
        return code

    def update_message(self):
        message = '\nKeys for %s: ' % self.action
        message += ' '.join(sorted(self.keys)) if self.keys else 'None'
        message += '\n\nChanges: '
        changes = []
        for key in sorted(self.keys.union(self.original_keys)):
            if key not in self.original_keys:
                changes.append('+' + key)
            elif key not in self.keys:
                changes.append('-' + key)
        message += ' '.join(changes) if changes else 'None'
        message += '\n'
        self.message.SetLabelText(message)
        self.sizer.Fit(self)
        self.sizer.Layout()

    def on_capture_key(self, key):
        if key in self.keys:
            self.keys.remove(key)
        else:
            self.keys.add(key)
        self.update_message()

class EditKeymapWidget(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):

    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.edit_item)
        self.InsertColumn(0, 'Steno Keys / Actions')
        self.InsertColumn(1, 'Keys')

    def edit_item(self, event):
        # Disallow editing of first column.
        item = self.GetItem(itemId=event.m_itemIndex, col=0)
        action = item.GetText()
        item = self.GetItem(itemId=event.m_itemIndex, col=1)
        keys = item.GetText().split()
        dlg = EditKeysDialog(self, action, keys)
        if wx.ID_OK != dlg.ShowModal():
            # Cancel.
            return
        text = ' '.join(sorted(dlg.keys))
        self.SetStringItem(event.m_itemIndex, 1, text)

    def set_mappings(self, mappings):
        rows = [(
            action,
            key_list if isinstance(key_list, basestring)
            else ' '.join(key_list)
        ) for action, key_list in mappings.items()]
        self.DeleteAllItems()
        for index, row in enumerate(rows):
            self.InsertStringItem(index, row[0])
            self.SetStringItem(index, 1, row[1])

    def get_mappings(self):
        # Don't screw up the order!
        mappings = OrderedDict()
        for index in range(self.GetItemCount()):
            action = self.GetItem(index, 0).GetText()
            key_list = self.GetItem(index, 1).GetText()
            mappings[action] = key_list.split()
        return mappings

class KeyboardConfigDialog(wx.Dialog):
    """Keyboard configuration dialog."""

    def __init__(self, options, parent, config):
        self.config = config
        self.options = options
        
        pos = (config.get_keyboard_config_frame_x(), 
               config.get_keyboard_config_frame_y())
        wx.Dialog.__init__(self, parent, title=DIALOG_TITLE, pos=pos)

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        instructions = wx.StaticText(self, label=ARPEGGIATE_INSTRUCTIONS)
        sizer.Add(instructions, border=UI_BORDER, flag=wx.ALL)
        self.arpeggiate_option = wx.CheckBox(self, label=ARPEGGIATE_LABEL)
        self.arpeggiate_option.SetValue(options.arpeggiate)
        sizer.Add(self.arpeggiate_option, border=UI_BORDER, 
                  flag=wx.LEFT | wx.RIGHT | wx.BOTTOM)
        
        # editable list for keymap bindings
        self.keymap_widget = EditKeymapWidget(self, style=wx.LC_REPORT, size=(300,200))
        self.keymap_widget.set_mappings(options.keymap.get_mappings())
        sizer.Add(self.keymap_widget, flag=wx.EXPAND)

        ok_button = wx.Button(self, id=wx.ID_OK)
        ok_button.SetDefault()
        cancel_button = wx.Button(self, id=wx.ID_CANCEL, label='Cancel')

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(ok_button, border=UI_BORDER, flag=wx.ALL)
        button_sizer.Add(cancel_button, border=UI_BORDER, flag=wx.ALL)
        sizer.Add(button_sizer, flag=wx.ALL | wx.ALIGN_RIGHT, border=UI_BORDER)
                  
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetRect(AdjustRectToScreen(self.GetRect()))
        
        self.Bind(wx.EVT_MOVE, self.on_move)
        ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_keyboard_config_frame_x(pos[0]) 
        self.config.set_keyboard_config_frame_y(pos[1])
        event.Skip()

    def on_ok(self, event):
        self.options.arpeggiate = self.arpeggiate_option.GetValue()
        mappings = self.keymap_widget.get_mappings()
        self.options.keymap.set_mappings(mappings)
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        
        
        
