# Copyright (c) 2013 Hesky Fisher.
# See LICENSE.txt for details.

"""StenoDictionary class and related functions.

A steno dictionary maps sequences of steno strokes to translations.

"""

import collections

class StenoDictionary(collections.MutableMapping):
    """A steno dictionary.

    This dictionary maps immutable sequences to translations and tracks the
    length of the longest key.

    Attributes:
    longest_key -- A read only property holding the length of the longest key.
    save -- If set, is a function that will save this dictionary.

    """
    def __init__(self, *args, **kw):
        self._dict = {}
        self._longest_key_length = 0
        self._longest_listener_callbacks = set()
        self.reverse = collections.defaultdict(list)
        self.casereverse = collections.defaultdict(set)
        self.filters = []
        self.update(*args, **kw)
        self.save = None
        self._path = ''

    @property
    def longest_key(self):
        """The length of the longest key in the dict."""
        return self._longest_key

    def __len__(self):
        return self._dict.__len__()
        
    def __iter__(self):
        return self._dict.__iter__()

    def __getitem__(self, key):
        value = self._dict.__getitem__(key)
        for f in self.filters:
            if f(key, value):
                raise KeyError('(%s, %s) is filtered' % (str(key), str(value)))
        return value

    def __setitem__(self, key, value):
        self._longest_key = max(self._longest_key, len(key))
        self._dict.__setitem__(key, value)
        self.reverse[value].append(key)
        # Case-insensitive reverse dict
        self.casereverse[value.lower()].add(value)

    def __delitem__(self, key):
        value = self._dict[key]
        self.reverse[value].remove(key)
        self._dict.__delitem__(key)
        if len(key) == self.longest_key:
            if self._dict:
                self._longest_key = max(len(x) for x in self._dict.iterkeys())
            else:
                self._longest_key = 0

    def __contains__(self, key):
        contained = self._dict.__contains__(key)
        if not contained:
            return False
        value = self._dict[key]
        for f in self.filters:
            if f(key, value):
                return False
        return True

    def set_path(self, path):
        self._path = path    

    def get_path(self):
        return self._path    

    def iterkeys(self):
        return self._dict.iterkeys()

    def itervalues(self):
        return self._dict.itervalues()
        
    def iteritems(self):
        return self._dict.iteritems()

    @property
    def _longest_key(self):
        return self._longest_key_length

    @_longest_key.setter
    def _longest_key(self, longest_key):
        if longest_key == self._longest_key_length:
            return
        self._longest_key_length = longest_key
        for callback in self._longest_listener_callbacks:
            callback(longest_key)

    def add_longest_key_listener(self, callback):
        self._longest_listener_callbacks.add(callback)

    def remove_longest_key_listener(self, callback):
        self._longest_listener_callbacks.remove(callback)

    def add_filter(self, f):
        self.filters.append(f)
        
    def remove_filter(self, f):
        self.filters.remove(f)
    
    def raw_get(self, key, default):
        """Bypass filters."""
        return self._dict.get(key, default)


class StenoDictionaryCollection(object):
    def __init__(self):
        self.dicts = []
        self.filters = []
        self.longest_key = 0
        self.longest_key_callbacks = set()

    def set_dicts(self, dicts):
        for d in self.dicts:
            d.remove_longest_key_listener(self._longest_key_listener)
        self.dicts = dicts[:]
        self.dicts.reverse()
        for d in dicts:
            d.add_longest_key_listener(self._longest_key_listener)
        self._longest_key_listener()

    def lookup(self, key):
        for d in self.dicts:
            value = d.get(key, None)
            if value:
                for f in self.filters:
                    if f(key, value):
                        return None
                return value

    def raw_lookup(self, key):
        for d in self.dicts:
            value = d.get(key, None)
            if value:
                return value

    def reverse_lookup(self, value):
        for d in self.dicts:
            if hasattr(d, 'reverse_lookup'):
                key = d.reverse_lookup(value)
            else:
                key = d.reverse.get(value, None)
            if key:
                return key

    def casereverse_lookup(self, value):
        for d in self.dicts:
            if hasattr(d, 'reverse_lookup'):
                key = set((value.lower(),))
            else:
                key = d.casereverse.get(value, None)
            if key:
                return key

    def set(self, key, value):
        if self.dicts:
            self.dicts[0][key] = value

    def save(self):
        if self.dicts:
            self.dicts[0].save()

    def save_all(self):
        for dict in self.dicts:
            dict.save()

    def get_by_path(self, path):
        for d in self.dicts:
            if d.get_path() == path:
                return d

    def add_filter(self, f):
        self.filters.append(f)

    def remove_filter(self, f):
        self.filters.remove(f)

    def add_longest_key_listener(self, callback):
        self.longest_key_callbacks.add(callback)

    def remove_longest_key_listener(self, callback):
        self.longest_key_callbacks.remove(callback)
    
    def _longest_key_listener(self, ignored=None):
        new_longest_key = max(d.longest_key for d in self.dicts)
        if new_longest_key != self.longest_key:
            self.longest_key = new_longest_key
            for c in self.longest_key_callbacks:
                c(new_longest_key)
