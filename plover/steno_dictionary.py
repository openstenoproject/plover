# Copyright (c) 2013 Hesky Fisher.
# See LICENSE.txt for details.

""" StenoDictionary class and related functions.
    A steno dictionary maps sequences of steno strokes to translations. """

import os
import shutil

from plover.dictionary.base import ReverseStenoDict
from plover.resource import ASSET_SCHEME, resource_filename, resource_timestamp


class StenoDictionary(dict):
    """ A steno dictionary.

    This dictionary maps immutable sequences to translations and tracks the
    length of the longest key. It also keeps a reverse mapping of translations
    back to sequences and allows searching from it.

    Attributes:
    longest_key -- A read only property holding the length of the longest key.
    timestamp -- File last modification time, used to detect external changes.
    readonly -- Is an attribute of the class and of instances.
        class: If True, new instances of the class may not be created through the create() method.
        instances: If True, the dictionary may not be modified, nor may it be written to the path on disk.
    enabled -- If True, dictionary is included in lookups by a StenoDictionaryCollection
    path -- File path where dictionary contents are stored on disk

    """

    # False if class supports creation.
    readonly = False

    def __init__(self):
        super().__init__()
        self._longest_key_length = 0
        self._longest_listener_callbacks = set()
        # Reverse dictionary matches translations to keys by exact match or by "similarity" if required.
        self.reverse = ReverseStenoDict()
        self.timestamp = 0
        self.readonly = False
        self.enabled = True
        self.path = None
        # The special search methods are simple pass-throughs to the reverse dictionary
        self.similar_reverse_lookup = self.reverse.get_similar_keys
        self.partial_reverse_lookup = self.reverse.partial_match_values
        self.regex_reverse_lookup = self.reverse.regex_match_values

    def __str__(self):
        return '%s(%r)' % (self.__class__.__name__, self.path)

    def __repr__(self):
        return str(self)

    @classmethod
    def create(cls, resource):
        assert not resource.startswith(ASSET_SCHEME)
        if cls.readonly:
            raise ValueError('%s does not support creation' % cls.__name__)
        d = cls()
        d.path = resource
        return d

    @classmethod
    def load(cls, resource):
        filename = resource_filename(resource)
        timestamp = resource_timestamp(filename)
        d = cls()
        d._load(filename)
        if resource.startswith(ASSET_SCHEME) or \
           not os.access(filename, os.W_OK):
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

    # Actual methods to load and save dictionary contents to files must be implemented by format-specific subclasses.
    def _load(self, filename):
        raise NotImplementedError()

    def _save(self, filename):
        raise NotImplementedError()

    def clear(self):
        """ Empty the dictionary without altering its file-based attributes. """
        super().clear()
        self.reverse.clear()
        self._longest_key = 0

    def __setitem__(self, key, value):
        assert not self.readonly
        # Be careful here. If the key already exists, we have to remove its old mapping from the reverse dictionary
        # while we can still find it. And if it's a new key, it could possibly be the new longest one.
        if key in self:
            self.reverse.remove_key(self[key], key)
        else:
            self._longest_key = max(self._longest_key, len(key))
        super().__setitem__(key, value)
        self.reverse.append_key(value, key)

    def __delitem__(self, key):
        assert not self.readonly
        value = super().pop(key)
        self.reverse.remove_key(value, key)
        # If the key deleted was the longest, we have no idea what the new longest is, so we must recalculate it.
        if len(key) == self.longest_key:
            self._calculate_longest_key()

    def update(self, *args, **kwargs):
        """ Update the dictionary using a single iterable sequence of (key, value) tuples or a single mapping
            located in args. kwargs is irrelevant since only strings can be keywords, but is included for
            method signature compatibility with dict. """
        assert not self.readonly
        if not self:
            # Fast path for when the dicts start out empty.
            super().update(*args, **kwargs)
            self.reverse.match_forward(self)
            self._calculate_longest_key()
        else:
            # If items already exist, update dicts one item at a time to be safe.
            for (k, v) in dict(*args, **kwargs).items():
                self[k] = v

    def reverse_lookup(self, value):
        """
        Return a list of keys that can exactly produce the given value.
        If there aren't any keys that produce this value, just return an empty list.
        """
        return self.reverse[value] if value in self.reverse else []

    def casereverse_lookup(self, value):
        """ Return a list of translations case-insensitive equal to the given value. For backwards compatibility. """
        return [v for v in self.similar_reverse_lookup(value) if value.lower() == v.lower()]

    @property
    def longest_key(self):
        """ Public read-only property returning the length of the longest key in the dict.
            It simply accesses the private version of the property and returns it. """
        return self._longest_key

    @property
    def _longest_key(self):
        """ Private property returning the internal value of the longest key length. It is readable and writable. """
        return self._longest_key_length

    @_longest_key.setter
    def _longest_key(self, longest_key):
        """ Set the private longest key length property, possibly triggering callbacks if it changed. """
        if longest_key == self._longest_key_length:
            return
        self._longest_key_length = longest_key
        for callback in self._longest_listener_callbacks:
            callback(longest_key)

    def _calculate_longest_key(self):
        """ Calculate and record the longest key in the dictionary by manually comparing all the keys. """
        self._longest_key = max(map(len, self), default=0)

    def add_longest_key_listener(self, callback):
        self._longest_listener_callbacks.add(callback)

    def remove_longest_key_listener(self, callback):
        self._longest_listener_callbacks.remove(callback)

    # Unimplemented methods from the base class that can mutate the object are unsafe. Make them return errors.
    def _UNSAFE_METHOD(self, *args, **kwargs): return NotImplementedError
    setdefault = pop = popitem = _UNSAFE_METHOD


class StenoDictionaryCollection:

    def __init__(self, dicts=[]):
        self.dicts = []
        self.filters = []
        self.longest_key = 0
        self.longest_key_callbacks = set()
        self.set_dicts(dicts)

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

    def __str__(self):
        return 'StenoDictionaryCollection' + repr(tuple(self.dicts))

    def __repr__(self):
        return str(self)

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
                # Ignore key if it's overridden by a higher priority dictionary.
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

    def first_writable(self):
        '''Return the first writable dictionary.'''
        for d in self.dicts:
            if not d.readonly:
                return d
        raise KeyError('no writable dictionary')

    def set(self, key, value, path=None):
        if path is None:
            d = self.first_writable()
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
