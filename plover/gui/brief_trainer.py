# by Brent Nesbitt
# Feb 22, 2014

# analyze output, and suggest when a brief in the dictionary would save strokes

from plover.dictionary.lookup_table import LookupTable
import wx


TITLE = "Brief Trainer"

class Candidate:
    #encapsulates potential incomplete briefs
    def __init__(self, strokes, phrase):
        self.strokes = strokes
        self.phrase = phrase

    def phrase(self):
        return self.phrase

    def addWord(self, backspaces, text):
        self.strokes+=BriefTrainer.strokes
        if (backspaces>0):
            self.phrase=self.phrase[0:-backspaces]+text
        else:
            self.phrase+=text

class Suggestion:
    #details for presenting to user
    def __init__(self, savings, stroke, phrase):
        self.savings = savings
        self.stroke = stroke
        self.phrase = phrase

    def __str__(self):
        return "("+str(self.savings)+") "+self.stroke+" : "+self.phrase

    def phrase(self):
        return self.phrase;



class BriefTrainer(wx.Dialog):
    #Lookup better briefs for multi-stroke words
    MAX_SUGGESTIONS=7
    instances = []
    suggestions = []
    candidates = []
    deleted = []
    sug_stroke = []
    sug_translation = []
    text = ""
    backspaces = 0
    strokes = 0
    lookupTable = LookupTable
    enabled = False

    def __init__(self, parent, config):
        self.config = config
        style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP
        pos = (config.get_brief_suggestions_x(), config.get_brief_suggestions_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.strokes = []
        self.translations = []
        for i in range(BriefTrainer.MAX_SUGGESTIONS):
            row = wx.BoxSizer(wx.HORIZONTAL)
            stroke = wx.StaticText(self, label='                                ')
            BriefTrainer.sug_stroke.append(stroke)
            translation = wx.StaticText(self, label=' ')
            BriefTrainer.sug_translation.append(translation)
            row.Add(stroke)
            row.Add(wx.StaticText(self, label=' : '))
            row.Add(translation)
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
        if not (BriefTrainer.enabled and BriefTrainer.lookupTable.loaded):
            return
        for candidate in list(BriefTrainer.candidates):
            candidate.addWord(BriefTrainer.backspaces, BriefTrainer.text)
            if (candidate.phrase):
                lookup = BriefTrainer.lookupTable.lookup(candidate.phrase)
                if (lookup):
                    if (len(lookup) < candidate.strokes):
                        savings = str(candidate.strokes-len(lookup))
                        suggestion = Suggestion(savings, str(lookup), candidate.phrase)
                        BriefTrainer.suggestions = [s for s in BriefTrainer.suggestions if s.phrase != candidate.phrase]
                        BriefTrainer.suggestions.append(suggestion)
                        while (len(BriefTrainer.suggestions) > BriefTrainer.MAX_SUGGESTIONS):
                            BriefTrainer.suggestions.remove(BriefTrainer.suggestions[0])
                        for i in range(len(BriefTrainer.suggestions)):
                            BriefTrainer.sug_stroke[i].SetLabel(BriefTrainer.suggestions[i].stroke)
                            BriefTrainer.sug_translation[i].SetLabel(BriefTrainer.suggestions[i].phrase)
                        #print(suggestion)

                else:
                    if not (BriefTrainer.backspaces==1): # don't delete if fingerspelling or suffix
                        BriefTrainer.deleted.append(candidate)
                        BriefTrainer.candidates.remove(candidate)
            else:
                BriefTrainer.candidates.remove(candidate)
        if (BriefTrainer.strokes > 0 and len(BriefTrainer.text)>0):
            BriefTrainer.candidates.append(Candidate(BriefTrainer.strokes, BriefTrainer.text))



