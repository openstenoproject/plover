# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Parsing a json formatted dictionary.

"""

from plover.steno_dictionary import StenoDictionary
from plover.steno import normalize_steno
from plover.exception import DictionaryLoaderException

try:
    import simplejson as json
except ImportError:
    import json
    

def load_dictionary(fp):
    """Load a json dictionary from a string."""

    def h(pairs):
        return StenoDictionary((normalize_steno(x[0]), x[1]) for x in pairs)

    data = fp.read()
    try:
        try:
            return json.loads(data, object_pairs_hook=h)
        except UnicodeDecodeError:
            return json.loads(data, 'latin-1', object_pairs_hook=h)
    except ValueError as e:
        raise DictionaryLoaderException('\'%s\' is not valid json: %s' % (fp.name, str(e)))
        
# TODO: test this
def save_dictionary(d, fp):
    d = dict(('/'.join(k), v) for k, v in d.iteritems())
    json.dump(d, fp, sort_keys=True, indent=0, separators=(',', ': '))
