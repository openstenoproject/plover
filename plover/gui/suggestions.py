# Copyright (c) 2015 Kevin Nygaard
# See LICENSE.txt for details.

"""A gui display of stroke suggestions """

import wx
import re
from wx.lib.utils import AdjustRectToScreen

PAT = re.compile(r'[-\'"\w]+|[^\w\s]')
TITLE = 'Plover: Suggestions Display'
ON_TOP_TEXT = "Always on top"
UI_BORDER = 4
MAX_STROKE_LINES = 38
LAST_WORD_TEXT = 'Last Word: %s'
DEFAULT_LAST_WORD = '[]'

class SuggestionsDisplayDialog(wx.Dialog):

    other_instances = []

    def __init__(self, parent, config, engine):
        self.config = config
        self.engine = engine
        self.words = ''
        on_top = config.get_suggestions_display_on_top()
        style = wx.DEFAULT_DIALOG_STYLE
        if on_top:
            style |= wx.STAY_ON_TOP
        pos = (config.get_suggestions_display_x(), config.get_suggestions_display_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)

        self.SetBackgroundColour(wx.WHITE)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.on_top = wx.CheckBox(self, label=ON_TOP_TEXT)
        self.on_top.SetValue(config.get_suggestions_display_on_top())
        self.on_top.Bind(wx.EVT_CHECKBOX, self.handle_on_top)
        sizer.Add(self.on_top, flag=wx.ALL, border=UI_BORDER)

        box = wx.BoxSizer(wx.HORIZONTAL)

        self.header = MyStaticText(self, label=LAST_WORD_TEXT % DEFAULT_LAST_WORD)
        font = self.header.GetFont()
        font.SetFaceName("Courier")
        self.header.SetFont(font)
        sizer.Add(self.header, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM,
                  border=UI_BORDER)
        sizer.Add(wx.StaticLine(self), flag=wx.EXPAND)

        self.listbox = wx.ListBox(self, size=wx.Size(210, 500))
        font = self.listbox.GetFont()
        font.SetFaceName("Courier")
        self.listbox.SetFont(font)

        sizer.Add(self.listbox,
                  flag=wx.ALL | wx.FIXED_MINSIZE,
                  border=3)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Layout()
        sizer.Fit(self)

        self.Show()
        self.close_all()
        self.other_instances.append(self)

        self.SetRect(AdjustRectToScreen(self.GetRect()))

        self.Bind(wx.EVT_MOVE, self.on_move)

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_suggestions_display_x(pos[0])
        self.config.set_suggestions_display_y(pos[1])
        event.Skip()

    def on_close(self, event):
        self.other_instances.remove(self)
        event.Skip()

    def lookup_suggestions(self, phrase):
        found = False
        ''' Return stroke suggestions for a given phrase, if it exists

            If we can't find an entry, we start manipulating the phrase to see if we
            can come up with something for the user. This allows for suggestions to
            be given for prefixes/suffixes.

        '''

        mods  = ['%s', '{^%s}', '{^%s^}', '{%s^}', '{&%s}']
        d     = self.engine.get_dictionary()
        for x in [mod % phrase for mod in mods]:
            strokes_list = d.reverse_lookup(x)
            if not strokes_list:
                continue
            else:
                # Return list of suggestions, sorted by amount of keys used
                return True, x, sorted(strokes_list, lambda x, y: cmp(sum(map(len, x)), sum(map(len, y))))

        return False, phrase, []

    def show_stroke(self, old, new):
        for action in old:
            remove = len(action.text)
            self.words = self.words[:-remove]

        for action in new:
            self.words = self.words + action.text

        # Limit phrasing memory to 100 characters, because most phrases probably
        # don't exceed this length
        self.words = self.words[-100:]


        split_words = PAT.findall(self.words)
        interp_phrase = split_words[-1:]
        self.listbox.Clear()
        for phrase in SuggestionsDisplayDialog.tails(split_words):
            phrase = ' '.join(phrase)
            found, interp_phrase, suggestions = self.lookup_suggestions(phrase)
            if found:
                # Limit arbitrarily to 10 suggestions
                for suggestion in suggestions[:10]:
                    self.listbox.Append('/'.join(suggestion))
                break
        else:
            self.listbox.Append('No suggestions')

        self.header.SetLabel(LAST_WORD_TEXT % interp_phrase)

    def handle_on_top(self, event):
        self.config.set_suggestions_display_on_top(event.IsChecked())
        self.display(self.GetParent(), self.config)

    @staticmethod
    def tails(ls):
        ''' Return all tail combinations (a la Haskell)

            tails :: [x] -> [[x]]
            >>> tails('abcd')
            ['abcd', 'bcd', 'cd', d']

        '''

        for i in xrange(0, len(ls)):
            yield ls[i:]

    @staticmethod
    def close_all():
        for instance in SuggestionsDisplayDialog.other_instances:
            instance.Close()
        del SuggestionsDisplayDialog.other_instances[:]

    @staticmethod
    def stroke_handler(old, new):
        for instance in SuggestionsDisplayDialog.other_instances:
            wx.CallAfter(instance.show_stroke, old, new)

    @staticmethod
    def display(parent, config, engine):
        # SuggestionsDisplayDialog shows itself.
        SuggestionsDisplayDialog(parent, config, engine)


# This class exists solely so that the text doesn't get grayed out when the
# window is not in focus.
class MyStaticText(wx.PyControl):
    def __init__(self, parent, id=wx.ID_ANY, label="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0, validator=wx.DefaultValidator,
                 name="MyStaticText"):
        wx.PyControl.__init__(self, parent, id, pos, size, style|wx.NO_BORDER,
                              validator, name)
        wx.PyControl.SetLabel(self, label)
        self.InheritAttributes()
        self.SetInitialSize(size)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        self.Draw(dc)

    def Draw(self, dc):
        width, height = self.GetClientSize()

        if not width or not height:
            return

        backBrush = wx.Brush(wx.WHITE, wx.SOLID)
        dc.SetBackground(backBrush)
        dc.Clear()

        dc.SetTextForeground(wx.BLACK)
        dc.SetFont(self.GetFont())
        label = self.GetLabel()
        dc.DrawText(label, 0, 0)

    def OnEraseBackground(self, event):
        pass

    def SetLabel(self, label):
        wx.PyControl.SetLabel(self, label)
        self.InvalidateBestSize()
        self.SetSize(self.GetBestSize())
        self.Refresh()

    def SetFont(self, font):
        wx.PyControl.SetFont(self, font)
        self.InvalidateBestSize()
        self.SetSize(self.GetBestSize())
        self.Refresh()

    def DoGetBestSize(self):
        label = self.GetLabel()
        font = self.GetFont()

        if not font:
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)

        dc = wx.ClientDC(self)
        dc.SetFont(font)

        textWidth, textHeight = dc.GetTextExtent(label)
        best = wx.Size(textWidth, textHeight)
        self.CacheBestSize(best)
        return best

    def AcceptsFocus(self):
        return False

    def SetForegroundColour(self, colour):
        wx.PyControl.SetForegroundColour(self, colour)
        self.Refresh()

    def SetBackgroundColour(self, colour):
        wx.PyControl.SetBackgroundColour(self, colour)
        self.Refresh()

    def GetDefaultAttributes(self):
        return wx.StaticText.GetClassDefaultAttributes()

    def ShouldInheritColours(self):
        return True
