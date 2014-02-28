# by Brent Nesbitt
# Feb 22, 2014

# analyze output, and suggest when a brief in the dictionary would save strokes

import plover.dictionary.lookup_table
from plover.dictionary.candidate import Candidate
import wx


TITLE = "Brief Trainer"


class BriefTrainer(wx.Dialog):
    #Lookup better briefs for multi-stroke words
    MAX_SUGGESTIONS=7
    instances = []
    suggestions = []
    candidates = []
    deleted = []
    sug_row = []
    sug_stroke = []
    sug_translation = []
    text = ""
    backspaces = 0
    strokes = 0
    enabled = False

    def __init__(self, parent, config):
        self.config = config
        BriefTrainer.enabled = True
        style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP
        pos = (config.get_brief_suggestions_x(), config.get_brief_suggestions_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.strokes = []
        self.translations = []
        for i in range(BriefTrainer.MAX_SUGGESTIONS):
            row = wx.BoxSizer(wx.HORIZONTAL)
            BriefTrainer.sug_row.append(row)
            stroke = wx.StaticText(self, label=' ', style=wx.ALIGN_LEFT)
            BriefTrainer.sug_stroke.append(stroke)
            translation = wx.StaticText(self, label=' ', style=wx.ALIGN_RIGHT)
            BriefTrainer.sug_translation.append(translation)
            row.Add(stroke, proportion=1, flag=wx.EXPAND)
            row.Add(wx.StaticText(self, label=' :'))
            row.Add(translation, proportion=1, flag=wx.EXPAND)
            sizer.Add(row)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Layout()
        #sizer.Fit(self)

        self.Show()

        BriefTrainer.instances.append(self)
        self.Bind(wx.EVT_MOVE, self.on_move)

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_brief_suggestions_x(pos[0])
        self.config.set_brief_suggestions_y(pos[1])
        event.Skip()



    @staticmethod
    def display(parent, config):
        if (BriefTrainer.instances):
            return
        BriefTrainer(parent, config)

    @staticmethod
    def stroke_handler(stroke):
        if (stroke.is_correction):
            BriefTrainer.strokes = -1
            BriefTrainer.candidates.extend(BriefTrainer.deleted)
            BriefTrainer.deleted = []
        else:
            BriefTrainer.strokes = 1
            BriefTrainer.deleted = []
        BriefTrainer.process()

    @staticmethod
    def output_handler(backspaces, text):
        BriefTrainer.backspaces = backspaces
        BriefTrainer.text = text

    @staticmethod
    def process():
        # add this text to all candidates,
        # exclude the ones without translations
        # notify if translation exists with fewer strokes
        if not (BriefTrainer.enabled and plover.dictionary.lookup_table.loaded):
            return
        for candidate in list(BriefTrainer.candidates):
            candidate.addWord(BriefTrainer.strokes, BriefTrainer.backspaces, BriefTrainer.text)
            if (candidate.phrase):
                lookup = plover.dictionary.lookup_table.lookup(candidate.phrase)
                if (lookup):
                    if (len(lookup) < candidate.strokes):
                        suggestion = Candidate(str(lookup), candidate.phrase)
                        BriefTrainer.suggestions = [s for s in BriefTrainer.suggestions if s.phrase != candidate.phrase]
                        BriefTrainer.suggestions.append(suggestion)
                        while (len(BriefTrainer.suggestions) > BriefTrainer.MAX_SUGGESTIONS):
                            BriefTrainer.suggestions.remove(BriefTrainer.suggestions[0])
                        for i in range(len(BriefTrainer.suggestions)):
                            BriefTrainer.sug_stroke[i].SetLabel(BriefTrainer.suggestions[i].strokes)
                            BriefTrainer.sug_translation[i].SetLabel(BriefTrainer.suggestions[i].phrase)
                            BriefTrainer.sug_row[i].RecalcSizes
                        print(suggestion)

                else:
                    if not (BriefTrainer.backspaces==1): # don't delete if fingerspelling or suffix
                        BriefTrainer.deleted.append(candidate)
                        BriefTrainer.candidates.remove(candidate)
            else:
                BriefTrainer.candidates.remove(candidate)
        if (BriefTrainer.strokes > 0 and len(BriefTrainer.text)>0):
            BriefTrainer.candidates.append(Candidate(BriefTrainer.strokes, BriefTrainer.text))



