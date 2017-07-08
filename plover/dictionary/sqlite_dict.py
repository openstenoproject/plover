# Copyright (c) 2017 Thomas Thurman
# See LICENSE.txt for details.

"""
A sqlite3-backed dictionary.

This is intended for use as a cache.
"""

import codecs
import sqlite3

from plover.steno_dictionary import StenoDictionary
from plover.steno import normalize_steno
from plover.resource import ASSET_SCHEME, resource_filename, resource_timestamp

SQLITE_DICTIONARY_FORMAT_VERSION = '0.1'

# we don't descend from StenoDictionary because
# we don't need to use any of its code, and
# we don't want to include any by mistake.
# We act as a subclass by duck typing.
class SqliteDictionary(object):

    def __init__(self):
        self._longest_key_length = None
        self._conn = None

    @classmethod
    def create(cls, resource):
        assert not resource.startswith(ASSET_SCHEME)
        d = cls()
        d.path = resource
        d._prepare_new()
        return d

    def _prepare_new(self):
        filename = resource_filename(self.path)
        self._conn = sqlite3.connect(filename)

        # TODO check that it doesn't already exist
        # (What do we do if it does? Same as json_dict etc, I suppose)

        # XXX actually, maybe we should just take a filename
        # as an optional param to init(), and create or load
        # as appropriate

        c = self._conn.cursor()

        c.execute("CREATE TABLE metadata (field text, value text)")

        c.execute("CREATE TABLE translations (stroke text, translation text)")

        self._set_metadata(c, "version",
                SQLITE_DICTIONARY_FORMAT_VERSION)
        c.commit()

    def _set_metadata(self, cursor, field, value):
        cursor.execute("INSERT INTO metadata VALUES(?, ?)",
                field,
                value)

    def _load(self, filename):
        raise NotImplementedError()

    def _save(self, filename):
        # no-op. These dictionaries are updated as we go along.
        pass
    
    def _save(self, filename):
        # no-op. These dictionaries are updated as we go along.
        pass

### TODO also implement....

   def __str__(self):
        raise NotImplementedError()
        return '%s(%r)' % (self.__class__.__name__, self.path)

    def __repr__(self):
        return str(self)

    @property
    def longest_key(self):
        if self._longest_key_length is not None:
            return self._longest_key_length
        else:
            raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()
        return self._dict.__len__()

    def __iter__(self):
        raise NotImplementedError()
        return self._dict.__iter__()

    def __getitem__(self, key):
        raise NotImplementedError()
        return self._dict.__getitem__(key)

    def clear(self):
        raise NotImplementedError()

    def items(self):
        raise NotImplementedError()
        return self._dict.items()

    def update(self, *args, **kwargs):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def get(self, key, fallback=None):
        raise NotImplementedError()

    def __delitem__(self, key):
        raise NotImplementedError()

    def __contains__(self, key):
        raise NotImplementedError()

    def reverse_lookup(self, value):
        raise NotImplementedError()

    def casereverse_lookup(self, value):
        raise NotImplementedError()

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
