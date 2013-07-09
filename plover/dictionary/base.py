# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

# TODO: maybe move this code into the StenoDictionary itself. The current saver 
# structure is odd and awkward.
# TODO: write tests for this file

"""Common elements to all dictionary formats."""

from os.path import join, splitext
import shutil
import threading

import plover.dictionary.json_dict as json_dict
import plover.dictionary.rtfcre_dict as rtfcre_dict
from plover.config import JSON_EXTENSION, RTF_EXTENSION, CONFIG_DIR
from plover.exception import DictionaryLoaderException

dictionaries = {
    JSON_EXTENSION.lower(): json_dict,
    RTF_EXTENSION.lower(): rtfcre_dict,
}

def load_dictionary(filename):
    """Load a dictionary from a file."""
    # The dictionary path can be either absolute or relative to the 
    # configuration directory.
    path = join(CONFIG_DIR, filename)
    extension = splitext(path)[1].lower()
    
    try:
        dict_type = dictionaries[extension]
    except KeyError:
        raise DictionaryLoaderException(
            'Unsupported extension %s. Supported extensions: %s', 
            (extension, ', '.join(loaders.keys())))

    loader = dict_type.load_dictionary

    try:
        with open(path, 'rb') as f:
            d = loader(f.read())
    except IOError as e:
        raise DictionaryLoaderException(unicode(e))
        
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
