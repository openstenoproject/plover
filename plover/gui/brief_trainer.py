# by Brent Nesbitt
# Feb 22, 2014

# analyze output, and suggest when a brief in the dictionary would save strokes

from plover.dictionary.lookup_table import LookupTable

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



class BriefTrainer:
    #Lookup better briefs for multi-stroke words
    candidates = []
    text = ""
    backspaces = 0
    strokes = 0
    lookupTable = LookupTable
    enabled = False

    def __init__(self):
        BriefTrainer.lookupTable.load()
        pass

    @staticmethod
    def stroke_handler(stroke):
        if (stroke.is_correction):
            BriefTrainer.strokes = -1
        else:
            BriefTrainer.strokes = 1
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
                    #print(candidate.strokes, candidate.phrase)
                    if (len(lookup) < candidate.strokes):
                        savings = str(candidate.strokes-len(lookup))
                        print(savings, str(lookup) + " : " + candidate.phrase)
                else:
                    BriefTrainer.candidates.remove(candidate)
            else:
                BriefTrainer.candidates.remove(candidate)
        if (BriefTrainer.strokes > 0 and len(BriefTrainer.text)>0):
            BriefTrainer.candidates.append(Candidate(BriefTrainer.strokes, BriefTrainer.text))
            #print(BriefTrainer.strokes, BriefTrainer.text)



