# by Brent Nesbitt
# Feb 25, 2014

# hints about words that begin with what was already typed

import wx
from plover.dictionary.candidate import Candidate

TITLE = "Stroke Helper"
WORD_LIMIT=50
MIN_LENGTH=2


class Predictions(wx.Dialog):
    enabled = False
    backspaces = 0
    text = ""
    candidates = []
    deleted_candidates = []
    instances = []
    listbox = {}
    dictionary = None

    def __init__(self, parent, dict, config):
        global dictionary
        dictionary = dict
        Predictions.enabled = True
        self.config = config
        style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.RESIZE_BORDER
        pos = (config.get_predictions_x(), config.get_predictions_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)
        self.Bind(wx.EVT_MOVE, self.on_move)

        main_sizer = wx.GridSizer(1, 1)

        Predictions.listbox = wx.ListCtrl(self, size=wx.Size(400, 400), style=wx.LC_REPORT)
        Predictions.listbox.InsertColumn(0, 'Stroke', width=200)
        Predictions.listbox.InsertColumn(1, 'Translation', width=190)
        main_sizer.Add(Predictions.listbox)

        for instance in Predictions.instances:
            instance.Close()
        Predictions.instances.append(self)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Show()

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_predictions_x(pos[0])
        self.config.set_predictions_y(pos[1])
        event.Skip()

    @staticmethod
    def process():
        global dictionary
        if not (Predictions.enabled):
            return
        Predictions.listbox.DeleteAllItems()
        if (not dictionary.trie_loaded):
            Predictions.listbox.InsertStringItem(0, "Initializing...")
            return
        i=0
        if Predictions.text:
            Predictions.candidates.append(Candidate(1, ""))
            for candidate in Predictions.candidates: # reverse the order to prioritize longest matches
                candidate.addWord(1, Predictions.backspaces, Predictions.text)
                if candidate.phrase:
                    if len(candidate.phrase) >= MIN_LENGTH:
                        lookup = dictionary.prefix_match(candidate.phrase.strip())
                        if not lookup.empty():
                            while (not lookup.empty()) and (i < WORD_LIMIT):
                                phrase = lookup.get()
                                stroke = dictionary.trie_lookup(phrase)
                                joined_stroke = '/'.join(stroke)
                                Predictions.listbox.InsertStringItem(i, joined_stroke)
                                Predictions.listbox.SetStringItem(i, 1, phrase)
                                i += 1
                        else:
                            Predictions.deleted_candidates.append(candidate)
                else:
                    Predictions.deleted_candidates.append(candidate)
            for del_candidate in Predictions.deleted_candidates:
                Predictions.candidates.remove(del_candidate)


    @staticmethod
    def output_handler(bs, txt):
        if not Predictions.enabled:
            return
        Predictions.backspaces = bs
        Predictions.text = txt
        if not Predictions.text:
            Predictions.candidates.extend(Predictions.deleted_candidates)
        else:
            Predictions.deleted_candidates = []
        Predictions.process()

    @staticmethod
    def display(parent, config):
        if Predictions.instances:
            return
        Predictions(parent, config)

    @staticmethod
    def refresh():
        for instance in Predictions.instances:
            instance.GetSizer().Fit(instance)
