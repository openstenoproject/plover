# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""A gui display of recent strokes."""

import wx
from plover.steno import STENO_KEY_ORDER, STENO_KEY_NUMBERS

TITLE = 'Plover: Stroke Display'
ON_TOP_TEXT = "Always on top"
UI_BORDER = 4
ALL_KEYS = ''.join(x[0].strip('-') for x in 
                   sorted(STENO_KEY_ORDER.items(), key=lambda x: x[1]))
REVERSE_NUMBERS = {v: k for k, v in STENO_KEY_NUMBERS.items()}


class StrokeDisplayDialog(wx.Dialog):
    
    other_instances = []

    def __init__(self, parent, on_top, initial_text=[]):
        style = wx.DEFAULT_DIALOG_STYLE
        if on_top:
            style |= wx.STAY_ON_TOP
        wx.Dialog.__init__(self, parent, title=TITLE, style=style)
        
        self.close_all()
        self.other_instances.append(self)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.on_top = wx.CheckBox(self, label=ON_TOP_TEXT)
        self.on_top.SetValue(on_top)
        self.on_top.Bind(wx.EVT_CHECKBOX, self.handle_on_top)
        sizer.Add(self.on_top, flag=wx.ALL, border=UI_BORDER)
        
        label = wx.StaticText(self, label=ALL_KEYS)
        font = label.GetFont()
        font.SetFaceName("Courier New")
        label.SetFont(font)
        sizer.Add(label, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, 
                  border=UI_BORDER)
        sizer.Add(wx.StaticLine(self), flag=wx.EXPAND)
        self.labels = [wx.StaticText(self, label=' ') for i in range(30)]
        for label in self.labels:
            font = label.GetFont()
            font.SetFaceName("Courier New")
            label.SetFont(font)
            sizer.Add(label, border=UI_BORDER, 
                      flag=wx.LEFT | wx.RIGHT | wx.BOTTOM)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Layout()
        sizer.Fit(self)
        
        for text in initial_text:
            self.show_text(text)
        
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
        initial_text = [l.GetLabel() for l in self.labels]
        StrokeDisplayDialog(
            self.GetParent(), event.IsChecked(), initial_text).Show()

    @staticmethod
    def close_all():
        for instance in StrokeDisplayDialog.other_instances:
            instance.Close()
            
    @staticmethod
    def stroke_handler(stroke):
        for instance in StrokeDisplayDialog.other_instances:
            instance.show_stroke(stroke)
        

class TestApp(wx.App):
    def OnInit(self):
        dlg = StrokeDisplayDialog(None, True)
        self.SetTopWindow(dlg)
        dlg.Show()
        import random
        from plover.steno import Stroke
        keys = STENO_KEY_ORDER.keys()
        for i in range(100):
            num = random.randint(1, len(keys))
            dlg.show_stroke(Stroke(random.sample(keys, num)))
        return True

if __name__ == "__main__":
    app = TestApp(0)
    app.MainLoop()
