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



class BriefTrainer:
    #Lookup better briefs for multi-stroke words
    MAX_SUGGESTIONS=5
    suggestions = []
    candidates = []
    deleted = []
    text = ""
    backspaces = 0
    strokes = 0
    lookupTable = LookupTable
    enabled = False

    @staticmethod
    def display(suggestion):
        pass

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
                        print(suggestion)

                else:
                    if not (BriefTrainer.backspaces==1): # don't delete if fingerspelling or suffix
                        BriefTrainer.deleted.append(candidate)
                        BriefTrainer.candidates.remove(candidate)
            else:
                BriefTrainer.candidates.remove(candidate)
        if (BriefTrainer.strokes > 0 and len(BriefTrainer.text)>0):
            BriefTrainer.candidates.append(Candidate(BriefTrainer.strokes, BriefTrainer.text))



