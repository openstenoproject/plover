# vim: set fileencoding=utf-8 :


from plover.steno_dictionary import StenoDictionary
from plover.exception import DictionaryLoaderException
from plover import plugins


class PythonDictionary(StenoDictionary):

    def __init__(self, maximum_key_length, lookup_translation, reverse_lookup=None):
        super(PythonDictionary, self).__init__()
        self._longest_key_length = maximum_key_length
        self._lookup_translation = lookup_translation
        if reverse_lookup is not None:
            self.reverse_lookup = reverse_lookup

    @property
    def _longest_key(self):
        return self._longest_key_length

    @_longest_key.setter
    def _longest_key(self, longest_key):
        raise NotImplementedError()

    def __len__(self):
        return 0

    def __iter__(self):
        return {}.__iter__()

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def __delitem__(self, key):
        raise NotImplementedError()

    def iterkeys(self):
        return {}.iterkeys()

    def itervalues(self):
        return {}.itervalues()

    def iteritems(self):
        raise {}.iteritems()

    def __contains__(self, key):
        if len(key) > self.longest_key:
            return False
        return True

    def __getitem__(self, key):
        if len(key) > self.longest_key:
            raise KeyError()
        return self._lookup_translation(key)

def load_dictionary(filename):
    if filename.startswith('plugins:'):
        dictionaries = plugins.get_dictionaries()
        mod = dictionaries[filename[8:]].load()
        maximum_key_length = mod.MAXIMUM_KEY_LENGTH
        lookup_translation = mod.lookup_translation
        reverse_lookup = getattr(mod, 'reverse_lookup', None)
    else:
        dict_syms = {}
        try:
            with open(filename, 'rb') as fp:
                exec fp in dict_syms, dict_syms
        except Exception as e:
            raise DictionaryLoaderException('Could not load dictionary: %s\n' % str(e))
        maximum_key_length = dict_syms.get('MAXIMUM_KEY_LENGTH', None)
        if not isinstance(maximum_key_length, int) or maximum_key_length < 0:
            raise DictionaryLoaderException('Invalid dictionary: missing or invalid `MAXIMUM_KEY_LENGTH\' constant: %s\n' % str(maximum_key_length))
        lookup_translation = dict_syms.get('lookup_translation', None)
        if not isinstance(lookup_translation, type(lambda x: x)):
            raise DictionaryLoaderException('Invalid dictionary: missing or invalid `lookup_translation\' function: %s\n' % str(lookup_translation))
        reverse_lookup = dict_syms.get('reverse_lookup', None)
        if reverse_lookup is not None and not isinstance(reverse_lookup, type(lambda x: x)):
            raise DictionaryLoaderException('Invalid dictionary: invalid `reverse_lookup\' function: %s\n' % str(lookup_translation))
    return PythonDictionary(maximum_key_length, lookup_translation, reverse_lookup)

def save_dictionary(d, fp):
    raise NotImplementedError()

