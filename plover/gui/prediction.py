# by Brent Nesbitt
# Feb 25, 2014

# hints about words that begin with what was already typed

from plover.dictionary.lookup_table import LookupTable

class Prediction:

    enabled = False
    backspaces = 0
    text = ""
    candidates = []
    suggestions = []


    @staticmethod
    def output_handler(backspaces, text):
        Prediction.backspaces = backspaces
        Prediction.text = text

    @staticmethod
    def process():
        if not (Prediction.enabled and LookupTable.loaded):
            return
        for candidate in list(Prediction.candidates):
            candidate.addWord(0, Prediction.backspaces, Prediction.text)
            if (candidate.phrase):
                lookup = LookupTable.prefixMatch(candidate.phrase)
