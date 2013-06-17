# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Parsing a json formatted dictionary.

"""

from plover.steno_dictionary import StenoDictionary
from plover.steno import normalize_steno

try:
    import simplejson as json
except ImportError:
    import json
    

def load_dictionary(data):
    """Load a json dictionary from a string."""

    def h(pairs):
        return StenoDictionary((normalize_steno(x[0]), x[1]) for x in pairs)

    try:
        return json.loads(data, object_pairs_hook=h)
    except UnicodeDecodeError:
        return json.loads(data, 'latin-1', object_pairs_hook=h)
