# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import wx
from wx.lib.utils import AdjustRectToScreen
import sys

DIALOG_TITLE = 'Keyboard Configuration'
ARPEGGIATE_LABEL = "Arpeggiate"
ARPEGGIATE_INSTRUCTIONS = """Arpeggiate allows using non-NKRO keyboards.
Each key can be pressed separately and the space bar
is pressed to send the stroke."""
GRAB_KEYBOARD_LABEL = "Grab keyboard"
GRAB_KEYBOARD_INSTRUCTIONS = """On Linux, grab keyboard lets us capture keystrokes
without outputting them first (and deleting them afterwards).  This can
fix bugs on some applications which do not support delete.  However, for
many text widgets this will cause the text cursor to become invisible while
using Plover."""
UI_BORDER = 4

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

        # ToDo: arguably this is an abstraction boundary violation, and
        # the set of available options should be handled by the oslayer
        # itself, but for now, bake it into the keyboard.
        if sys.platform.startswith('linux'):
            sizer.Add(wx.StaticText(self, label=GRAB_KEYBOARD_INSTRUCTIONS),
                    border=UI_BORDER, flag=wx.ALL)
            self.grab_keyboard_option = wx.CheckBox(self, label=GRAB_KEYBOARD_LABEL)
            self.grab_keyboard_option.SetValue(options.grab_keyboard)
            sizer.Add(self.grab_keyboard_option, border=UI_BORDER,
                      flag=wx.LEFT | wx.RIGHT | wx.BOTTOM)
        
        ok_button = wx.Button(self, id=wx.ID_OK)
        ok_button.SetDefault()
        cancel_button = wx.Button(self, id=wx.ID_CANCEL)

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
        self.options.grab_keyboard = self.grab_keyboard_option.GetValue()
        self.EndModal(wx.ID_OK)
    
    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
        
        
        
