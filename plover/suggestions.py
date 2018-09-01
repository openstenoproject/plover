import collections
import re

from plover.steno import sort_steno_strokes


Suggestion = collections.namedtuple('Suggestion', 'text steno_list')

# Hard limit on results returned by search (to avoid slowdown on overly broad searches such as regex .*)
MATCH_LIMIT = 100


class Suggestions:
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def find(self, translation, count=MATCH_LIMIT, partial=False, regex=False):
        """ Find translations that are equal or similar (different case, prefixes, suffixes, etc.) to the given one.
            Special search types such as partial words and regular expressions are also available.
            Return a list of suggestion tuples with these translations along with the strokes that can produce them. """
        suggestions = []
        # Don't bother looking for suggestions on empty strings or whitespace.
        if translation and not translation.isspace():
            # Perform the requested type of lookup. The results should be sorted correctly when received.
            max_matches = min(count, MATCH_LIMIT)
            if regex:
                try:
                    items = self.dictionary.find_regex(translation, max_matches)
                except re.error as e:
                    return [Suggestion("Invalid regular expression", [(e.msg,)])]
            elif partial:
                items = self.dictionary.find_partial(translation, max_matches)
            else:
                items = self.dictionary.find_similar(translation)[:max_matches]
            # Package the lookup results into namedtuples for display.
            for (t, kl) in items:
                s = Suggestion(t, sort_steno_strokes(kl))
                # If we got an exact match, put it at the top of the list, otherwise append the results in order.
                if t == translation:
                    suggestions.insert(0, s)
                else:
                    suggestions.append(s)
        return suggestions
