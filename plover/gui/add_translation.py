# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import wx
import sys
if sys.platform.startswith('win32'):
    import win32gui

class AddTranslationDialog(wx.Dialog):
    
    BORDER = 3
    STROKES_TEXT = 'Strokes:'
    TRANSLATION_TEXT = 'Translation:'
    
    def __init__(self, 
                 parent,
                 id=wx.ID_ANY,
                 title='', 
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize, 
                 style=wx.DEFAULT_DIALOG_STYLE,
                 name=wx.DialogNameStr):
        print '__init__'
                 
        wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)

        # components
        self.strokes_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.translation_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
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
        self.strokes_text.Bind(wx.EVT_TEXT, self.on_strokes_change)
        self.translation_text.Bind(wx.EVT_TEXT, self.on_translation_change)
        self.strokes_text.Bind(wx.EVT_SET_FOCUS, self.on_strokes_gained_focus)
        self.strokes_text.Bind(wx.EVT_KILL_FOCUS, self.on_strokes_lost_focus)
        self.strokes_text.Bind(wx.EVT_TEXT_ENTER, self.on_add_translation)
        self.translation_text.Bind(wx.EVT_SET_FOCUS, self.on_translation_gained_focus)
        self.translation_text.Bind(wx.EVT_KILL_FOCUS, self.on_translation_lost_focus)
        self.translation_text.Bind(wx.EVT_TEXT_ENTER, self.on_add_translation)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)

    def show(self, engine):
        print 'show'
        self.engine = engine
        
        if self.IsShown():
            self.on_close()
        
        # TODO: add functions on engine for state
        self.previous_state = self.engine.translator.get_state()
        # TODO: use state constructor?
        self.engine.translator.clear_state()
        self.strokes_state = self.engine.translator.get_state()
        self.engine.translator.clear_state()
        self.translation_state = self.engine.translator.get_state()
        self.engine.translator.set_state(self.previous_state)
        
        self.closing = False
        self.Show()
        
        if sys.platform.startswith('win32'):
            self.last_window = win32gui.GetForegroundWindow()

    def on_activate(self, event):
        print 'on_activate'
        if event.GetActive():
            print 'dialog activated'
            self.strokes_text.SetFocus()
        else:
            print 'dialog deactivated'
            if not self.closing:
                self.on_close()
    
    def on_add_translation(self, event=None):
        print 'on_add_translation'
        d = self.engine.get_dictionary()
        strokes = self.strokes_text.GetValue().upper().replace('/', ' ').split()
        strokes = tuple(strokes)
        translation = self.translation_text.GetValue().strip()
        if strokes and translation:
            d[strokes] = translation
            d.save()
            print 'add %s: %s' % (strokes, translation)

        self.Close()

    def on_close(self, event=None):
        print 'on_close'
        self.closing = True
        self.engine.translator.set_state(self.previous_state)
        self.Hide()
        if sys.platform.startswith('win32'):
            win32gui.SetForegroundWindow(self.last_window)

    def on_strokes_change(self, event):
        print 'on_stroked_change'
        stroke = event.GetString().upper()
        self.strokes_text.ChangeValue(stroke)
        self.strokes_text.SetInsertionPointEnd()
        strokes = stroke.replace('/', ' ').split()
        stroke = '/'.join(strokes)
        if stroke:
            key = tuple(strokes)
            d = self.engine.get_dictionary()
            translation = d.raw_get(key, None)
            if translation:
                label = '%s maps to %s' % (stroke, translation)
            else:
                label = '%s is not in the dictionary' % stroke
        else:
            label = ''
        self.stroke_mapping_text.SetLabel(label)
        self.GetSizer().Layout()

    def on_translation_change(self, event):
        print 'on_translation_change'
        # TODO: normalize dict entries to make reverse lookup more reliable with 
        # whitespace.
        translation = event.GetString().strip()
        if translation:
            d = self.engine.get_dictionary()
            strokes_list = d.reverse[translation]
            if strokes_list:
                strokes = ', '.join('/'.join(x) for x in strokes_list)
                label = '%s is mapped from %s' % (translation, strokes)
            else:
                label = '%s is not in the dictionary' % translation
        else:
            label = ''
        self.translation_mapping_text.SetLabel(label)
        self.GetSizer().Layout()
        
    def on_strokes_gained_focus(self, event):
        print 'on_strokes_gained_focus'
        self.engine.get_dictionary().add_filter(self.stroke_dict_filter)
        self.engine.translator.set_state(self.strokes_state)
        
    def on_strokes_lost_focus(self, event):
        print 'on_strokes_lost_focus'
        self.engine.get_dictionary().remove_filter(self.stroke_dict_filter)

    def on_translation_gained_focus(self, event):
        print 'on_translation_fained_focus'
        self.engine.translator.set_state(self.translation_state)
        
    def on_translation_lost_focus(self, event):
        print 'on_translation_lost_focus'

    def stroke_dict_filter(self, key, value):
        # Only allow translations with special entries. Do this by looking for 
        # braces but take into account escaped braces and slashes.
        escaped = value.replace('\\\\', '').replace('\\{', '')
        special = '{#'  in escaped or '{PLOVER:' in escaped
        return not special

dialog_instance = None

def Show(engine):
    print 'global Show'
    global dialog_instance
    if not dialog_instance:
        dialog_instance = AddTranslationDialog(None)
    dialog_instance.show(engine)

def Destroy():
    print 'global Destroy'
    global dialog_instance
    if dialog_instance:
        dialog_instance.Destroy()
        dialog_instance = None
