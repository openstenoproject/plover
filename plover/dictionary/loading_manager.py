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
        dicts = []
        for f in filenames:
            d, exc_info = self.dictionaries[f].get()
            if exc_info is not None:
                reraise(*exc_info)
            dicts.append(d)
        return dicts


class DictionaryLoadingOperation(object):

    def __init__(self, filename):
        self.loading_thread = threading.Thread(target=self.load)
        self.filename = filename
        self.exc_info = None
        self.dictionary = None
        self.loading_thread.start()

    def load(self):
        try:
            self.dictionary = load_dictionary(self.filename)
        except DictionaryLoaderException:
            self.exc_info = sys.exc_info()

    def get(self):
        self.loading_thread.join()
        return self.dictionary, self.exc_info


manager = DictionaryLoadingManager()
