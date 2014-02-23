from os.path import splitext

from plover.dictionary.tst import TST


class LookupTable:
    #a reverse lookup TST
    table = TST()
    loaded = False

    def __init__(self):
        pass


    @staticmethod
    def load(dictionaries):
        for dictionary in dictionaries.dicts:
            for item in dictionary.iteritems():
                LookupTable.addToDictionary(item)

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