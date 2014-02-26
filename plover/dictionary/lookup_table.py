from os.path import splitext
import threading

from plover.dictionary.tst import TST


class LookupTable:
    #a reverse lookup TST
    table = TST()
    loaded = False


    @staticmethod
    def load(dictionary_collection):
        if (not LookupTable.loaded):
            background=threading.Thread(target=LookupTable.load_in_background, args=[dictionary_collection.dicts])
            background.start()


    @staticmethod
    def load_in_background(dictionaries):
        for dictionary in dictionaries:
            for item in dictionary.iteritems():
                LookupTable.addToDictionary(item)
        LookupTable.loaded=True

    @staticmethod
    def lookup(phrase):
        if (not phrase.strip()):
            return
        return LookupTable.table.get(phrase.strip())

    @staticmethod
    def addToDictionary(item):
        phrase=item[1]
        new_stroke = item[0]
        if (not phrase):
            return
        current_stroke = LookupTable.table.get(phrase)
        if (current_stroke):
            new_stroke = LookupTable.shortestOf(current_stroke, new_stroke)
            if (current_stroke == new_stroke):
                return
        LookupTable.table.put(phrase, new_stroke)

    @staticmethod
    def shortestOf(stroke1, stroke2):
        #compare strokes by existence, then number of strokes, then absolute length
        if (not (stroke1 or stroke2)):
            return ""
        if (not stroke2):
            return stroke1
        if (not stroke1):
            return stroke2
        if (len(stroke1) < len(stroke2)):
            return stroke1
        if (len(stroke1) > len(stroke2)):
            return stroke2
        if (len(str(stroke1)) < len(str(stroke2))):
            return stroke1
        return stroke2

class Candidate:
    #encapsulates potential incomplete briefs
    def __init__(self, strokes, phrase):
        self.strokes = strokes
        self.phrase = phrase

    def phrase(self):
        return self.phrase

    def addWord(self, stroke, backspaces, text):
        self.strokes+=stroke
        if (backspaces>0):
            self.phrase=self.phrase[0:-backspaces]+text
        else:
            self.phrase+=text
