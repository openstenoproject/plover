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

from steno_dictionary import StenoDictionary

class Translation(object):
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

    def __init__(self, strokes, rtfcreDict):
        """Create a translation by looking up strokes in a dictionary.

        Arguments:

        strokes -- A list of Stroke objects.

        rtfcreDict -- A dictionary that maps strings in RTF/CRE format
        to English phrases or meta commands.

        """
        self.strokes = strokes
        self.rtfcre = tuple(s.rtfcre for s in strokes)
        self.english = rtfcreDict.get(self.rtfcre, None)
        self.replaced = []
        self.formatting = None

    def __eq__(self, other):
        return self.rtfcre == other.rtfcre

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return 'Translation(%s : %s)' % (self.rtfcre, self.english)

    def __repr__(self):
        return str(self)

    def __len__(self):
        if self.strokes is not None:
            return len(self.strokes)
        return 0

class Translator(object):
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
        self.set_dictionary(StenoDictionary())
        self._listeners = set()
        self._state = _State()

    def translate(self, stroke):
        """Process a single stroke."""
        _translate_stroke(stroke, self._state, self._dictionary, self._output)
        self._resize_translations()

    def set_dictionary(self, d):
        """Set the dictionary."""
        callback = self._dict_callback
        if self._dictionary:
            self._dictionary.remove_longest_key_listener(callback)
        self._dictionary = d
        d.add_longest_key_listener(callback)

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

class _State(object):
    """An object representing the current state of the translator state machine.
    
    Attributes:

    translations -- A list of all previous translations that are still undoable.

    tail -- The oldest translation still saved but is no longer undoable.

    """
    def __init__(self):
        self.translations = []
        self.tail = None

    def last(self):
        """Get the most recent translation."""
        if self.translations:
            return self.translations[-1]
        return self.tail

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

def _translate_stroke(stroke, state, dictionary, callback):
    """Process a stroke.

    See the class documentation for details of how Stroke objects
    are converted to Translation objects.

    Arguments:

    stroke -- The Stroke object to process.

    state -- The state object hold stroke and translation history.

    dictionary -- The steno dictionary.

    callback -- A function that takes the following arguments: A list of
    translations to undo, a list of new translations, and the translation that
    is the context for the new translations.

    """
    
    undo = []
    do = []
    
    if stroke.is_correction:
        if state.translations:
            prev = state.translations[-1]
            undo.append(prev)
            do.extend(prev.replaced)
    else:
        # Figure out how much of the translation buffer can be involved in this
        # stroke and build the stroke list for translation.
        strokes = [stroke]
        translation_count = 0
        for i, t in enumerate(reversed(state.translations)):
            if len(strokes) + len(t) > dictionary.longest_key:
                break
            strokes[:0] = t.strokes
            translation_count += 1
        translation_index = len(state.translations) - translation_count
        
        # The new stroke can either create a new translation or replace
        # existing translations by matching a longer entry in the
        # dictionary.
        for i in xrange(translation_index, len(state.translations)):
            t = Translation(strokes, dictionary)
            if t.english != None:
                t.replaced = state.translations[i:]
                undo.extend(t.replaced)
                do.append(t)
                break
            else:
                del strokes[:len(state.translations[i])]
        else:
            do.append(Translation([stroke], dictionary))
    
    del state.translations[len(state.translations) - len(undo):]
    callback(undo, do, state.last())
    state.translations.extend(do)
