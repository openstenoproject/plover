# by Brent Nesbitt
# Feb 22, 2014

# analyze output, and suggest when a brief in the dictionary would save strokes

import plover.dictionary.lookup_table
from plover.dictionary.candidate import Candidate
import wx

TITLE = "Brief Trainer"
MAX_SUGGESTIONS = 10


class BriefTrainer(wx.Dialog):
    #Lookup better briefs for multi-stroke words
    enabled = False
    strokes = 0
    backspaces = 0
    text = ""
    candidates = []
    deleted_candidates = []
    suggestions = []
    current_index = 0
    instances = []
    listbox = {}

    def __init__(self, parent, config):
        self.config = config
        BriefTrainer.enabled = True
        style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.RESIZE_BORDER
        pos = (config.get_brief_suggestions_x(), config.get_brief_suggestions_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)
        self.Bind(wx.EVT_MOVE, self.on_move)

        main_sizer = wx.GridSizer(1, 1)

        BriefTrainer.listbox = wx.ListCtrl(self, size=wx.Size(400, 220), style=wx.LC_REPORT)
        BriefTrainer.listbox.InsertColumn(0, 'Stroke', width=200)
        BriefTrainer.listbox.InsertColumn(1, 'Translation', width=190)
        main_sizer.Add(BriefTrainer.listbox)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Show()

        for instance in BriefTrainer.instances:
            instance.Close()
        BriefTrainer.instances.append(self)

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_brief_suggestions_x(pos[0])
        self.config.set_brief_suggestions_y(pos[1])
        event.Skip()

    @staticmethod
    def process():
        # add this text to all candidates,
        # exclude the ones without translations
        # notify if translation exists with fewer strokes
        if not (BriefTrainer.enabled and plover.dictionary.lookup_table.loaded):
            return
        for candidate in list(BriefTrainer.candidates):
            candidate.addWord(BriefTrainer.strokes, BriefTrainer.backspaces, BriefTrainer.text)
            if candidate.phrase:
                lookup = plover.dictionary.lookup_table.lookup(candidate.phrase)
                if lookup:
                    if len(lookup) < candidate.strokes:
                        BriefTrainer.listbox.DeleteAllItems()
                        joined_stroke = '/'.join(lookup)
                        suggestion = Candidate(joined_stroke, candidate.phrase)
                        BriefTrainer.suggestions = [s for s in BriefTrainer.suggestions if s.phrase != candidate.phrase]
                        BriefTrainer.suggestions.append(suggestion)
                        while len(BriefTrainer.suggestions) > MAX_SUGGESTIONS:
                            BriefTrainer.suggestions.remove(BriefTrainer.suggestions[0])
                        for i in range(len(BriefTrainer.suggestions)):
                            BriefTrainer.listbox.InsertStringItem(i, BriefTrainer.suggestions[i].strokes)
                            BriefTrainer.listbox.SetStringItem(i, 1, BriefTrainer.suggestions[i].phrase)
                            BriefTrainer.current_index+=1
                            if BriefTrainer.current_index > MAX_SUGGESTIONS:
                                BriefTrainer.current_index = MAX_SUGGESTIONS

                else:
                    if not (BriefTrainer.backspaces==1):  # don't delete if fingerspelling or suffix
                        BriefTrainer.deleted_candidates.append(candidate)
                        BriefTrainer.candidates.remove(candidate)
            else:
                BriefTrainer.candidates.remove(candidate)
        if BriefTrainer.strokes > 0 and len(BriefTrainer.text)>0:
            BriefTrainer.candidates.append(Candidate(BriefTrainer.strokes, BriefTrainer.text))

    @staticmethod
    def stroke_handler(stroke):
        if stroke.is_correction:
            BriefTrainer.strokes = -1
            BriefTrainer.candidates.extend(BriefTrainer.deleted_candidates)
            BriefTrainer.deleted_candidates = []
        else:
            BriefTrainer.strokes = 1
            BriefTrainer.deleted_candidates = []
        BriefTrainer.process()

    @staticmethod
    def output_handler(bs, txt):
        BriefTrainer.backspaces = bs
        BriefTrainer.text = txt

    @staticmethod
    def display(parent, config):
        if BriefTrainer.instances:
            return
        BriefTrainer(parent, config)








