# by Brent Nesbitt
# Feb 25, 2014

# hints about words that begin with what was already typed

import plover.dictionary.lookup_table
from plover.dictionary.candidate import Candidate

WORD_LIMIT=50
MIN_LENGTH=2
enabled = True
backspaces = 0
text = ""
candidates = []
deleted_candidates = []
output = []

def output_handler(bs, txt):
    global backspaces, text, candidates, deleted_candidates
    backspaces = bs
    text = txt
    if (not text):
        candidates.extend(deleted_candidates)
    else:
        deleted_candidates = []
    process()

def process():
    global enabled, backspaces, text, candidates, deleted_candidates, output, WORD_LIMIT
    if not (enabled and plover.dictionary.lookup_table.loaded):
        return
    output = []
    if (text):
        candidates.append(Candidate(1, ""))
        for candidate in (candidates): #reverse the order to prioritize longest matches
            candidate.addWord(1, backspaces, text)
            #print("processing: "+candidate.phrase)
            if (candidate.phrase):
                if (len(candidate.phrase) >= MIN_LENGTH):
                    lookup = plover.dictionary.lookup_table.prefixMatch(candidate.phrase.strip())
                    if (not lookup.empty()):
                        while (not lookup.empty()) and (len(output)<WORD_LIMIT):
                            phrase = lookup.get()
                            stroke = plover.dictionary.lookup_table.lookup(phrase)
                            suggestion=(Candidate(stroke, phrase))
                            output.append(suggestion)
                            print(suggestion)
                    else:
                        #print("lookup not found, marking: "+candidate.phrase)
                        deleted_candidates.append(candidate)
            else:
                #print("deleting blank marking")
                deleted_candidates.append(candidate)
        for del_candidate in deleted_candidates:
            candidates.remove(del_candidate)



def display(parent, config):
    pass
