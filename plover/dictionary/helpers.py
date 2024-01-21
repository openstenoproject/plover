from plover import _, log
from plover.misc import shorten_path
from plover.steno import normalize_steno


class StenoNormalizer:

    def __init__(self, dictionary_path):
        self._dictionary_path = dictionary_path
        self._errors_count = 0

    def normalize(self, steno):
        try:
            return normalize_steno(steno)
        except ValueError:
            self._errors_count += 1
            return tuple(steno.split('/'))

    def __enter__(self):
        return self.normalize

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None and self._errors_count:
            log.warning(_('dictionary `%s` loaded with %u invalid steno errors'),
                        shorten_path(self._dictionary_path), self._errors_count)
