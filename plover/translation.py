# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Stenography translation.

This module handles translating streams of strokes in translations. Two classes
compose this module:

Translation -- A data model class that encapsulates a sequence of Stroke objects
in the context of a particular dictionary. The dictionary in question maps
stroke sequences to strings, which are typically words or phrases, but could
also be meta commands.

Translator -- A state machine that takes in a single Stroke object at a time and
emits one or more Translation objects based on a greedy conversion algorithm.

"""

from collections import namedtuple
import re

from plover.steno import Stroke
from plover.steno_dictionary import StenoDictionaryCollection
from plover.registry import registry
from plover import system


PREFIX_STROKE = Stroke(())

_ESCAPE_RX = re.compile('(\\\\[nrt]|[\n\r\t])')
_ESCAPE_REPLACEMENTS = {
    '\n': r'\n',
    '\r': r'\r',
    '\t': r'\t',
    r'\n': r'\\n',
    r'\r': r'\\r',
    r'\t': r'\\t',
}

def escape_translation(translation):
    return _ESCAPE_RX.sub(lambda m: _ESCAPE_REPLACEMENTS[m.group(0)], translation)

_UNESCAPE_RX = re.compile(r'((?<!\\)|\\)\\([nrt])')
_UNESCAPE_REPLACEMENTS = {
    r'\\n': r'\n',
    r'\\r': r'\r',
    r'\\t': r'\t',
    r'\n' : '\n',
    r'\r' : '\r',
    r'\t' : '\t',
}

def unescape_translation(translation):
    return _UNESCAPE_RX.sub(lambda m: _UNESCAPE_REPLACEMENTS[m.group(0)], translation)


_LEGACY_MACROS_ALIASES = {
    '{*}': 'retrospective_toggle_asterisk',
    '{*!}': 'retrospective_delete_space',
    '{*?}': 'retrospective_insert_space',
    '{*+}': 'repeat_last_stroke',
}

_MACRO_RX = re.compile(r'=\w+(:|$)')

Macro = namedtuple('Macro', 'name stroke cmdline')

def _mapping_to_macro(mapping, stroke):
    '''Return a macro/stroke if mapping is one, or None otherwise.'''
    macro, cmdline = None, ''
    if mapping is None:
        if stroke.is_correction:
            macro = 'undo'
    else:
        if mapping in _LEGACY_MACROS_ALIASES:
            macro = _LEGACY_MACROS_ALIASES[mapping]
        elif _MACRO_RX.match(mapping):
            args = mapping[1:].split(':', 1)
            macro = args[0]
            if len(args) == 2:
                cmdline = args[1]
    return Macro(macro, stroke, cmdline) if macro else None


class Translation:
    """A data model for the mapping between a sequence of Strokes and a string.

    This class represents the mapping between a sequence of Stroke objects and
    a text string, typically a word or phrase. This class is used as the output
    from translation and the input to formatting. The class contains the 
    following attributes:

    strokes -- A sequence of Stroke objects from which the translation is
    derived.

    rtfcre -- A tuple of RTFCRE strings representing the stroke list. This is
    used as the key in the translation mapping.

    english -- The value of the dictionary mapping given the rtfcre
    key, or None if no mapping exists.

    replaced -- A list of translations that were replaced by this one. If this
    translation is undone then it is replaced by these.

    formatting -- Information stored on the translation by the formatter for
    sticky state (e.g. capitalize next stroke) and to hold undo info.

    """

    def __init__(self, outline, translation):
        """Create a translation by looking up strokes in a dictionary.

        Arguments:

        outline -- A list of Stroke objects.

        translation -- A translation for the outline or None.

        """
        self.strokes = outline
        self.rtfcre = tuple(s.rtfcre for s in outline)
        self.english = translation
        self.replaced = []
        self.formatting = []
        self.is_retrospective_command = False

    def __eq__(self, other):
        return self.rtfcre == other.rtfcre and self.english == other.english

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        if self.english is None:
            translation = 'None'
        else:
            translation = escape_translation(self.english)
            translation = '"%s"' % translation.replace('"', r'\"')
        return 'Translation(%s : %s)' % (self.rtfcre, translation)

    def __repr__(self):
        return str(self)

    def __len__(self):
        if self.strokes is not None:
            return len(self.strokes)
        return 0

    def has_undo(self):
        # If there is no formatting then we're not dealing with a formatter
        # so all translations can be undone.
        # TODO: combos are not undoable but in some contexts they appear
        # as text. Should we provide a way to undo those? or is backspace
        # enough?
        if not self.formatting:
            return True
        if self.replaced:
            return True
        for a in self.formatting:
            if a.text or a.prev_replace:
                return True
        return False


class Translator:
    """Converts a stenotype key stream to a translation stream.

    An instance of this class serves as a state machine for processing key
    presses as they come off a stenotype machine. Key presses arrive in batches,
    each batch representing a single stenotype chord. The Translator class
    receives each chord as a Stroke and adds the Stroke to an internal,
    length-limited FIFO, which is then translated into a sequence of Translation
    objects. The resulting sequence of Translations is compared to those
    previously emitted by the state machine and a sequence of new Translations
    (some corrections and some new) is emitted.

    The internal Stroke FIFO is translated in a greedy fashion; the Translator
    finds a translation for the longest sequence of Strokes that starts with the
    oldest Stroke in the FIFO before moving on to newer Strokes that haven't yet
    been translated. In practical terms, this means that corrections are needed
    for cases in which a Translation comprises two or more Strokes, at least the
    first of which is a valid Translation in and of itself.

    For example, consider the case in which the first Stroke can be translated
    as 'cat'. In this case, a Translation object representing 'cat' will be
    emitted as soon as the Stroke is processed by the Translator. If the next
    Stroke is such that combined with the first they form 'catalogue', then the
    Translator will first issue a correction for the initial 'cat' Translation
    and then issue a new Translation for 'catalogue'.

    A Translator takes input via the translate method and provides translation
    output to every function that has registered via the add_callback method.

    """
    def __init__(self):
        self._undo_length = 0
        self._dictionary = None
        self.set_dictionary(StenoDictionaryCollection())
        self._listeners = set()
        self._state = _State()
        self._to_undo = []
        self._to_do = 0

    def translate(self, stroke):
        """Process a single stroke."""
        self.translate_stroke(stroke)
        self.flush()

    def set_dictionary(self, d):
        """Set the dictionary."""
        callback = self._dict_callback
        if self._dictionary:
            self._dictionary.remove_longest_key_listener(callback)
        self._dictionary = d
        d.add_longest_key_listener(callback)

    def get_dictionary(self):
        return self._dictionary

    def add_listener(self, callback):
        """Add a listener for translation outputs.

        Arguments:

        callback -- A function that takes: a list of translations to undo, a
        list of new translations to render, and a translation that is the
        context for the new translations.

        """
        self._listeners.add(callback)

    def remove_listener(self, callback):
        """Remove a listener added by add_listener."""
        self._listeners.remove(callback)

    def set_min_undo_length(self, n):
        """Set the minimum number of strokes that can be undone.

        The actual number may be larger depending on the translations in the
        dictionary.

        """
        self._undo_length = n
        self._resize_translations()

    def flush(self, extra_translations=None):
        '''Process translations scheduled for undoing/doing.

        Arguments:

        extra_translations --  Extra translations to add to the list
                               of translation to do. Note: those will
                               not be saved to the state history.
        '''
        if self._to_do:
            prev = self._state.prev(self._to_do)
            do = self._state.translations[-self._to_do:]
        else:
            prev = self._state.prev()
            do = []
        if extra_translations is not None:
            do.extend(extra_translations)
        undo = self._to_undo
        self._to_undo = []
        self._to_do = 0
        if undo or do:
            self._output(undo, do, prev)
        self._resize_translations()

    def _output(self, undo, do, prev):
        for callback in self._listeners:
            callback(undo, do, prev)

    def _resize_translations(self):
        self._state.restrict_size(max(self._dictionary.longest_key,
                                      self._undo_length))

    def _dict_callback(self, value):
        self._resize_translations()

    def get_state(self):
        """Get the state of the translator."""
        return self._state

    def set_state(self, state):
        """Set the state of the translator."""
        self._state = state

    def clear_state(self):
        """Reset the sate of the translator."""
        self._state = _State()

    def translate_stroke(self, stroke):
        """Process a stroke.

        See the class documentation for details of how Stroke objects
        are converted to Translation objects.

        Arguments:

        stroke -- The Stroke object to process.

        """
        mapping = self._lookup_with_prefix(self._state.translations, [stroke])
        macro = _mapping_to_macro(mapping, stroke)
        if macro is not None:
            self.translate_macro(macro)
            return
        t = (
            self._find_translation_helper(stroke) or
            self._find_translation_helper(stroke, system.SUFFIX_KEYS) or
            Translation([stroke], mapping)
        )
        self.translate_translation(t)

    def translate_macro(self, macro):
        macro_fn = registry.get_plugin('macro', macro.name).obj
        macro_fn(self, macro.stroke, macro.cmdline)

    def translate_translation(self, t):
        self._undo(*t.replaced)
        self._do(t)

    def untranslate_translation(self, t):
        self._undo(t)
        self._do(*t.replaced)

    def _undo(self, *translations):
        for t in reversed(translations):
            assert t == self._state.translations.pop()
            if self._to_do:
                self._to_do -= 1
            else:
                self._to_undo.insert(0, t)

    def _do(self, *translations):
        self._state.translations.extend(translations)
        self._to_do += len(translations)

    def _find_translation_helper(self, stroke, suffixes=()):
        # Figure out how much of the translation buffer can be involved in this
        # stroke and build the stroke list for translation.
        num_strokes = 1
        translation_count = 0
        for t in reversed(self._state.translations):
            num_strokes += len(t)
            if num_strokes > self._dictionary.longest_key:
                break
            translation_count += 1
        translation_index = len(self._state.translations) - translation_count
        translations = self._state.translations[translation_index:]
        # The new stroke can either create a new translation or replace
        # existing translations by matching a longer entry in the
        # dictionary.
        for i in range(len(translations)+1):
            replaced = translations[i:]
            strokes = [s for t in replaced for s in t.strokes]
            strokes.append(stroke)
            mapping = self._lookup_with_prefix(translations[:i], strokes, suffixes)
            if mapping is not None:
                t = Translation(strokes, mapping)
                t.replaced = replaced
                return t

    def lookup(self, strokes, suffixes=()):
        dict_key = tuple(s.rtfcre for s in strokes)
        result = self._dictionary.lookup(dict_key)
        if result is not None:
            return result
        for key in suffixes:
            if key in strokes[-1].steno_keys:
                dict_key = (Stroke([key]).rtfcre,)
                suffix_mapping = self._dictionary.lookup(dict_key)
                if suffix_mapping is None:
                    continue
                keys = strokes[-1].steno_keys[:]
                keys.remove(key)
                copy = strokes[:]
                copy[-1] = Stroke(keys)
                dict_key = tuple(s.rtfcre for s in copy)
                main_mapping = self._dictionary.lookup(dict_key)
                if main_mapping is None:
                    continue
                return main_mapping + ' ' + suffix_mapping
        return None

    def _previous_word_is_finished(self, last_translations):
        if not last_translations:
            return True
        formatting = last_translations[-1].formatting
        if not formatting:
            return True
        return formatting[-1].word_is_finished

    def _lookup_with_prefix(self, last_translations, strokes, suffixes=()):
        if self._previous_word_is_finished(last_translations):
            mapping = self.lookup([PREFIX_STROKE] + strokes, suffixes)
            if mapping is not None:
                return mapping
        return self.lookup(strokes, suffixes)


class _State:
    """An object representing the current state of the translator state machine.

    Attributes:

    translations -- A list of all previous translations that are still undoable.

    tail -- The oldest translation still saved but is no longer undoable.

    """
    def __init__(self):
        self.translations = []
        self.tail = None

    def prev(self, count=None):
        """Get the most recent translations."""
        if count is not None:
            prev = self.translations[:-count]
        else:
            prev = self.translations
        if prev:
            return prev
        if self.tail is not None:
            return [self.tail]
        return None

    def restrict_size(self, n):
        """Reduce the history of translations to n."""
        stroke_count = 0
        translation_count = 0
        for t in reversed(self.translations):
            stroke_count += len(t)
            translation_count += 1
            if stroke_count >= n:
                break
        translation_index = len(self.translations) - translation_count
        if translation_index:
            self.tail = self.translations[translation_index - 1]
        del self.translations[:translation_index]
