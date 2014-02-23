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
    strokes = 0
    lookupTable = LookupTable
    enabled = False

    def __init__(self):
        BriefTrainer.lookupTable.load()
        pass

    @staticmethod
    def numberOfStrokes(text):
        return len(text)

    @staticmethod
    def stroke_handler(stroke):
        BriefTrainer.strokes = BriefTrainer.numberOfStrokes(stroke.rtfcre)

    @staticmethod
    def output_handler(backspaces, text):
        # add this text to all candidates,
        # exclude the ones without translations
        # notify if translation exists with fewer strokes
        if not (BriefTrainer.enabled and BriefTrainer.lookupTable.loaded):
            return
        for candidate in list(BriefTrainer.candidates):
            candidate.addWord(backspaces, text)
            if (candidate.phrase):
                lookup = BriefTrainer.lookupTable.lookup(candidate.phrase)
                if (lookup):
                    if (BriefTrainer.numberOfStrokes(lookup) < candidate.strokes):
                        print(str(lookup) + " : " + candidate.phrase)
                else:
                    BriefTrainer.candidates.remove(candidate)
            else:
                BriefTrainer.candidates.remove(candidate)
        BriefTrainer.candidates.append(Candidate(BriefTrainer.strokes, text))






