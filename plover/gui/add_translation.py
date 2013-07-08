# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import wx


class AddTranslationDialog(wx.Dialog):
    
    BORDER = 3
    STROKES_TEXT = 'Strokes:'
    TRANSLATION_TEXT = 'Translation:'
    
    def __init__(self, 
                 parent,
                 engine,
                 id=wx.ID_ANY,
                 title='', 
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize, 
                 style=wx.DEFAULT_DIALOG_STYLE,
                 name=wx.DialogNameStr):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)

        self.engine = engine

        # components
        self.strokes_text = wx.TextCtrl(self)
        self.translation_text = wx.TextCtrl(self)
        button = wx.Button(self, label='Add to dictionary')
        self.stroke_mapping_text = wx.StaticText(self)
        self.translation_mapping_text = wx.StaticText(self)
        
        # layout
        global_sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, label=self.STROKES_TEXT)
        sizer.Add(label, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, 
                  border=self.BORDER)
        sizer.Add(self.strokes_text, 
                  flag=wx.TOP | wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 
                  border=self.BORDER)
        label = wx.StaticText(self, label=self.TRANSLATION_TEXT)
        sizer.Add(label, 
                  flag=wx.TOP | wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 
                  border=self.BORDER)
        sizer.Add(self.translation_text          , 
                  flag=wx.TOP | wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 
                  border=self.BORDER)
        sizer.Add(button, 
                  flag=wx.TOP | wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 
                  border=self.BORDER)
        global_sizer.Add(sizer)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.stroke_mapping_text, 
                  flag= wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                  border=self.BORDER)
        global_sizer.Add(sizer)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.translation_mapping_text, 
                  flag= wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                  border=self.BORDER)
        global_sizer.Add(sizer)
        
        self.SetAutoLayout(True)
        self.SetSizer(global_sizer)
        global_sizer.Fit(self)
        global_sizer.SetSizeHints(self)
        self.Layout()
        
        # events
        button.Bind(wx.EVT_BUTTON, self.on_add_translation)
        
        self.strokes_text.SetFocus()
        
    def on_add_translation(self, event=None):
        d = self.engine.get_dictionary()
        strokes = tuple(s for s in self.strokes_text.GetValue().split())
        translation = self.translation_text.GetValue()
        d[strokes] = translation
        d.save()
        self.EndModal(wx.ID_OK)

class TestApp(wx.App):
    """A test application that brings up a SerialConfigDialog.

    Serial port information is printed both before and after the
    dialog is dismissed.
    """
    def OnInit(self):
        dialog = AddTranslationDialog(None)
        self.SetTopWindow(dialog)
        dialog.Show()
        return True


if __name__ == "__main__":
    app = TestApp(0)
    app.MainLoop()
    