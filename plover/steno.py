# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Generic stenography data models and translation engine.

This module is the foundation for manipulating and understanding the
output of a stenotype machine. Three classes copmose this module:

Stroke -- A data model class that encapsulates a sequence of steno
keys, which might be ASCII or raw binary data, in the context of a
particular normalized dictionary format, essentially abstracting away
the details of a particular stenotype machine's formatting.

Translation -- A data model class that encapsulates a sequence of
Stroke objects in the context of a particular dictionary. The
dictionary in question maps stroke sequences to strings, which are
typically English words or phrases, but could also be meta commands.

Translator -- A state machine that takes in a single Stroke object at
a time and emits one or more Translation objects based on a greedy
conversion algorithm.

"""

STENO_KEY_NUMBERS = { 'S-':'1-', 
                      'T-': '2-',
                      'P-': '3-',
                      'H-': '4-',
                      'A-': '5-',
                      'O-': '0-',
                      '-F': '-6',
                      '-P': '-7',
                      '-L': '-8',
                      '-T': '-9'}

STENO_KEY_ORDER = {"#": -1,
                   "S-": 0,
                   "T-": 1,
                   "K-": 2,
                   "P-": 3,
                   "W-": 4,
                   "H-": 5,
                   "R-": 6,
                   "A-": 7,
                   "O-": 8,
                   "*": 9,     # Also 10, 11, and 12 for some machines.
                   "-E": 13,
                   "-U": 14,
                   "-F": 15,
                   "-R": 16,
                   "-P": 17,
                   "-B": 18,
                   "-L": 19,
                   "-G": 20,
                   "-T": 21,
                   "-S": 22,
                   "-D": 23,
                   "-Z": 24}

STENO_KEYS = tuple(STENO_KEY_ORDER.keys())


class Stroke :
    """A standardized data model for stenotype machine strokes.

    This class standardizes the representation of a stenotype chord
    according to a particular dictionary format. A stenotype chord can
    be any sequence of stenotype keys that can be simultaneously
    pressed. Nearly all stenotype machines offer the same set of keys
    that can be combined into a chord, though some variation exists
    due to duplicate keys. This class accounts for such duplication,
    imposes the standard stenographic ordering on the keys, and
    combines the keys into a single string (called RTFCRE for
    historical reasons) according to a particular dictionary format.

    """
        
    def __init__(self, steno_keys, dictionary_format) :
        """Create a steno stroke by formatting steno keys.

        Arguments:

        steno_keys -- A sequence of unordered stenographic keys
        composing this stroke. Valid stenographic keys are given in
        STENO_KEYS.

        dictionary_format -- A Python module that encapsulates a
        specific stenographic dictionary format. Typically, this is
        one of the modules in plover.dictionary, but it could be any
        module that provides a STROKE_DELIMITER constant and a
        toRTFCRE method that takes in a sequence and returns a string.
        
        """

        # Remove duplicate keys and save local versions of the input
        # parameters.
        self.steno_keys = list(set(steno_keys))
        self.dictionary_format = dictionary_format

        # Order the steno keys so comparisons can be made.
        self.steno_keys.sort(key=lambda x: STENO_KEY_ORDER[x])
                
        # Convert strokes involving the number bar to numbers.
        if '#' in self.steno_keys:
            numeral = False
            for i, e in enumerate(self.steno_keys):
                if e in STENO_KEY_NUMBERS:
                    self.steno_keys[i] = STENO_KEY_NUMBERS[e]
                    numeral = True
            if numeral:
                self.steno_keys.remove('#')

        # Convert the list of steno keys to the RTF/CRE format.
        self.rtfcre = self.dictionary_format.toRTFCRE(self.steno_keys)

        # Determine if this stroke is a correction stroke.
        self.is_correction = (self.rtfcre == '*')
            
    def __str__(self):
        if self.is_correction :
            prefix = '*'
        else :
            prefix = ''
        return '%sStroke(%s : %s)' % (prefix, self.rtfcre, self.steno_keys)
    
    def __eq__(self, other):
        return isinstance(other, Stroke) and self.steno_keys==other.steno_keys

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __repr__(self):
        return str(self)


class Translation :
    """A data model for the mapping between a sequence of Strokes and a string.

    This class represents the mapping between a sequence of Stroke
    objects and a text string, typically an English word or
    phrase. This class is used as the output from a Translator
    instance and the input to a Formatter instance. The class contains
    the following attributes:

    strokes -- A list of Stroke objects from which the translation is
    derived.

    rtfcre -- A string representation of the stroke list. This is used
    as the key in the translation mapping.

    english -- The value of the dictionary mapping given the rtfcre
    key, or None if no mapping exists.

    is_correction -- True if this translation is a correction, False
    otherwise.

    """

    def __init__(self, strokes, rtfcreDict):
        """Create a translation by looking up strokes in a dictionary.

        Arguments:

        strokes -- A list of Stroke objects.

        rtfcreDict -- A dictionary that maps strings in RTF/CRE format
        to English phrases or meta commands.

        """
        self.strokes = strokes
        if strokes :
            dict_format = strokes[0].dictionary_format
            delimiter = dict_format.STROKE_DELIMITER
            self.rtfcre = delimiter.join([s.rtfcre for s in strokes])
        else :
            dict_format = None
            self.rtfcre = ''
        self.english = rtfcreDict.get(self.rtfcre, None)
        self.is_correction = False
            
    def __eq__(self, other):
        return self.rtfcre == other.rtfcre

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        if self.is_correction :
            prefix = '*'
        else :
            prefix = ''
        return '%sTranslation(%s : %s)' % (prefix, self.rtfcre, self.english)

    def __repr__(self):
        return str(self)

    def __len__(self):
        if self.strokes is not None:
            return len(self.strokes)
        return 0
    

class Translator :
    """Converts a stenotype key stream to a translation stream.

    An instance of this class serves as a state machine for processing
    key presses as they come off a stenotype machine. Key presses
    arrive in batches, each batch representing a single stenotype
    chord. The Translator class packages each chord as a Stroke and
    adds the Stroke to an internal, length-limited FIFO, which is then
    translated into a sequence of Translation objects. The resulting
    sequence of Translations is compared to those previously emitted
    by the state machine and a sequence of new Translations (some
    corrections and some new) is emitted.

    The internal Stroke FIFO is translated in a greedy fashion; the
    Translator finds a translation for the longest sequence of Strokes
    that starts with the oldest Stroke in the FIFO before moving on to
    newer Strokes that haven't yet been translated. In practical
    terms, this means that corrections are needed for cases in which a
    Translation comprises two or more Strokes, at least the first of
    which is a valid Translation in and of itself.

    For example, consider the case in which the first Stroke can be
    translated as 'cat'. In this case, a Translation object
    representing 'cat' will be emitted as soon as the Stroke is
    processed by the Translator. If the next Stroke is such that
    combined with the first they form 'catalogue', then the Translator
    will first issue a correction for the initial 'cat' Translation
    and then issue a new Translation for 'catalogue'.

    A Translator takes steno key input via the consume_steno_keys
    method and provides translation output to every function that has
    registered via the add_callback method.

    """

    def __init__(self,
                 steno_machine,
                 dictionary,
                 dictionary_format,
                 max_number_of_strokes=None):
        """Prepare to translate steno keys into dictionary string values.

        Arguments:

        steno_machine -- An instance of the Stenotype class from one
        of the submodules of plover.machine. For example,
        plover.machine.geminipr.Stenotype.

        dictionary -- A dictionary that maps strings in RTF/CRE format
        to English or meta command strings.

        dictionary_format -- One of the submodules of
        plover.dictionary. For example, plover.dictionary.eclipse.

        max_number_of_strokes -- The length of the internal Stroke
        FIFO. This should generally be the longest sequence of strokes
        expected to be a valid translation. If None, this value
        defaults to the longest sequence of strokes found in the
        dictionary argument. This value should generally be left
        unchanged from its default of None.

        """
        self.steno_machine = steno_machine
        self.strokes = []
        self.translations = []
        self.overflow = None
        self.dictionary = dictionary
        self.dictionary_format = dictionary_format
        self.subscribers = []
        if max_number_of_strokes is None :
            max_number_of_strokes = 0
            delimiter = dictionary_format.STROKE_DELIMITER
            for rtfcre in dictionary.keys() :
                max_number_of_strokes = max(max_number_of_strokes, 
                                            len(rtfcre.split(delimiter)))
        self.max_number_of_strokes = max_number_of_strokes
        self.steno_machine.add_callback(self.consume_steno_keys)

    def consume_steno_keys(self, steno_keys):
        """Process the raw output from a Stenotype object.

        This is a convenience method that packages the raw output of a
        Stenotype instance into a Stroke object before passing it
        along for further processing.

        Arguments:

        steno_keys -- The raw output from a stenotype machine.

        """
        if steno_keys :
            self.consume_stroke(Stroke(steno_keys, self.dictionary_format))

    def consume_stroke(self, stroke):
        """Process a stenotype chord, emitting translations as needed.

        See the class documentation for details of how Stroke objects
        are converted to Translation objects.

        Arguments:

        stroke -- The Stroke object to process.

        """
        # If stroke buffer is full, discard all strokes of oldest
        # translation to make room for the new stroke.
        if stroke.is_correction and len(self.strokes) > 0:
            self.strokes.pop()
        self.overflow = None
        if len(self.strokes) >= self.max_number_of_strokes:
            self.overflow = self.translations.pop(0)
            for s0 in self.overflow.strokes:
                s1 = self.strokes.pop(0) 
                if s0 != s1:
                    raise(RuntimeError("Steno stroke buffers out of sync."))
        if not stroke.is_correction:
            self.strokes.append(stroke)

        # Convert Strokes to Translations.  Strokes are converted
        # oldest to newest and each Translation is constructed to use
        # as many Strokes as possible. If a Translation with a proper
        # dictionary entry can't be constructed, then a Translation
        # containing only the first Stroke is created.
        new_translations = []
        n = 0 
        while n != len(self.strokes):
            unused = self.strokes[n:]
            for i in range(len(unused),0,-1):
                longest_translation = Translation(unused[:i], self.dictionary)
                if longest_translation.english != None:
                    break
            else:
                longest_translation = Translation(unused[0:1], self.dictionary)
            new_translations.append(longest_translation)
            n += len(longest_translation)

        # Update translation buffer, but keep track of previous state.
        old_translations = self.translations
        self.translations = new_translations

        # Compare old translations to the new translations and
        # reconcile them by emitting one or more tokens, where a token
        # is either a correction or a translation.
        for i in range(min(len(old_translations), len(new_translations))):
            if old_translations[i] != new_translations[i]:
                # Emit corrections for each remaining element in
                # old_translations after the two lists differ.
                for t in old_translations[i:] :
                    t.is_correction = True
                    self._emit_translation(t)
                for t in new_translations[i:] :
                    self._emit_translation(t)
                break
        else:
            # The translation and new translations don't differ except
            # for one is the same as the other with additional
            # translations appended.  As such, translations must be
            # removed or added, depending on which list is longer.
            if len(old_translations) > len(new_translations) :
                for t in old_translations[len(new_translations):] :
                    t.is_correction = True
                    self._emit_translation(t)
            else :
                for t in new_translations[len(old_translations):] :
                    self._emit_translation(t)

    def add_callback(self, callback) :
        """Subscribes a function to receive new trasnlations.

        Arguments:

        callback -- A function that takes two arguments. The first
        argument is a Translation object newly emitted from the
        Translator. The second argument is a Translation object that
        has been removed from the internal FIFO to make room for the
        new Translation, or None if nothing was removed.

        """
        self.subscribers.append(callback)

    def _emit_translation(self, translation):
        # Send a new translation and any dropped translations to all listeners.
        for callback in self.subscribers :
            callback(translation, self.overflow)
        self.overflow = None
