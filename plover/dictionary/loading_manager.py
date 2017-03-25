# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Centralized place for dictionary loading operation."""

import sys
import threading

# Python 2/3 compatibility.
from six import reraise

from plover.dictionary.base import load_dictionary
from plover.exception import DictionaryLoaderException
from plover import log


class DictionaryLoadingManager(object):

    def __init__(self):
        self.dictionaries = {}

    def start_loading(self, filename):
        op = self.dictionaries.get(filename)
        if op is not None:
            return self.dictionaries[filename]
        log.debug('loading dictionary: %s', filename)
        op = DictionaryLoadingOperation(filename)
        self.dictionaries[filename] = op
        return op

    def load(self, filenames):
        self.dictionaries = {f: self.start_loading(f) for f in filenames}
        return [
            self.dictionaries[f].get()
            for f in filenames
        ]


class DictionaryLoadingOperation(object):

    def __init__(self, filename):
        self.loading_thread = threading.Thread(target=self.load)
        self.filename = filename
        self.result = None
        self.loading_thread.start()

    def load(self):
        try:
            self.result = load_dictionary(self.filename)
        except Exception as e:
            log.debug('loading dictionary %s failed', self.filename, exc_info=True)
            self.result = DictionaryLoaderException(self.filename, e)

    def get(self):
        self.loading_thread.join()
        return self.result
