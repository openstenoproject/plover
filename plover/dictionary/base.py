# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Common elements to all dictionary formats."""

from os.path import join, splitext

from plover.dictionary.json_dict import load_dictionary as json_loader
from plover.dictionary.rtfcre_dict import load_dictionary as rtfcre_loader
from plover.config import JSON_EXTENSION, RTF_EXTENSION, CONFIG_DIR
from plover.exception import DictionaryLoaderException

loaders = {
    JSON_EXTENSION.lower(): json_loader,
    RTF_EXTENSION.lower(): rtfcre_loader,
}


def load_dictionary(filename):
    """Load a dictionary from a file."""
    # The dictionary path can be either absolute or relative to the 
    # configuration directory.
    path = join(CONFIG_DIR, filename)
    extension = splitext(path)[1].lower()
    
    try:
        loader = loaders[extension]
    except KeyError:
        raise DictionaryLoaderException(
            'Unsupported extension %s. Supported extensions: %s', 
            (extension, ', '.join(loaders.keys())))

    try:
        with open(path, 'rb') as f:
            return loader(f.read())
    except IOError as e:
        raise DictionaryLoaderException(unicode(e))
