# by Brent Nesbitt
# Feb 25, 2014

# hints about words that begin with what was already typed

import plover.dictionary.lookup_table
from plover.dictionary.candidate import Candidate

WORD_LIMIT=25
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
    candidates.append(Candidate(0, text))
    for candidate in list(candidates):
        candidate.addWord(0, backspaces, text)
        if (candidate.phrase):
            if (len(candidate.phrase.strip()) > MIN_LENGTH):
                lookup = plover.dictionary.lookup_table.prefixMatch(candidate.phrase.strip())
                if (lookup.empty()):
                    deleted_candidates.append(candidate)
                    candidates.remove(candidate)
                else:
                    i=0
                    while ((not lookup.empty()) and (i<WORD_LIMIT)):
                        phrase = lookup.get()
                        stroke = plover.dictionary.lookup_table.lookup(phrase)
                        print(lookup.qsize(), stroke, phrase)
                        #output.append(Candidate(str(lookup)))
                        i += 1
        else:
            candidates.remove(candidate)


def display(parent, config):
    pass
