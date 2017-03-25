# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

# TODO: maybe move this code into the StenoDictionary itself. The current saver 
# structure is odd and awkward.
# TODO: write tests for this file

"""Common elements to all dictionary formats."""

from os.path import splitext
import shutil
import sys
import threading

from plover.registry import registry
from plover.resource import ASSET_SCHEME, resource_filename, resource_timestamp


def _get_dictionary_module(filename):
    extension = splitext(filename)[1].lower()[1:]
    try:
        dict_module = registry.get_plugin('dictionary', extension).obj
    except KeyError:
        raise ValueError(
            'Unsupported extension: %s. Supported extensions: %s' %
            (extension, ', '.join(plugin.name for plugin in
                                  registry.list_plugins('dictionary'))))
    return dict_module

def create_dictionary(resource):
    '''Create a new dictionary.

    The format is inferred from the extension.

    Note: the file is not created! The resulting dictionary save
    method must be called to finalize the creation on disk.
    '''
    assert not resource.startswith(ASSET_SCHEME)
    filename = resource_filename(resource)
    dictionary_module = _get_dictionary_module(filename)
    if not hasattr(dictionary_module, 'create_dictionary'):
        raise ValueError('%s does not support creation' % dictionary_module.__name__)
    d = dictionary_module.create_dictionary()
    d.set_path(resource)
    d.save = ThreadedSaver(d, filename, dictionary_module.save_dictionary)
    return d

def load_dictionary(resource):
    '''Load a dictionary from a file.

    The format is inferred from the extension.
    '''
    filename = resource_filename(resource)
    timestamp = resource_timestamp(filename)
    dictionary_module = _get_dictionary_module(filename)
    d = dictionary_module.load_dictionary(filename)
    d.set_path(resource)
    d.timestamp = timestamp
    if not resource.startswith(ASSET_SCHEME) and \
       hasattr(dictionary_module, 'save_dictionary'):
        d.save = ThreadedSaver(d, filename, dictionary_module.save_dictionary)
    return d

def save_dictionary(d, resource, saver):
    assert not resource.startswith(ASSET_SCHEME)
    filename = resource_filename(resource)
    # Write the new file to a temp location.
    tmp = filename + '.tmp'
    with open(tmp, 'wb') as fp:
        saver(d, fp)
    timestamp = resource_timestamp(tmp)
    # Then move the new file to the final location.
    shutil.move(tmp, filename)
    # And update our timestamp.
    d.timestamp = timestamp
    
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
