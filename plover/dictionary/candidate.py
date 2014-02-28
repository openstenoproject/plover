class Candidate:
    #encapsulates potential incomplete briefs
    def __init__(self, strokes, phrase):
        self.strokes = strokes
        self.phrase = phrase

    def __str__(self):
        return("("+str(self.strokes) + ") : " + self.phrase)

    def phrase(self):
        return self.phrase

    def addWord(self, stroke, backspaces, text):
        self.strokes+=stroke
        if (backspaces>0):
            self.phrase=self.phrase[0:-backspaces]+text
        else:
            self.phrase+=text
