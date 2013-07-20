# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""A gui display of recent strokes."""

import wx
from wx.lib.utils import AdjustRectToScreen
from collections import deque
from plover.steno import STENO_KEY_ORDER, STENO_KEY_NUMBERS

TITLE = 'Plover: Stroke Display'
ON_TOP_TEXT = "Always on top"
UI_BORDER = 4
ALL_KEYS = ''.join(x[0].strip('-') for x in 
                   sorted(STENO_KEY_ORDER.items(), key=lambda x: x[1]))
REVERSE_NUMBERS = {v: k for k, v in STENO_KEY_NUMBERS.items()}
STROKE_LINES = 30


class StrokeDisplayDialog(wx.Dialog):
    
    other_instances = []
    strokes = deque(maxlen=STROKE_LINES)

    def __init__(self, parent, config):
        self.config = config        
        on_top = config.get_stroke_display_on_top()
        style = wx.DEFAULT_DIALOG_STYLE
        if on_top:
            style |= wx.STAY_ON_TOP
        pos = (config.get_stroke_display_x(), config.get_stroke_display_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)
                
        self.SetBackgroundColour(wx.WHITE)
                
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.on_top = wx.CheckBox(self, label=ON_TOP_TEXT)
        self.on_top.SetValue(on_top)
        self.on_top.Bind(wx.EVT_CHECKBOX, self.handle_on_top)
        sizer.Add(self.on_top, flag=wx.ALL, border=UI_BORDER)
        
        self.header = wx.StaticText(self, label=ALL_KEYS)
        font = self.header.GetFont()
        font.SetFaceName("Courier New")
        self.header.SetFont(font)
        sizer.Add(self.header, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, 
                  border=UI_BORDER)
        sizer.Add(wx.StaticLine(self), flag=wx.EXPAND)
        
        self.labels = []
        for i in range(STROKE_LINES):
            label = wx.StaticText(self, label=' ')
            self.labels.append(label)
            font = label.GetFont()
            font.SetFaceName("Courier New")
            label.SetFont(font)
            sizer.Add(label, border=UI_BORDER, 
                      flag=wx.LEFT | wx.RIGHT | wx.BOTTOM)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Layout()
        sizer.Fit(self)
        
        for stroke in self.strokes:
            self.show_stroke(stroke)
            
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
        for i in range(len(self.labels) - 1):
            self.labels[i].SetLabel(self.labels[i + 1].GetLabel())
        self.labels[-1].SetLabel(text)
        
    def show_stroke(self, stroke):
        text = [' '] * len(ALL_KEYS)
        keys = stroke.steno_keys[:]
        if any(key in REVERSE_NUMBERS for key in keys):
            keys.append('#')
        for key in keys:
            if key in REVERSE_NUMBERS:
                key = REVERSE_NUMBERS[key]
            index = STENO_KEY_ORDER[key]
            text[index] = ALL_KEYS[index]
        text = ''.join(text)
        self.show_text(text)

    def handle_on_top(self, event):
        self.config.set_stroke_display_on_top(event.IsChecked())
        self.display(self.GetParent(), self.config)

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

    def save(self, fp):
        pass

class TestApp(wx.App):
    def OnInit(self):
        StrokeDisplayDialog.display(None, fake_config())
        #self.SetTopWindow(dlg)
        import random
        from plover.steno import Stroke
        keys = STENO_KEY_ORDER.keys()
        for i in range(100):
            num = random.randint(1, len(keys))
            StrokeDisplayDialog.stroke_handler(Stroke(random.sample(keys, num)))
        return True

if __name__ == "__main__":
    app = TestApp(0)
    app.MainLoop()
