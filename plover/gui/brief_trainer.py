# by Brent Nesbitt
# Feb 22, 2014

# analyze output, and suggest when a brief in the dictionary would save strokes

import plover.dictionary.lookup_table
from plover.dictionary.candidate import Candidate
import wx


TITLE = "Brief Trainer"
MAX_SUGGESTIONS = 10

enabled = False
strokes = 0
backspaces = 0
text = ""
candidates = []
deleted_candidates = []
suggestions = []
current_index = 0

def stroke_handler(stroke):
    global strokes, candidates, deleted_candidates
    if (stroke.is_correction):
        strokes = -1
        candidates.extend(deleted_candidates)
        deleted_candidates = []
    else:
        strokes = 1
        deleted_candidates = []
    process()

def output_handler(bs, txt):
    global backspaces, text
    backspaces = bs
    text = txt

def display(parent, config):
    if (BriefTrainer.instances):
        return
    BriefTrainer(parent, config)

def process():
    global enabled, candidates, suggestions, deleted_candidates, strokes, backspaces, text, MAX_SUGGESTIONS, current_index
    # add this text to all candidates,
    # exclude the ones without translations
    # notify if translation exists with fewer strokes
    if not (enabled and plover.dictionary.lookup_table.loaded):
        return
    for candidate in list(candidates):
        candidate.addWord(strokes, backspaces, text)
        if (candidate.phrase):
            lookup = plover.dictionary.lookup_table.lookup(candidate.phrase)
            if (lookup):
                if (len(lookup) < candidate.strokes):
                    BriefTrainer.listbox.DeleteAllItems()
                    joined_stroke = '/'.join(lookup)
                    suggestion = Candidate(joined_stroke, candidate.phrase)
                    suggestions = [s for s in suggestions if s.phrase != candidate.phrase]
                    suggestions.append(suggestion)
                    while (len(suggestions) > MAX_SUGGESTIONS):
                        suggestions.remove(suggestions[0])
                    for i in range(len(suggestions)):
                        #print current_index
                        BriefTrainer.listbox.InsertStringItem(i, suggestions[i].strokes)
                        BriefTrainer.listbox.SetStringItem(i, 1, suggestions[i].phrase)
                        current_index+=1
                        if current_index > MAX_SUGGESTIONS:
                            current_index = MAX_SUGGESTIONS
                    #print(suggestion)

            else:
                if not (backspaces==1): # don't delete if fingerspelling or suffix
                    deleted_candidates.append(candidate)
                    candidates.remove(candidate)
        else:
            candidates.remove(candidate)
    if (strokes > 0 and len(text)>0):
        candidates.append(Candidate(strokes, text))


class BriefTrainer(wx.Dialog):
    #Lookup better briefs for multi-stroke words
    instances = []
    listbox = {}

    def __init__(self, parent, config):
        global MAX_SUGGESTIONS, TITLE
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






