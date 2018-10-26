# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

# TODO: maybe move this code into the StenoDictionary itself. The current saver 
# structure is odd and awkward.
# TODO: write tests for this file

"""Common elements to all dictionary formats."""

from os.path import splitext
from bisect import bisect_left
import collections
import functools
import itertools
import operator
import re
import threading

from plover import formatting
from plover.registry import registry

# Characters to strip from ends of translation when performing inexact bisection search
SEARCH_STRIP_CHARS = "".join(set(
    formatting.SPACE + formatting.META_ATTACH_FLAG +
    formatting.META_START + formatting.META_END +
    formatting.META_LOWER + formatting.META_UPPER +
    formatting.META_CAPITALIZE + formatting.META_CARRY_CAPITALIZATION +
    formatting.META_GLUE_FLAG + formatting.META_KEY_COMBINATION))

# Regex to match ASCII characters matched as literals counting from the start of a regex pattern
REGEX_MATCH_PREFIX = re.compile(r'[\w \"#%\',\-:;<=>@`~]+').match


def _get_dictionary_class(filename):
    extension = splitext(filename)[1].lower()[1:]
    try:
        dict_module = registry.get_plugin('dictionary', extension).obj
    except KeyError:
        raise ValueError(
            'Unsupported extension: %s. Supported extensions: %s' %
            (extension, ', '.join(plugin.name for plugin in
                                  registry.list_plugins('dictionary'))))
    return dict_module

def _locked(fn):
    lock = threading.Lock()
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with lock:
            fn(*args, **kwargs)
    return wrapper

def _threaded(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=fn, args=args, kwargs=kwargs)
        t.start()
    return wrapper

def create_dictionary(resource, threaded_save=True):
    '''Create a new dictionary.

    The format is inferred from the extension.

    Note: the file is not created! The resulting dictionary save
    method must be called to finalize the creation on disk.
    '''
    d = _get_dictionary_class(resource).create(resource)
    if threaded_save:
        d.save = _threaded(_locked(d.save))
    return d

def load_dictionary(resource, threaded_save=True):
    '''Load a dictionary from a file.

    The format is inferred from the extension.
    '''
    d = _get_dictionary_class(resource).load(resource)
    if not d.readonly and threaded_save:
        d.save = _threaded(_locked(d.save))
    return d


class SimilarSearchDict(dict):
    """
    A special hybrid dictionary implementation using a sorted key list along with the usual hash map. This allows
    lookups for keys that are "similar" to a given key in O(log n) time as well as exact O(1) hash lookups, at the
    cost of extra memory to store transformed keys and increased time for individual item insertion and deletion.
    It is most useful for large dictionaries that are mutated rarely after initialization, and which have a need
    to compare and sort their keys by some measure other than their natural sorting order (if they have one).

    The "similarity function" returns a measure of how close two keys are to one another. This function should take a
    single key as input, and the return values should compare equal for keys that are deemed to be "similar". Even if
    they are not equal, keys with return values that are close will be close together in the list and may appear
    together in a search where equality is not required (i.e filter_keys with no filter). All implemented
    functionality other than similarity search is equivalent to that of a regular dictionary.

    The keys must be of a type that is immutable, hashable, and totally orderable (i.e. it is possible to rank all
    the keys from least to greatest using comparisons) both before and after applying the given similarity function.
    Inside the list, keys are stored in sorted order as tuples of (simkey, rawkey), which means they are ordered first
    by the value computed by the similarity function, and if those are equal, then by their natural value.

    The average-case time complexity for common operations are as follows:

    +-------------------+-------------------+------+
    |     Operation     | SimilarSearchDict | dict |
    +-------------------+-------------------+------+
    | Initialize        | O(n log n)        | O(n) |
    | Lookup (exact)    | O(1)              | O(1) |
    | Lookup (inexact)  | O(log n)          | O(n) |
    | Insert Item       | O(n)              | O(1) |
    | Delete Item       | O(n)              | O(1) |
    | Iteration         | O(n)              | O(n) |
    +-------------------+-------------------+------+
    """

    def __init__(self, simfn=None, *args, **kwargs):
        """ Initialize the dict and list to empty and set up the similarity function (identity if not provided).
            If other arguments were given, treat them as containing initial items to add as with dict.update(). """
        super().__init__()
        self._list = []
        if simfn is None:
            simfn = lambda x: x
        self._simfn = simfn
        if args or kwargs:
            self.update(*args, **kwargs)

    def clear(self):
        super().clear()
        self._list.clear()

    def __setitem__(self, k, v):
        """ Set an item in the dict. If the key didn't exist before, find where it goes in the list and insert it. """
        if k not in self:
            idx = self._index_exact(k)
            self._list.insert(idx, (self._simfn(k), k))
        super().__setitem__(k, v)

    def __delitem__(self, k):
        """ Delete an item from the dict and list (if it exists). This will not affect sort order. """
        if k in self:
            idx = self._index_exact(k)
            del self._list[idx]
            super().__delitem__(k)

    def update(self, *args, **kwargs):
        """ Update the dict and list using items from the given arguments. Because this is typically used
            to fill dictionaries with large amounts of items, a fast path is included if this one is empty. """
        if not self:
            super().update(*args, **kwargs)
            self._list = list(zip(map(self._simfn, self), self))
            self._list.sort()
        else:
            for (k, v) in dict(*args, **kwargs).items():
                self[k] = v

    def filter_keys(self, k, count=None, filterfn=None):
        """
        Starting from the leftmost position in the list where <k> could be, return keys in order until:
        1. (if <filterfn> is not None): the filter function returns False. The filter function is
           a T/F comparison between <k> and each list key when altered by the similarity function.
        2. (if <count> is not None): a maximum of <count> keys have been returned.
        Either condition will terminate the loop, as will reaching the end of the list.
        """
        simkey = self._simfn(k)
        idx_start = self._index_left(k)
        # Creating a list iterator and manually setting the index is much faster than islice
        # or subscripting for the case where an indefinite iterator over a long list is needed.
        list_iter = iter(self._list)
        list_iter.__setstate__(idx_start)
        keys = []
        keys_append = keys.append
        for (sk, rk) in list_iter:
            if filterfn is not None and not filterfn(sk, simkey):
                break
            keys_append(rk)
            if count is not None and len(keys) >= count:
                break
        return keys

    def get_similar_keys(self, k, count=None):
        """ Return a list of at most <count> keys that compare equal to <k> under the similarity function. """
        return self.filter_keys(k, count=count, filterfn=operator.eq)

    def prefix_search(self, prefix):
        """ Return a generator producing all possible raw keys that could contain <prefix>. """
        sim_prefix = self._simfn(prefix)
        # If the prefix is empty after transformation, it could possibly match anything in the list.
        if not sim_prefix:
            return map(operator.itemgetter(1), self._list)
        # All possibilities will be found in the sort order between the prefix itself (inclusive) and
        # the prefix with one added to the numerical value of its final character (exclusive).
        idx_start = self._index_left(sim_prefix, already_transformed=True)
        marker_end = sim_prefix[:-1] + chr(ord(sim_prefix[-1]) + 1)
        idx_end = self._index_left(marker_end, already_transformed=True)
        # If the range is empty, return a blank list instead of a generator so that it compares False.
        if idx_start == idx_end:
            return []
        return map(operator.itemgetter(1), self._list[idx_start:idx_end])

    def _index_left(self, k, already_transformed=False):
        """ Find the leftmost list index of the key <k> (or the place it should be) using bisection search. """
        # Out of all tuples with an equal first value, the 1-tuple with this value compares less than any 2-tuple.
        return bisect_left(self._list, (k if already_transformed else self._simfn(k),))

    def _index_exact(self, k):
        """ Find the exact list index of the key <k>  using bisection search (if it exists). """
        return bisect_left(self._list, (self._simfn(k), k))

    # Unimplemented methods from the base class that can mutate the object are unsafe. Make them return errors.
    def _UNSAFE_METHOD(self, *args, **kwargs): return NotImplementedError
    setdefault = pop = popitem = _UNSAFE_METHOD


