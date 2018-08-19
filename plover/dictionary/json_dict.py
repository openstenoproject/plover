# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Parsing a json formatted dictionary.

"""

import codecs

try:
    import simplejson as json
except ImportError:
    import json

from plover.steno_dictionary import StenoDictionary
from plover.steno import normalize_steno


class JsonDictionary(StenoDictionary):

    def _load(self, filename):
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
        self.update((normalize_steno(x[0]), x[1]) for x in d.items())

    def _save(self, filename):
        with open(filename, 'wb') as fp:
            writer = codecs.getwriter('utf-8')(fp)
            json.dump({'/'.join(k): v for k, v in self.items()},
                      writer, ensure_ascii=False, sort_keys=True,
                      indent=0, separators=(',', ': '))
            writer.write('\n')
