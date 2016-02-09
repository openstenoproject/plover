# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

# TODO: maybe move this code into the StenoDictionary itself. The current saver 
# structure is odd and awkward.
# TODO: write tests for this file

"""Common elements to all dictionary formats."""

from os.path import splitext
import shutil
import threading

from plover.dictionary import json_dict, rtfcre_dict, python_dict
from plover.config import JSON_EXTENSION, RTF_EXTENSION, PYTHON_EXTENSION
from plover.exception import DictionaryLoaderException

dictionaries = {
    JSON_EXTENSION.lower(): json_dict,
    RTF_EXTENSION.lower(): rtfcre_dict,
    PYTHON_EXTENSION.lower(): python_dict,
}

def load_dictionary(filename):
    """Load a dictionary from a file."""

    if filename.startswith('plugins:'):
        dict_type = python_dict
    else:
        extension = splitext(filename)[1].lower()
        try:
            dict_type = dictionaries[extension]
        except KeyError:
            raise DictionaryLoaderException(
                'Unsupported extension for dictionary: %s. Supported extensions: %s' %
                (extension, ', '.join(dictionaries.keys())))

    try:
        d = dict_type.load_dictionary(filename)
    except IOError as e:
        raise DictionaryLoaderException(unicode(e))

    d.set_path(filename)
    d.save = ThreadedSaver(d, filename, dict_type.save_dictionary)
    return d

def save_dictionary(d, filename, saver):
    # Write the new file to a temp location.
    tmp = filename + '.tmp'
    with open(tmp, 'wb') as fp:
        saver(d, fp)

    # Then move the new file to the final location.
    shutil.move(tmp, filename)
    
class ThreadedSaver(object):
    """A callable that saves a dictionary in the background.
    
    Also makes sure that there is only one active call at a time.
    """
    def __init__(self, d, filename, saver):
        self.d = d
        self.filename = filename
        self.saver = saver
        self.lock = threading.Lock()
        
    def __call__(self):
        t = threading.Thread(target=self.save)
        t.start()
        
    def save(self):
        with self.lock:
            save_dictionary(self.d, self.filename, self.saver)
