# by Brent Nesbitt
# Feb 25, 2014

# hints about words that begin with what was already typed

import wx
import plover.dictionary.lookup_table
from plover.dictionary.candidate import Candidate

TITLE = "Stroke Helper"
WORD_LIMIT=50
MIN_LENGTH=2

enabled = False
backspaces = 0
text = ""
candidates = []
deleted_candidates = []
output = []

def output_handler(bs, txt):
    global backspaces, text, candidates, deleted_candidates, enabled
    if not enabled:
        return
    backspaces = bs
    text = txt
    if (not text):
        candidates.extend(deleted_candidates)
    else:
        deleted_candidates = []
    process()

def process():
    global enabled, backspaces, text, candidates, deleted_candidates, output, WORD_LIMIT
    if not (enabled and plover.dictionary.lookup_table.loaded):
        return
    output = []
    Dialog.listbox.DeleteAllItems()
    i=0
    if (text):
        candidates.append(Candidate(1, ""))
        for candidate in (candidates): #reverse the order to prioritize longest matches
            candidate.addWord(1, backspaces, text)
            #print("processing: "+candidate.phrase)
            if (candidate.phrase):
                if (len(candidate.phrase) >= MIN_LENGTH):
                    lookup = plover.dictionary.lookup_table.prefixMatch(candidate.phrase.strip())
                    if (not lookup.empty()):
                        while (not lookup.empty()) and (i<WORD_LIMIT):
                            phrase = lookup.get()
                            stroke = plover.dictionary.lookup_table.lookup(phrase)
                            joined_stroke = '/'.join(stroke)
                            Dialog.listbox.InsertStringItem(i, joined_stroke)
                            Dialog.listbox.SetStringItem(i, 1, phrase)
                            #suggestion=(Candidate(stroke, phrase))
                            #output.append(suggestion)
                            #print(suggestion)
                            i+=1
                    else:
                        #print("lookup not found, marking: "+candidate.phrase)
                        deleted_candidates.append(candidate)
            else:
                #print("deleting blank marking")
                deleted_candidates.append(candidate)
        for del_candidate in deleted_candidates:
            candidates.remove(del_candidate)

def display(parent, config):
    if (Dialog.instances):
        return
    Dialog(parent, config)

def refresh():
    for instance in Dialog.instances:
        instance.GetSizer().Fit(instance)

class Dialog(wx.Dialog):
    instances = []
    listbox = {}

    def __init__(self, parent, config):
        global TITLE, enabled
        enabled = True
        self.config = config
        style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.RESIZE_BORDER
        pos = (config.get_predictions_x(), config.get_predictions_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)
        self.Bind(wx.EVT_MOVE, self.on_move)

        main_sizer = wx.GridSizer(1, 1)
        
        Dialog.listbox = wx.ListCtrl(self, size=wx.Size(400, 400), style=wx.LC_REPORT)
        Dialog.listbox.InsertColumn(0, 'Stroke', width=200)
        Dialog.listbox.InsertColumn(1, 'Translation', width=190)
        main_sizer.Add(Dialog.listbox)

        for instance in Dialog.instances:
            instance.Close()
        Dialog.instances.append(self)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Show()

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_predictions_x(pos[0])
        self.config.set_predictions_y(pos[1])
        event.Skip()