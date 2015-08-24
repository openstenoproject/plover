# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Centralized place for dictionary loading operation."""

import threading
from plover.dictionary.base import load_dictionary
from plover.exception import DictionaryLoaderException

class DictionaryLoadingManager(object):
    def __init__(self):
        self.dictionaries = {}
        
    def start_loading(self, filename):
        if filename in self.dictionaries:
            return self.dictionaries[filename]
        op = DictionaryLoadingOperation(filename)
        self.dictionaries[filename] = op
        return op
        
    def load(self, filenames):
        self.dictionaries = {f: self.start_loading(f) for f in filenames}
        # Result must be in order given so can't just use values().
        ops = [self.dictionaries[f] for f in filenames]
        results = [op.get() for op in ops]
        dicts = []
        for d, e in results:
            if e:
                raise e
            dicts.append(d)
        return dicts
        
        
class DictionaryLoadingOperation(object):
    def __init__(self, filename):
        self.loading_thread = threading.Thread(target=self.load)
        self.filename = filename
        self.exception = None
        self.dictionary = None
        self.loading_thread.start()
        
    def load(self):
        try:
            self.dictionary = load_dictionary(self.filename)
        except DictionaryLoaderException as e:
            self.exception = e
        
    def get(self):
        self.loading_thread.join()
        return self.dictionary, self.exception

manager = DictionaryLoadingManager()
