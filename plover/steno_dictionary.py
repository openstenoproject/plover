# Copyright (c) 2013 Hesky Fisher.
# See LICENSE.txt for details.

"""StenoDictionary class and related functions.

A steno dictionary maps sequences of steno strokes to translations.

"""

import collections
import shutil

from plover.resource import ASSET_SCHEME, resource_filename, resource_timestamp


class StenoDictionary(collections.MutableMapping):
    """A steno dictionary.

    This dictionary maps immutable sequences to translations and tracks the
    length of the longest key.

    Attributes:
    longest_key -- A read only property holding the length of the longest key.
    timestamp -- File last modification time, used to detect external changes.

    """
    def __init__(self):
        self._dict = {}
        self._longest_key_length = 0
        self._longest_listener_callbacks = set()
        self.reverse = collections.defaultdict(list)
        # Case-insensitive reverse dict
        self.casereverse = collections.defaultdict(collections.Counter)
        self.filters = []
        self.timestamp = 0
        self.readonly = False
        self.enabled = True
        self.path = None

    @classmethod
    def create(cls, resource):
        assert not resource.startswith(ASSET_SCHEME)
        d = cls()
        if d.readonly:
            raise ValueError('%s does not support creation' % cls.__name__)
        d.path = resource
        return d

    @classmethod
    def load(cls, resource):
        filename = resource_filename(resource)
        timestamp = resource_timestamp(filename)
        d = cls()
        d._load(filename)
        if resource.startswith(ASSET_SCHEME):
            d.readonly = True
        d.path = resource
        d.timestamp = timestamp
        return d

    def save(self):
        assert not self.readonly
        filename = resource_filename(self.path)
        # Write the new file to a temp location.
        tmp = filename + '.tmp'
        self._save(tmp)
        timestamp = resource_timestamp(tmp)
        # Then move the new file to the final location.
        shutil.move(tmp, filename)
        # And update our timestamp.
        self.timestamp = timestamp

    def _load(self, filename):
        raise NotImplementedError()

    def _save(self, filename):
        raise NotImplementedError()

    @property
    def longest_key(self):
        """The length of the longest key in the dict."""
        return self._longest_key

    def __len__(self):
        return self._dict.__len__()

    def __iter__(self):
        return self._dict.__iter__()

    def __getitem__(self, key):
        return self._dict.__getitem__(key)

    def __setitem__(self, key, value):
        assert not self.readonly
        self._longest_key = max(self._longest_key, len(key))
        self._dict[key] = value
        self.reverse[value].append(key)
        self.casereverse[value.lower()][value] += 1

    def __delitem__(self, key):
        assert not self.readonly
        value = self._dict.pop(key)
        self.reverse[value].remove(key)
        counter = self.casereverse[value.lower()]
        count = counter.pop(value) - 1
        if count:
            counter[value] = count
        if len(key) == self.longest_key:
            if self._dict:
                self._longest_key = max(len(x) for x in self._dict)
            else:
                self._longest_key = 0

    def __contains__(self, key):
        return self.get(key) is not None

    def reverse_lookup(self, value):
        return self.reverse[value]

    def casereverse_lookup(self, value):
        return list(self.casereverse[value].keys())

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
        for d in self.dicts:
            d.add_longest_key_listener(self._longest_key_listener)
        self._longest_key_listener()

    def _lookup(self, key, dicts=None, filters=()):
        if dicts is None:
            dicts = self.dicts
        key_len = len(key)
        if key_len > self.longest_key:
            return None
        for d in dicts:
            if not d.enabled:
                continue
            if key_len > d.longest_key:
                continue
            value = d.get(key)
            if value:
                for f in filters:
                    if f(key, value):
                        return None
                return value

    def lookup(self, key):
        return self._lookup(key, filters=self.filters)

    def raw_lookup(self, key):
        return self._lookup(key)

    def reverse_lookup(self, value):
        keys = []
        for n, d in enumerate(self.dicts):
            if not d.enabled:
                continue
            for k in d.reverse_lookup(value):
                # Ignore key if it's overriden by a higher priority dictionary.
                if self._lookup(k, dicts=self.dicts[:n]) is None:
                    keys.append(k)
        return keys

    def casereverse_lookup(self, value):
        for d in self.dicts:
            if not d.enabled:
                continue
            key = d.casereverse_lookup(value)
            if key:
                return key

    def set(self, key, value, path=None):
        if path is None:
            d = self.dicts[0]
        else:
            d = self[path]
        d[key] = value

    def save(self, path_list=None):
        '''Save the dictionaries in <path_list>.

        If <path_list> is None, all writable dictionaries are saved'''
        if path_list is None:
            dict_list = [d for d in self if dictionary.save is not None]
        else:
            dict_list = [self[path] for path in path_list]
        for d in dict_list:
            d.save()

    def get(self, path):
        for d in self.dicts:
            if d.path == path:
                return d

    def __getitem__(self, path):
        d = self.get(path)
        if d is None:
            raise KeyError(repr(path))
        return d

    def __iter__(self):
        for d in self.dicts:
            yield d.path

    def add_filter(self, f):
        self.filters.append(f)

    def remove_filter(self, f):
        self.filters.remove(f)

    def add_longest_key_listener(self, callback):
        self.longest_key_callbacks.add(callback)

    def remove_longest_key_listener(self, callback):
        self.longest_key_callbacks.remove(callback)
    
    def _longest_key_listener(self, ignored=None):
        if self.dicts:
            new_longest_key = max(d.longest_key for d in self.dicts)
        else:
            new_longest_key = 0
        if new_longest_key != self.longest_key:
            self.longest_key = new_longest_key
            for c in self.longest_key_callbacks:
                c(new_longest_key)
