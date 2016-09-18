# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import wx
from wx.lib.utils import AdjustRectToScreen

from plover.steno import normalize_steno
import plover.gui.util as util
from plover.translation import escape_translation, unescape_translation

TITLE = 'Plover: Lookup'
CANCEL_BUTTON = 'Close'

class LookupDialog(wx.Dialog):

    BORDER = 3

    other_instances = []

    def __init__(self, parent, engine, config):
        pos = (config.get_lookup_frame_x(),
               config.get_lookup_frame_y())
        wx.Dialog.__init__(self, parent, title=TITLE, pos=pos,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.config = config

        # components
        self.translation_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.listbox = wx.ListBox(self, size=wx.Size(210, 200),
                                  style=wx.LB_HSCROLL)
        cancel = wx.Button(self, wx.ID_CANCEL, CANCEL_BUTTON)
        cancel.Bind(wx.EVT_BUTTON, self.on_close)
        # layout
        global_sizer = wx.BoxSizer(wx.VERTICAL)

        global_sizer.Add(self.translation_text, 0, wx.ALL | wx.EXPAND,
                         self.BORDER)
        global_sizer.Add(self.listbox, 1, wx.ALL & ~wx.TOP | wx.EXPAND,
                         self.BORDER)
        global_sizer.Add(cancel, 0, wx.ALL & ~wx.TOP | wx.EXPAND, self.BORDER)

        self.SetAutoLayout(True)
        self.SetSizer(global_sizer)
        global_sizer.Fit(self)
        global_sizer.SetSizeHints(self)
        self.Layout()
        self.SetRect(AdjustRectToScreen(self.GetRect()))

        # events
        self.translation_text.Bind(wx.EVT_TEXT, self.on_translation_change)
        self.translation_text.Bind(wx.EVT_SET_FOCUS, self.on_translation_gained_focus)
        self.translation_text.Bind(wx.EVT_KILL_FOCUS, self.on_translation_lost_focus)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Bind(wx.EVT_MOVE, self.on_move)

        self.engine = engine
        
        # TODO: add functions on engine for state
        self.previous_state = self.engine.translator.get_state()
        # TODO: use state constructor?
        self.engine.translator.clear_state()
        self.translation_state = self.engine.translator.get_state()
        self.engine.translator.set_state(self.previous_state)
        
        self.last_window = util.GetForegroundWindow()
        
        # Now that we saved the last window we'll close other instances. This 
        # may restore their original window but we've already saved ours so it's 
        # fine.
        for instance in self.other_instances:
            instance.Close()
        del self.other_instances[:]
        self.other_instances.append(self)

    def on_close(self, event=None):
        self.engine.translator.set_state(self.previous_state)
        self.other_instances.remove(self)
        self.Destroy()
        self.Update()  # confirm dialog is removed before setting fg window
        try:
            util.SetForegroundWindow(self.last_window)
        except:
            pass

    def on_translation_change(self, event):
        translation = event.GetString()
        self.listbox.Clear()
        if translation:
            suggestions = self.engine.get_suggestions(
                unescape_translation(translation)
            )
            if suggestions:
                for suggestion, strokes in suggestions:
                    self.listbox.Append(escape_translation(suggestion))
                    entries = ('/'.join(x) for x in strokes)
                    for entry in entries:
                        self.listbox.Append('    %s' % (entry))
                self.listbox.EnsureVisible(0)
            else:
                self.listbox.Append('No entries')
        self.GetSizer().Layout()

    def on_translation_gained_focus(self, event):
        self.engine.translator.set_state(self.translation_state)
        
    def on_translation_lost_focus(self, event):
        self.engine.translator.set_state(self.previous_state)

    def on_button_gained_focus(self, event):
        self.strokes_text.SetFocus()

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_lookup_frame_x(pos[0])
        self.config.set_lookup_frame_y(pos[1])
        event.Skip()

    def _normalized_strokes(self):
        strokes = self.strokes_text.GetValue().upper().replace('/', ' ').split()
        strokes = normalize_steno('/'.join(strokes))
        return strokes


def Show(parent, engine, config):
    dialog_instance = LookupDialog(parent, engine, config)
    dialog_instance.Show()
    dialog_instance.Raise()
    dialog_instance.translation_text.SetFocus()
    util.SetTopApp(dialog_instance)
