# Copyright (c) 2015 Kevin Nygaard
# See LICENSE.txt for details.

"""A gui display of stroke suggestions """

import wx
import re
from wx.lib.utils import AdjustRectToScreen
from plover.gui.util import find_fixed_width_font
from plover.steno import STENO_KEY_ORDER

PAT = re.compile(r'[-\'"\w]+|[^\w\s]')
TITLE = 'Plover: Suggestions Display'
ON_TOP_TEXT = "Always on top"
UI_BORDER = 4
LAST_WORD_TEXT = 'Last Word: %s'
DEFAULT_LAST_WORD = 'N/A'
HISTORY_SIZE = 10
MAX_DISPLAY_LINES = 20
STROKE_INDENT = 2
DISPLAY_WIDTH = len(STENO_KEY_ORDER) + 2 * STROKE_INDENT + 1 # extra +1 for /

class SuggestionsDisplayDialog(wx.Dialog):

    other_instances = []

    def __init__(self, parent, config, engine):
        self.config = config
        self.engine = engine
        self.words = ''
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
        dc = wx.ScreenDC()
        dc.SetFont(fixed_font)
        fixed_text_size = dc.GetTextExtent(' ' * DISPLAY_WIDTH)
        dc.SetFont(standard_font)
        standard_text_size = dc.GetTextExtent(' ' * DISPLAY_WIDTH)

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
        self.strokes_indent = ' ' * STROKE_INDENT
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

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_suggestions_display_x(pos[0])
        self.config.set_suggestions_display_y(pos[1])
        event.Skip()

    def on_close(self, event):
        self.other_instances.remove(self)
        event.Skip()

    def lookup_suggestions(self, phrase):
        ''' Return stroke suggestions for a given phrase, if it exists

            If we can't find an entry, we start manipulating the phrase to see if we
            can come up with something for the user. This allows for suggestions to
            be given for prefixes/suffixes.

        '''

        suggestions = []

        mods  = ['%s', '{^%s}', '{^%s^}', '{%s^}', '{&%s}']
        d     = self.engine.get_dictionary()

        similar_words = d.casereverse_lookup(phrase.lower())
        if similar_words:
            similar_words_list = list(similar_words - set([phrase]))
        else:
            similar_words_list = []


        for p in [phrase] + similar_words_list:
            for x in [mod % p for mod in mods]:
                strokes_list = d.reverse_lookup(x)
                if not strokes_list:
                    continue
                else:
                    # Return list of suggestions, sorted by fewest strokes, then fewest keys
                    suggestions.append((x, sorted(strokes_list, key=lambda x: len(x) * 32 + sum(map(len, x)))))

        return suggestions

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

        # Limit history.
        if len(self.history) == HISTORY_SIZE:
            length = self.history.pop(0)
            last_position = self.listbox.GetLastPosition()
            self.listbox.Remove(last_position - length, last_position)
        # Insert last entry on top.
        self.listbox.SetInsertionPoint(0)

        split_words = PAT.findall(self.words)
        interp_phrase = ''
        for phrase in SuggestionsDisplayDialog.tails(split_words):
            phrase = ' '.join(phrase)
            suggestions_list = self.lookup_suggestions(phrase)
            if not suggestions_list:
                continue

            for x, suggestions in suggestions_list:
                self.listbox.SetDefaultStyle(self.word_style)
                self.listbox.WriteText(x + '\n')
                self.listbox.SetDefaultStyle(self.stroke_style)
                # Limit arbitrarily to 10 suggestions per word
                for stroke_list in suggestions[:10]:
                    line_length = 0
                    for n, stroke in enumerate(stroke_list):
                        if 0 == n:
                            text = stroke
                            indent = self.strokes_indent
                        else:
                            text = '/' + stroke
                            indent = 2 * self.strokes_indent
                        if 0 == line_length:
                            text = indent + text
                            line_length = len(text)
                        elif (len(text) + line_length) > DISPLAY_WIDTH:
                            text = '\n' + indent + text
                            line_length = len(text)
                        else:
                            line_length += len(text)
                        self.listbox.WriteText(text)
                    self.listbox.WriteText('\n')

            # Set interp_phrase on first found suggestions for given phrase
            if suggestions_list and not interp_phrase:
                interp_phrase = phrase

        if not interp_phrase:
            interp_phrase = DEFAULT_LAST_WORD
            if len(split_words) > 0:
                self.listbox.SetDefaultStyle(self.word_style)
                self.listbox.WriteText(split_words[-1] + '\n')
                self.listbox.SetDefaultStyle(self.no_suggestion_style)
                self.listbox.WriteText(self.no_suggestion_indent)
                self.listbox.WriteText('No suggestions\n')

        length = self.listbox.GetInsertionPoint()
        if length:
            self.history.append(length)
            # Reset style after final \n, so following
            # word is correctly displayed.
            self.listbox.SetDefaultStyle(self.word_style)
            self.listbox.WriteText('')
            # Make sure first line is shown.
            self.listbox.ShowPosition(0)

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

