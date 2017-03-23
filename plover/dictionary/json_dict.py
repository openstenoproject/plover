# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Parsing a json formatted dictionary.

"""

import codecs

try:
    import simplejson as json
except ImportError:
    import json

# Python 2/3 compatibility.
from six import iteritems

from plover.steno_dictionary import StenoDictionary
from plover.steno import normalize_steno


def create_dictionary():
    return StenoDictionary()

def load_dictionary(filename):
    with open(filename, 'rb') as fp:
        contents = fp.read()
    for encoding in ('utf-8', 'latin-1'):
        try:
            contents = contents.decode(encoding)
        except UnicodeDecodeError:
            continue
        else:
            break
    else:
        raise ValueError('\'%s\' encoding could not be determined' % (filename,))
    d = dict(json.loads(contents))
    return StenoDictionary((normalize_steno(x[0]), x[1]) for x in iteritems(d))

def save_dictionary(d, fp):
    contents = json.dumps(dict(('/'.join(k), v) for k, v in iteritems(d)),
                          ensure_ascii=False, sort_keys=True,
                          indent=0, separators=(',', ': '))
    fp.write(contents.encode('utf-8'))
