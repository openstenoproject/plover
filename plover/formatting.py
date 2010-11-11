# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""This module converts translations to printable text."""

import re
import orthography

SPACE = ' '
STOP_SPACE = ' '
NO_SPACE = ''
META_STOPS = ('.', '!', '?')
META_COMMAS = (',', ':', ';')
META_ED_SUFFIX = '^ed'
META_ER_SUFFIX = '^er'
META_ING_SUFFIX = '^ing'
META_CAPITALIZE = '-|'
META_PLURALIZE = '^s'
META_GLUE_FLAG = '&'
META_ATTACH_FLAG = '^'
META_KEY_COMBINATION = '#'

META_ESCAPE = '\\'
RE_META_ESCAPE = '\\\\'
META_START = '{'
META_END = '}'
META_ESC_START = META_ESCAPE + META_START
META_ESC_END = META_ESCAPE + META_END

META_RE = re.compile(r"""(?:%s%s|%s%s|[^%s%s])+ # One or more of anything
                                                # other than unescaped { or }
                                                #
                                              | # or
                                                #
                     %s(?:%s%s|%s%s|[^%s%s])*%s # Anything of the form {X}
                                                # where X doesn't contain
                                                # unescaped { or }
                      """ % (RE_META_ESCAPE, META_START, RE_META_ESCAPE,
                             META_END, META_START, META_END,
                             META_START,
                             RE_META_ESCAPE, META_START, RE_META_ESCAPE,
                             META_END, META_START, META_END,
                             META_END),
                     re.VERBOSE)

# A more human-readable version of the above RE is:
#
# re.compile(r"""(?:\\{|\\}|[^{}])+ # One or more of anything other than
#                                   # unescaped { or }
#                                   #
#                                 | # or
#                                   #
#              {(?:\\{|\\}|[^{}])*} # Anything of the form {X} where X
#                                   # doesn't contain unescaped { or }
#             """, re.VERBOSE)

    
class Formatter:
    """A state machine for converting Translation objects into printable text.

    Instances of this class take in one Translation object at a time
    through the consume_translation method and output printable text.

    """
    
    def __init__(self, translator, text_output):
        """Create a state machine for processing Translation objects.

        Arguments:

        translator -- A Translator that outputs Translation objects
        available via an add_callback interface.

        text_output -- Any object that has a send_backspaces method
        that takes an integer as an argument, a send_string method
        that takes a string as an argument, and a send_key_combination
        method that takes a string as an argument.

        """
        self.translator = translator
        self.text_output = text_output
        self.keystrokes = ''
        self.translator.add_callback(self.consume_translation)

    def consume_translation(self, translation, overflow):
        """Process a Translation object.

        Arguments:

        translation -- A Translation object to be converted to text.

        overflow -- None, or a Translation object that is no longer
        being kept track of due to space limitations.

        """
        num_backspaces = 0
        non_backspaces = ''
        if overflow:
            tBuffer = [overflow] + self.translator.translations
        else:
            tBuffer = self.translator.translations
        newKeystrokes = self._translations_to_string(tBuffer)
        
        # XXX: There is some code duplication here with
        # TranslationBuffer.consume_stroke. Might be worth
        # generalizing and consolidating.
        
        # Compare old keystrokes to new keystrokes and reconcile them
        # by emitting zero or more backspaces and zero or more
        # keystrokes.
        for i in range(min(len(self.keystrokes), len(newKeystrokes))):
            if self.keystrokes[i] != newKeystrokes[i]:
                num_backspaces += len(self.keystrokes) - i
                non_backspaces = newKeystrokes[i:]
                break
        else:
            # The old keystrokes and new keystrokes don't differ except
            # for one is the same as the other with additional keystrokes
            # appended.  As such, keystrokes must be removed or added,
            # depending on which string is longer.
            if len(self.keystrokes) > len(newKeystrokes):
                num_backspaces += len(self.keystrokes) - len(newKeystrokes)
            else:
                non_backspaces = newKeystrokes[len(self.keystrokes):]

        # Now that the old and new keystrokes have been reconciled,
        # keep a record of the current state and output the changes.
        self.keystrokes = self._translations_to_string( \
                                                  self.translator.translations)
        self.text_output.send_backspaces(num_backspaces)
        self.text_output.send_string(non_backspaces)

    def _translations_to_string(self, translations):
        """ Converts a list of Translation objects into printable text.

        Argument:

        translations -- A list of Translation objects.

        Returns a printable string.

        """
        text = []
        previous_atom = None
        for translation in translations:
            # Reduce the translation to atoms. An atom is in
            # irreducible string that is either entirely a single meta
            # command or entirely text containing no meta commands.
            if translation.english is not None:
                atoms = META_RE.findall(translation.english)
            else:
                atoms = [translation.rtfcre]
            for atom in atoms:
                atom = atom.strip()
                if text:
                    space = SPACE
                else:
                    space = NO_SPACE
                meta = self._get_meta(atom)
                if meta is not None:
                    meta = self._unescape_atom(meta)
                    english = meta
                    space = NO_SPACE  # Correct for most meta commands.
                    if meta == META_ED_SUFFIX:
                        if text:
                            text[-1] = orthography.add_ed_suffix(text[-1])
                            english = NO_SPACE
                    elif meta == META_ER_SUFFIX:
                        if text:
                            text[-1] = orthography.add_er_suffix(text[-1])
                            english = NO_SPACE
                    elif meta == META_ING_SUFFIX:
                        if text:
                            text[-1] = orthography.add_ing_suffix(text[-1])
                            english = NO_SPACE
                    elif meta in META_COMMAS or meta in META_STOPS:
                        pass  # Space is already deleted.
                    elif meta == META_PLURALIZE:
                        if text:
                            text[-1] = orthography.pluralize_with_s(text[-1])
                            english = NO_SPACE
                    elif meta.startswith(META_GLUE_FLAG):
                        english = meta[1:]
                        previous_meta = self._get_meta(previous_atom)
                        if (previous_meta is None or
                            not previous_meta.startswith(META_GLUE_FLAG)):
                            space = SPACE
                    elif meta.startswith(META_ATTACH_FLAG):
                        english = meta[1:]
                        if english.endswith(META_ATTACH_FLAG):
                            english = english[:-1]
                    elif meta.endswith(META_ATTACH_FLAG):
                        space = SPACE
                        english = meta[:-1]
                    elif meta == META_CAPITALIZE:
                        english = NO_SPACE
                    elif meta.startswith(META_KEY_COMBINATION):
                        english = NO_SPACE
                        key_combination = meta[1:]
                        # XXX : Do something with the key combination.
                else:
                    english = self._unescape_atom(atom)

                # Check if the previous atom is a meta command that
                # influences the next atom, namely this atom.
                previous_meta = self._get_meta(previous_atom)
                if previous_meta is not None:
                    if previous_meta in META_STOPS:
                        space = STOP_SPACE
                        english = english.capitalize()
                    elif previous_meta == META_CAPITALIZE:
                        space = NO_SPACE
                        english = english.capitalize()
                    elif previous_meta.endswith(META_ATTACH_FLAG):
                        space = NO_SPACE

                text.append(space + english)
                previous_atom = atom
                    
        return ''.join(text)

    def _get_meta(self, atom):
        # Return the meta command, if any, without surrounding meta markups. 
        if (atom is not None and
            atom.startswith(META_START) and
            atom.endswith(META_END)):
            return atom[1:-1]
        return None

    def _unescape_atom(self, atom):
        # Replace escaped meta markups with unescaped meta markups.
        return atom.replace(META_ESC_START, META_START).replace(META_ESC_END,
                                                                META_END)

