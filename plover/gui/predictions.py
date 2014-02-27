# by Brent Nesbitt
# Feb 25, 2014

# hints about words that begin with what was already typed

from plover.dictionary.lookup_table import LookupTable
from plover.dictionary.lookup_table import Candidate

WORD_LIMIT=25
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
    if not (enabled and LookupTable.loaded):
        return
    for candidate in list(candidates):
        candidate.addWord(0, backspaces, text)
        if (candidate.phrase):
            lookup = LookupTable.prefixMatch(candidate.phrase)
            if lookup:
                i=0
                while lookup and (i<WORD_LIMIT):
                    print(lookup)
                    #output.append(Candidate(str(lookup)))
            else:
                deleted_candidates.append(candidate)
                candidates.remove(candidate)
        else:
            candidates.remove(candidate)
    candidates.append(Candidate(0, text))

def display(parent, config):
    pass
