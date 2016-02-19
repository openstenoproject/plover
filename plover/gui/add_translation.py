# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import wx
from wx.lib.utils import AdjustRectToScreen
from plover.steno import normalize_steno
import plover.gui.util as util

TITLE = 'Plover: Add Translation'

class AddTranslationDialog(wx.Dialog):
    
    BORDER = 3
    STROKES_TEXT = 'Strokes:'
    TRANSLATION_TEXT = 'Translation:'
    
    other_instances = []
    
    def __init__(self, parent, engine, config):
        pos = (config.get_translation_frame_x(),
               config.get_translation_frame_y())
        wx.Dialog.__init__(self, parent, title=TITLE, pos=pos)

        self.config = config

        # components
        self.strokes_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.translation_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        button = wx.Button(self, id=wx.ID_OK, label='Add to dictionary')
        cancel = wx.Button(self, id=wx.ID_CANCEL, label='Cancel')
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
        self.SetRect(AdjustRectToScreen(self.GetRect()))
        
        # events
        button.Bind(wx.EVT_BUTTON, self.on_add_translation)
        # The reason for the focus event here is to skip focus on tab traversal
        # of the buttons. But it seems that on windows this prevents the button
        # from being pressed. Leave this commented out until that problem is
        # resolved.
        #button.Bind(wx.EVT_SET_FOCUS, self.on_button_gained_focus)
        cancel.Bind(wx.EVT_BUTTON, self.on_close)
        #cancel.Bind(wx.EVT_SET_FOCUS, self.on_button_gained_focus)
        self.strokes_text.Bind(wx.EVT_TEXT, self.on_strokes_change)
        self.translation_text.Bind(wx.EVT_TEXT, self.on_translation_change)
        self.strokes_text.Bind(wx.EVT_SET_FOCUS, self.on_strokes_gained_focus)
        self.strokes_text.Bind(wx.EVT_KILL_FOCUS, self.on_strokes_lost_focus)
        self.strokes_text.Bind(wx.EVT_TEXT_ENTER, self.on_add_translation)
        self.translation_text.Bind(wx.EVT_SET_FOCUS, self.on_translation_gained_focus)
        self.translation_text.Bind(wx.EVT_KILL_FOCUS, self.on_translation_lost_focus)
        self.translation_text.Bind(wx.EVT_TEXT_ENTER, self.on_add_translation)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_MOVE, self.on_move)
        
        self.engine = engine
        
        # TODO: add functions on engine for state
        self.previous_state = self.engine.translator.get_state()
        # TODO: use state constructor?
        self.engine.translator.clear_state()
        self.strokes_state = self.engine.translator.get_state()
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
    
    def on_add_translation(self, event=None):
        d = self.engine.get_dictionary()
        strokes = self._normalized_strokes()
        translation = self.translation_text.GetValue().strip()
        if strokes and translation:
            d.set(strokes, translation)
            d.save()
        self.Close()

    def on_close(self, event=None):
        self.engine.translator.set_state(self.previous_state)
        self.other_instances.remove(self)
        self.Destroy()
        self.Update()
        try:
            util.SetForegroundWindow(self.last_window)
        except:
            pass

    def on_strokes_change(self, event):
        key = self._normalized_strokes()
        if key:
            d = self.engine.get_dictionary()
            translation = d.raw_lookup(key)
            strokes = '/'.join(key)
            if translation:
                label = '%s maps to %s' % (strokes, translation)
            else:
                label = '%s is not in the dictionary' % strokes
            label = util.shorten_unicode(label)
        else:
            label = ''
        self.stroke_mapping_text.SetLabel(label)
        self.GetSizer().Layout()

    def on_translation_change(self, event):
        # TODO: normalize dict entries to make reverse lookup more reliable
        # with whitespace.
        translation = event.GetString().strip()
        if translation:
            d = self.engine.get_dictionary()
            strokes_list = d.reverse_lookup(translation)
            if strokes_list:
                strokes = ', '.join('/'.join(x) for x in strokes_list)
                label = '%s is mapped from %s' % (translation, strokes)
            else:
                label = '%s is not in the dictionary' % translation
            label = util.shorten_unicode(label)
        else:
            label = ''
        self.translation_mapping_text.SetLabel(label)
        self.GetSizer().Layout()

    def on_strokes_gained_focus(self, event):
        self.engine.get_dictionary().add_filter(self.stroke_dict_filter)
        self.engine.translator.set_state(self.strokes_state)
        event.Skip()
        
    def on_strokes_lost_focus(self, event):
        self.engine.get_dictionary().remove_filter(self.stroke_dict_filter)
        self.engine.translator.set_state(self.previous_state)
        event.Skip()

    def on_translation_gained_focus(self, event):
        self.engine.translator.set_state(self.translation_state)
        event.Skip()
        
    def on_translation_lost_focus(self, event):
        self.engine.translator.set_state(self.previous_state)
        event.Skip()

    def on_button_gained_focus(self, event):
        self.strokes_text.SetFocus()
        event.Skip()
        
    def stroke_dict_filter(self, key, value):
        # Only allow translations with special entries. Do this by looking for 
        # braces but take into account escaped braces and slashes.
        escaped = value.replace('\\\\', '').replace('\\{', '')
        special = '{#'  in escaped or '{PLOVER:' in escaped
        return not special

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_translation_frame_x(pos[0]) 
        self.config.set_translation_frame_y(pos[1])
        event.Skip()

    def _normalized_strokes(self):
        strokes = self.strokes_text.GetValue().upper().replace('/', ' ').split()
        strokes = normalize_steno('/'.join(strokes))
        return strokes

def Show(parent, engine, config):
    dialog_instance = AddTranslationDialog(parent, engine, config)
    dialog_instance.Show()
    dialog_instance.Raise()
    dialog_instance.strokes_text.SetFocus()
    util.SetTopApp(dialog_instance)