class ReverseStenoDict(SimilarSearchDict):
    """
    A reverse dictionary with search capabilities for steno translations.
    It has special searches and the similarity function defined.

    Since normal dictionaries can have multiple keys that map to the same value (many-to-one),
    reverse dictionaries must be able to store multiple values under the same key (one-to-many).
    This means that the lookup results must be lists. These methods manage those lists.

    Naming conventions are reversed - in a reverse dictionary, we look up a value to get a list
    of keys that would map to it in the forward dictionary.
    """

    def __init__(self, *args, **kwargs):
        """ Initialize the base dict with the search function and any given arguments. """
        def simfn(s, strip=str.strip, lower=str.lower, strip_chars=SEARCH_STRIP_CHARS):
            """ Translations are similar if they compare equal when stripped of case and certain exterior symbols. """
            return lower(strip(s, strip_chars))
        super().__init__(simfn=simfn, *args, **kwargs)

    def append_key(self, v, k):
        """ Append the key <k> to the list located under the value <v>.
            Create a new list with that key if the value doesn't exist yet. """
        if v in self:
            self[v].append(k)
        else:
            self[v] = [k]

    def remove_key(self, v, k):
        """ Remove the key <k> from the list located under the value <v>. The key must exist.
            If it was the last key in the list, remove the dictionary entry entirely. """
        if v in self:
            self[v].remove(k)
            if not self[v]:
                del self[v]

    def match_forward(self, fdict):
        """ Make this dict into the reverse of the given forward dict by rebuilding all of the lists.
            It is a fast way to populate a reverse dict from scratch after creation. """
        self.clear()
        rdict = collections.defaultdict(list)
        list_append = list.append
        for (k, v) in fdict.items():
            list_append(rdict[v], k)
        self.update(rdict)

    def partial_match_values(self, v, count=None):
        """ Return a list of at most <count> values that are equal to
            or begin with the value <v> under the similarity function. """
        return self.filter_keys(v, count=count, filterfn=str.startswith)

    def regex_match_values(self, pattern, count=None):
        """ Return a list of at most <count> translations that match the regex <pattern> from the start. """
        # First, figure out how much of the pattern string from the start is literal (no regex special characters).
        prefix_match = REGEX_MATCH_PREFIX(pattern)
        prefix = prefix_match.group() if prefix_match else ""
        # If we know that all matches start with a certain prefix, we can narrow the range of our search.
        value_gen = self.prefix_search(prefix)
        if not value_gen:
            return []
        # If the prefix and pattern are equal, we have a complete literal string. Regex is not necessary.
        # Just do a partial case-sensitive match in that case. Otherwise, compile the regular expression.
        if prefix == pattern:
            match_op = operator.methodcaller("startswith", pattern)
        else:
            match_op = re.compile(pattern).match
        # Set up the match filter and limit the output to <count> if requested.
        results = filter(match_op, value_gen)
        if count is not None:
            results = itertools.islice(results, count)
        # Execute the entire chain of iterators at the end to return a list.
        return list(results)
