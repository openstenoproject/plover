# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import wx
import sys

if sys.platform.startswith('win32'):
    import win32gui
    GetForegroundWindow = win32gui.GetForegroundWindow
    SetForegroundWindow = win32gui.SetForegroundWindow

    def SetTopApp():
        # Nothing else is necessary for windows.
        pass

elif sys.platform.startswith('darwin'):
    from Foundation import NSAppleScript
    from AppKit import NSApp, NSApplication

    def GetForegroundWindow():
        return NSAppleScript.alloc().initWithSource_("""
tell application "System Events"
    return unix id of first process whose frontmost = true
end tell""").executeAndReturnError_(None)[0].int32Value()

    def SetForegroundWindow(pid):
        NSAppleScript.alloc().initWithSource_("""
tell application "System Events"
    set the frontmost of first process whose unix id is %d to true
end tell""" % pid).executeAndReturnError_(None)

    def SetTopApp():
        NSApplication.sharedApplication()
        NSApp().activateIgnoringOtherApps_(True)

elif sys.platform.startswith('linux'):
    from subprocess import call, check_output, CalledProcessError

    def GetForegroundWindow():
        try:
            output = check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'])
            return output.split()[-1]
        except CalledProcessError:
            return None

    def SetForegroundWindow(w):
        try:
            call(['wmctrl', '-i', '-a', w])
        except CalledProcessError:
            pass

    def SetTopApp():
        try:
            call(['wmctrl', '-a', TITLE])
        except CalledProcessError:
            pass

else:
    # These functions are optional so provide a non-functional default 
    # implementation.
    def GetForegroundWindow():
        return None

    def SetForegroundWindow(w):
        pass

    def SetTopApp():
        pass

TITLE = 'Plover: Add Translation'

class AddTranslationDialog(wx.Dialog):
    
    BORDER = 3
    STROKES_TEXT = 'Strokes:'
    TRANSLATION_TEXT = 'Translation:'
    
    def __init__(self, parent, engine):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, TITLE, 
                           wx.DefaultPosition, wx.DefaultSize, 
                           wx.DEFAULT_DIALOG_STYLE, wx.DialogNameStr)

        # components
        self.strokes_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.translation_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        button = wx.Button(self, id=wx.ID_OK, label='Add to dictionary')
        cancel = wx.Button(self, id=wx.ID_CANCEL)
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
        sizer.Add(cancel, 
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
        button.Bind(wx.EVT_SET_FOCUS, self.on_button_gained_focus)
        cancel.Bind(wx.EVT_BUTTON, self.on_close)
        cancel.Bind(wx.EVT_SET_FOCUS, self.on_button_gained_focus)
        self.strokes_text.Bind(wx.EVT_TEXT, self.on_strokes_change)
        self.translation_text.Bind(wx.EVT_TEXT, self.on_translation_change)
        self.strokes_text.Bind(wx.EVT_SET_FOCUS, self.on_strokes_gained_focus)
        self.strokes_text.Bind(wx.EVT_KILL_FOCUS, self.on_strokes_lost_focus)
        self.strokes_text.Bind(wx.EVT_TEXT_ENTER, self.on_add_translation)
        self.translation_text.Bind(wx.EVT_SET_FOCUS, self.on_translation_gained_focus)
        self.translation_text.Bind(wx.EVT_KILL_FOCUS, self.on_translation_lost_focus)
        self.translation_text.Bind(wx.EVT_TEXT_ENTER, self.on_add_translation)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        self.engine = engine
        
        # TODO: add functions on engine for state
        self.previous_state = self.engine.translator.get_state()
        # TODO: use state constructor?
        self.engine.translator.clear_state()
        self.strokes_state = self.engine.translator.get_state()
        self.engine.translator.clear_state()
        self.translation_state = self.engine.translator.get_state()
        self.engine.translator.set_state(self.previous_state)
        
        self.last_window = GetForegroundWindow()
    
    def on_add_translation(self, event=None):
        d = self.engine.get_dictionary()
        strokes = self.strokes_text.GetValue().upper().replace('/', ' ').split()
        strokes = tuple(strokes)
        translation = self.translation_text.GetValue().strip()
        if strokes and translation:
            d[strokes] = translation
            d.save()
        self.Close()

    def on_close(self, event=None):
        self.engine.translator.set_state(self.previous_state)
        try:
            SetForegroundWindow(self.last_window)
        except:
            pass
        self.Destroy()

    def on_strokes_change(self, event):
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
        self.engine.get_dictionary().add_filter(self.stroke_dict_filter)
        self.engine.translator.set_state(self.strokes_state)
        
    def on_strokes_lost_focus(self, event):
        self.engine.get_dictionary().remove_filter(self.stroke_dict_filter)
        self.engine.translator.set_state(self.previous_state)

    def on_translation_gained_focus(self, event):
        self.engine.translator.set_state(self.translation_state)
        
    def on_translation_lost_focus(self, event):
        self.engine.translator.set_state(self.previous_state)

    def on_button_gained_focus(self, event):
        self.strokes_text.SetFocus()
        
    def stroke_dict_filter(self, key, value):
        # Only allow translations with special entries. Do this by looking for 
        # braces but take into account escaped braces and slashes.
        escaped = value.replace('\\\\', '').replace('\\{', '')
        special = '{#'  in escaped or '{PLOVER:' in escaped
        return not special

def Show(parent, engine):
    dialog_instance = AddTranslationDialog(parent, engine)
    dialog_instance.Show()
    dialog_instance.Raise()
    dialog_instance.strokes_text.SetFocus()
    SetTopApp()
