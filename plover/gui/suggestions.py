# Copyright (c) 2015 Kevin Nygaard
# See LICENSE.txt for details.

"""A gui display of stroke suggestions """

import wx
import re
from wx.lib.utils import AdjustRectToScreen
from plover.gui.util import find_fixed_width_font, shorten_unicode
from plover import system
from plover.suggestions import Suggestion
from plover.translation import escape_translation

PAT = re.compile(r'[-\'"\w]+|[^\w\s]')
TITLE = 'Plover: Suggestions Display'
ON_TOP_TEXT = "Always on top"
UI_BORDER = 4
LAST_WORD_TEXT = 'Last Word: %s'
DEFAULT_LAST_WORD = 'N/A'
MAX_DISPLAY_LINES = 20
STROKE_INDENT = 2

class SuggestionsDisplayDialog(wx.Dialog):

    other_instances = []

    def __init__(self, parent, config, engine):
        self.config = config
        self.engine = engine
        self.words = u''
        on_top = config.get_suggestions_display_on_top()
        style = wx.DEFAULT_DIALOG_STYLE
        style |= wx.RESIZE_BORDER
        if on_top:
            style |= wx.STAY_ON_TOP
        pos = (config.get_suggestions_display_x(), config.get_suggestions_display_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.on_top = wx.CheckBox(self, label=ON_TOP_TEXT)
        self.on_top.SetValue(config.get_suggestions_display_on_top())
        self.on_top.Bind(wx.EVT_CHECKBOX, self.handle_on_top)
        sizer.Add(self.on_top, flag=wx.ALL, border=UI_BORDER)

        sizer.Add(wx.StaticLine(self), flag=wx.EXPAND)

        self.listbox = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP|wx.BORDER_NONE)

        standard_font = self.listbox.GetFont()
        fixed_font = find_fixed_width_font()

        # Calculate required width and height.
        display_width = len(system.KEYS) + 2 * STROKE_INDENT + 1 # extra +1 for /
        dc = wx.ScreenDC()
        dc.SetFont(fixed_font)
        fixed_text_size = dc.GetTextExtent(' ' * display_width)
        dc.SetFont(standard_font)
        standard_text_size = dc.GetTextExtent(' ' * display_width)

        text_width, text_height = [max(d1, d2) for d1, d2 in
                                   zip(fixed_text_size, standard_text_size)]

        # Will show MAX_DISPLAY_LINES lines (+1 for inter-line spacings...).
        self.listbox.SetSize(wx.Size(text_width, text_height * (MAX_DISPLAY_LINES + 1)))

        self.history = []

        sizer.Add(self.listbox,
                  proportion=1,
                  flag=wx.ALL | wx.FIXED_MINSIZE | wx.EXPAND,
                  border=UI_BORDER)

        self.word_style = wx.TextAttr()
        self.word_style.SetFont(standard_font)
        self.word_style.SetFontStyle(wx.FONTSTYLE_NORMAL)
        self.word_style.SetFontWeight(wx.FONTWEIGHT_BOLD)
        self.word_style.SetAlignment(wx.TEXT_ALIGNMENT_LEFT)
        self.stroke_style = wx.TextAttr()
        self.stroke_style.SetFont(fixed_font)
        self.stroke_style.SetFontStyle(wx.FONTSTYLE_NORMAL)
        self.stroke_style.SetFontWeight(wx.FONTWEIGHT_NORMAL)
        self.stroke_style.SetAlignment(wx.TEXT_ALIGNMENT_LEFT)
        self.no_suggestion_style = wx.TextAttr()
        self.no_suggestion_style.SetFont(standard_font)
        self.no_suggestion_style.SetFontStyle(wx.FONTSTYLE_ITALIC)
        self.no_suggestion_style.SetFontWeight(wx.FONTWEIGHT_NORMAL)
        self.no_suggestion_style.SetAlignment(wx.TEXT_ALIGNMENT_LEFT)
        self.strokes_indent = u' ' * STROKE_INDENT
        self.no_suggestion_indent = self.strokes_indent
        self.no_suggestion_indent *= (fixed_text_size[0] / standard_text_size[0])

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Layout()
        sizer.Fit(self)

        self.Show()
        self.close_all()
        self.other_instances.append(self)

        self.SetRect(AdjustRectToScreen(self.GetRect()))

        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_SIZE, self.on_resize)

    def on_resize(self, event):
        self.Layout()
        # Reflow suggestions text on resize.
        history = self.history
        self.history = []
        self.listbox.Clear()
        for suggestion_list, _ in history:
            self.show_suggestions(suggestion_list)

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_suggestions_display_x(pos[0])
        self.config.set_suggestions_display_y(pos[1])
        event.Skip()

    def on_close(self, event):
        self.other_instances.remove(self)
        event.Skip()

    def show_suggestions(self, suggestion_list):

        # Limit history.
        undo_levels = self.config.get_undo_levels()
        while len(self.history) >= undo_levels:
            _, text_length = self.history.pop(0)
            last_position = self.listbox.GetLastPosition()
            self.listbox.Remove(last_position - text_length, last_position)
        # Insert last entry on top.
        self.listbox.SetInsertionPoint(0)

        # Find available text width.
        max_width = self.listbox.Size[0]
        # Yes, 2 times the scrollbar width, because...
        max_width -= 2 * wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
        dc = wx.ScreenDC()
        dc.SetFont(self.stroke_style.GetFont())

        for suggestion in suggestion_list:
            self.listbox.SetDefaultStyle(self.word_style)
            self.listbox.WriteText(
                shorten_unicode(escape_translation(suggestion.text)) + u'\n'
            )
            if not suggestion.steno_list:
                self.listbox.SetDefaultStyle(self.no_suggestion_style)
                self.listbox.WriteText(self.no_suggestion_indent)
                self.listbox.WriteText(u'No suggestions\n')
                continue
            self.listbox.SetDefaultStyle(self.stroke_style)
            # Limit arbitrarily to 10 suggestions per word.
            for stroke_list in suggestion.steno_list[:10]:
                line_text = None
                for n, stroke in enumerate(stroke_list):
                    if 0 == n:
                        line_text = text = self.strokes_indent + stroke
                    else:
                        text = u'/' + stroke
                        line_text += text
                        if dc.GetTextExtent(line_text)[0] >= max_width:
                            line_text = 2 * self.strokes_indent + text
                            text = u'\n' + line_text
                    self.listbox.WriteText(shorten_unicode(text))
                self.listbox.WriteText(u'\n')

        length = self.listbox.GetInsertionPoint()
        assert length
        self.history.append((suggestion_list, length))
        # Reset style after final \n, so following
        # word is correctly displayed.
        self.listbox.SetDefaultStyle(self.word_style)
        self.listbox.WriteText('')
        # Make sure first line is shown.
        self.listbox.ShowPosition(0)

    def show_stroke(self, old, new):
        for action in old:
            remove = len(action.text)
            self.words = self.words[:-remove]
            self.words = self.words + action.replace

        for action in new:
            remove = len(action.replace)
            if remove > 0:
                self.words = self.words[:-remove]
            self.words = self.words + action.text

        # Limit phrasing memory to 100 characters, because most phrases probably
        # don't exceed this length
        self.words = self.words[-100:]

        suggestion_list = []
        split_words = PAT.findall(self.words)
        for phrase in SuggestionsDisplayDialog.tails(split_words):
            phrase = u' '.join(phrase)
            suggestion_list.extend(self.engine.get_suggestions(phrase))

        if not suggestion_list and split_words:
            suggestion_list = [Suggestion(split_words[-1], [])]

        if suggestion_list:
            self.show_suggestions(suggestion_list)

    def handle_on_top(self, event):
        on_top = event.IsChecked()
        self.config.set_suggestions_display_on_top(on_top)
        style = wx.DEFAULT_DIALOG_STYLE
        if on_top:
            style |= wx.STAY_ON_TOP
        self.SetWindowStyleFlag(style)

    @staticmethod
    def tails(ls):
        ''' Return all tail combinations (a la Haskell)

            tails :: [x] -> [[x]]
            >>> tails('abcd')
            ['abcd', 'bcd', 'cd', d']

        '''

        for i in range(len(ls)):
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

