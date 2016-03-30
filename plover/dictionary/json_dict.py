# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Parsing a json formatted dictionary.

"""

import io

try:
    import simplejson as json
except ImportError:
    import json

from plover.steno_dictionary import StenoDictionary
from plover.steno import normalize_steno


def load_dictionary(filename):

    for encoding in ('utf-8', 'latin-1'):
        try:
            with io.open(filename, 'r', encoding=encoding) as fp:
                d = json.load(fp)
                break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError('\'%s\' encoding could not be determined' % (filename,))

    return StenoDictionary((normalize_steno(x[0]), x[1])
                           for x in dict(d).iteritems())


# TODO: test this
def save_dictionary(d, fp):
    d = dict(('/'.join(k), v) for k, v in d.iteritems())
    json.dump(d, fp, sort_keys=True, indent=0, separators=(',', ': '))
