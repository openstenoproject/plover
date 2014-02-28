from os.path import splitext
import threading

from plover.dictionary.tst import TST

#a reverse lookup TST

table = TST()
loaded = False

def load(dictionary_collection):
    global loaded
    if (not loaded):
        background=threading.Thread(target=load_in_background, args=[dictionary_collection.dicts])
        background.start()

def load_in_background(dictionaries):
    global loaded
    for dictionary in dictionaries:
        for item in dictionary.iteritems():
            addToDictionary(item)
    loaded=True

def lookup(phrase):
    global table
    if (not phrase.strip()):
        return
    return table.get(phrase.strip())

def addToDictionary(item):
    global table
    phrase=item[1]
    new_stroke = item[0]
    if (not phrase):
        return
    current_stroke = table.get(phrase)
    if (current_stroke):
        new_stroke = shortestOf(current_stroke, new_stroke)
        if (current_stroke == new_stroke):
            return
    table.put(phrase, new_stroke)

def prefixMatch(word):
    global table
    return table.prefixMatch(word)

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



