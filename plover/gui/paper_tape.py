# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""A gui display of recent strokes."""

import wx
import time
from wx.lib.utils import AdjustRectToScreen
from collections import deque
from plover import system
from plover.gui.util import find_fixed_width_font
from plover import log

TITLE = 'Plover: Stroke Display'
ON_TOP_TEXT = "Always on top"
UI_BORDER = 4
MAX_STROKE_LINES = 30
MAX_STROKES_IN_LOG = 2000000
STYLE_TEXT = 'Style:'
STYLE_PAPER = 'Paper'
STYLE_RAW = 'Raw'
STYLES = [STYLE_PAPER, STYLE_RAW]
CLEAR_BUTTON_NAME = 'Clear'
SAVE_BUTTON_NAME = 'Save'
CLEAR_PROMPT = 'Would you like to clear the notes?'
CLEAR_PROMPT_TITLE = 'Clear?'
SAVE_NOTES_DIALOG_TITLE = 'Save notes'
SAVE_NOTES_FILE_DIALOG_TEXT_FILE_FILTER = 'Text files (*.txt)|*'

class StrokeDisplayDialog(wx.Dialog):
    
    other_instances = []
    strokes = deque(maxlen=MAX_STROKES_IN_LOG)

    def __init__(self, parent, config):
        self.config = config        
        on_top = config.get_stroke_display_on_top()
        style = wx.DEFAULT_DIALOG_STYLE
        if on_top:
            style |= wx.STAY_ON_TOP
        pos = (config.get_stroke_display_x(), config.get_stroke_display_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.on_top = wx.CheckBox(self, label=ON_TOP_TEXT)
        self.on_top.SetValue(config.get_stroke_display_on_top())
        self.on_top.Bind(wx.EVT_CHECKBOX, self.handle_on_top)
        sizer.Add(self.on_top, flag=wx.ALL, border=UI_BORDER)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, label=STYLE_TEXT),
                border=UI_BORDER,
                flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT)
        self.choice = wx.Choice(self, choices=STYLES)
        self.choice.SetStringSelection(self.config.get_stroke_display_style())
        self.choice.Bind(wx.EVT_CHOICE, self.on_style)
        box.Add(self.choice, proportion=1)
        sizer.Add(box, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 
                  border=UI_BORDER)

        fixed_font = find_fixed_width_font()

        self.all_keys = ''.join(k.strip('-') for k in system.KEYS)
        self.reverse_numbers = {v: k for k, v in system.NUMBERS.items()}

        # Calculate required width and height.
        dc = wx.ScreenDC()
        dc.SetFont(fixed_font)
        # Extra spaces for Max OS X...
        text_width, text_height = dc.GetTextExtent(self.all_keys + 2 * ' ')
        scroll_width = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
        scroll_height = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)

        self.header = wx.StaticText(self)
        self.header.SetFont(fixed_font)
        sizer.Add(self.header, flag=wx.ALL|wx.EXPAND|wx.ALIGN_LEFT, border=UI_BORDER)

        sizer.Add(wx.StaticLine(self), flag=wx.EXPAND)

        self.listbox = wx.TextCtrl(self,
                                   style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP|wx.BORDER_NONE|wx.HSCROLL|wx.VSCROLL,
                                   # Will show MAX_STROKE_LINES lines.
                                   size=wx.Size(scroll_width + text_width,
                                                scroll_height + text_height * MAX_STROKE_LINES))
        self.listbox.SetFont(fixed_font)

        sizer.Add(self.listbox,
                  flag=wx.ALL|wx.EXPAND|wx.ALIGN_LEFT,
                  border=UI_BORDER)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(buttons, flag=wx.EXPAND|wx.ALL)

        clear_button = wx.Button(self, id=wx.ID_CLEAR, label=CLEAR_BUTTON_NAME)
        buttons.AddSpacer(5)
        buttons.Add(clear_button, flag=wx.EXPAND|wx.ALIGN_LEFT)
        self.Bind(wx.EVT_BUTTON, self._clear, clear_button)
        buttons.AddStretchSpacer()
        save_button = wx.Button(self, id=wx.ID_SAVE, label=SAVE_BUTTON_NAME)
        buttons.Add(save_button, flag=wx.EXPAND|wx.ALIGN_RIGHT)
        buttons.AddSpacer(5)
        self.Bind(wx.EVT_BUTTON, self._save, save_button)

        sizer.AddSpacer(5)

        self.on_style()

        self.SetSizerAndFit(sizer)

        self.Show()
        self.close_all()
        self.other_instances.append(self)
        
        self.SetRect(AdjustRectToScreen(self.GetRect()))
        
        self.Bind(wx.EVT_MOVE, self.on_move)
        
    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_stroke_display_x(pos[0]) 
        self.config.set_stroke_display_y(pos[1])
        event.Skip()
        
    def on_close(self, event):
        self.other_instances.remove(self)
        event.Skip()
        
    def show_text(self, text):
        if self.listbox.IsEmpty():
            self.listbox.AppendText(text)
        else:
            self.listbox.AppendText('\n' + text)
        self.line_lengths.append(len(text) + 1)

    def show_stroke(self, stroke):
        self.show_text(self.formatter(stroke))

    def handle_on_top(self, event):
        on_top = event.IsChecked()
        self.config.set_stroke_display_on_top(on_top)
        style = wx.DEFAULT_DIALOG_STYLE
        if on_top:
            style |= wx.STAY_ON_TOP
        self.SetWindowStyleFlag(style)

    def on_style(self, event=None):
        format = self.choice.GetStringSelection()
        self.formatter = getattr(self, format.lower() + '_format')
        self.listbox.Clear()
        self.line_lengths = []
        if STYLE_PAPER == format:
            self.header.SetLabel(self.all_keys)
        else:
            self.header.SetLabel('')
        for stroke in self.strokes:
            self.show_stroke(stroke)
        self.config.set_stroke_display_style(format)

    def paper_format(self, stroke):
        text = [' '] * len(self.all_keys)
        keys = stroke.steno_keys[:]
        if any(key in self.reverse_numbers for key in keys):
            keys.append('#')
        for key in keys:
            if key in self.reverse_numbers:
                key = self.reverse_numbers[key]
            index = system.KEY_ORDER[key]
            text[index] = self.all_keys[index]
        text = ''.join(text)
        return text        

    def _clear(self, event=None):
        message_dialog = wx.MessageDialog(self, CLEAR_PROMPT, CLEAR_PROMPT_TITLE)
        message_dialog.SetOKLabel("Clear")
        if message_dialog.ShowModal() == wx.ID_OK:
            self.listbox.Clear()
            self.strokes.clear()

    def _save(self, event=None):
        file_name_suggestion = 'steno-notes-%s.txt' % time.strftime('%Y-%m-%d-%H-%M')
        file_dialog = wx.FileDialog(self, SAVE_NOTES_DIALOG_TITLE, "", file_name_suggestion,
                                    SAVE_NOTES_FILE_DIALOG_TEXT_FILE_FILTER, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if file_dialog.ShowModal() == wx.ID_OK:
            try:
                with open(file_dialog.GetPath(), 'w') as fd:
                    fd.write(self.listbox.GetValue()+'\n')
            except IOError:
                log.error("Cannot save notes in file '%s'." % file_dialog.GetPath(), exc_info=True)

    def raw_format(self, stroke):
        return stroke.rtfcre

    @staticmethod
    def close_all():
        for instance in StrokeDisplayDialog.other_instances:
            instance.Close()
        del StrokeDisplayDialog.other_instances[:]

    @staticmethod
    def stroke_handler(stroke):
        StrokeDisplayDialog.strokes.append(stroke)
        for instance in StrokeDisplayDialog.other_instances:
            wx.CallAfter(instance.show_stroke, stroke)

    @staticmethod
    def display(parent, config):
        # StrokeDisplayDialog shows itself.
        StrokeDisplayDialog(parent, config)

class fake_config(object):
    def __init__(self):
        self.on_top = True
        self.target_file = 'testfile'
        self.x = -1
        self.y = -1
        self.style = 'Raw'
        
    def get_stroke_display_on_top(self):
        return self.on_top
    
    def set_stroke_display_on_top(self, b):
        self.on_top = b
        
    def get_stroke_display_x(self):
        return self.x

    def set_stroke_display_x(self, x):
        self.x = x

    def get_stroke_display_y(self):
        return self.y

    def set_stroke_display_y(self, y):
        self.y = y

    def set_stroke_display_style(self, style):
        self.style = style
        
    def get_stroke_display_style(self):
        return self.style

    def save(self, fp):
        pass

class TestApp(wx.App):
    def OnInit(self):
        StrokeDisplayDialog.display(None, fake_config())
        #self.SetTopWindow(dlg)
        import random
        from plover.steno import Stroke
        keys = system.KEY_ORDER.keys()
        for i in range(100):
            num = random.randint(1, len(keys))
            StrokeDisplayDialog.stroke_handler(Stroke(random.sample(keys, num)))
        return True

if __name__ == "__main__":
    app = TestApp(0)
    app.MainLoop()
