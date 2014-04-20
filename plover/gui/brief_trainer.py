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
    global enabled, candidates, suggestions, deleted_candidates, strokes, backspaces, text, MAX_SUGGESTIONS
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
                    suggestion = Candidate(str(lookup), candidate.phrase)
                    suggestions = [s for s in suggestions if s.phrase != candidate.phrase]
                    suggestions.append(suggestion)
                    while (len(suggestions) > MAX_SUGGESTIONS):
                        suggestions.remove(suggestions[0])
                    for i in range(len(suggestions)):
                        BriefTrainer.controls[(i*2)].SetLabel(suggestions[i].strokes)
                        BriefTrainer.controls[(i*2)+1].SetLabel(suggestions[i].phrase)
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
    controls = []

    def __init__(self, parent, config):
        global MAX_SUGGESTIONS, TITLE
        self.config = config
        BriefTrainer.enabled = True
        style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.RESIZE_BORDER
        pos = (config.get_brief_suggestions_x(), config.get_brief_suggestions_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)
        self.Bind(wx.EVT_MOVE, self.on_move)

        main_sizer = wx.GridSizer(MAX_SUGGESTIONS, 2, 3, 10)
        for i in range(MAX_SUGGESTIONS):
            stroke = wx.StaticText(self, label='                            ', style=wx.ALIGN_LEFT)
            BriefTrainer.controls.append(stroke)
            main_sizer.Add(stroke, 0, wx.EXPAND)
            translation = wx.StaticText(self, label=' ', style=wx.ALIGN_RIGHT)
            BriefTrainer.controls.append(translation)
            main_sizer.Add(translation, 0, wx.EXPAND)

        self.SetSizer(main_sizer)
        #self.SetAutoLayout(True)
        #sizer.Layout()
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






