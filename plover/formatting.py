# Copyright (c) 2010-2011 Joshua Harlan Lifton.
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
META_COMMAND = 'PLOVER:'

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
    
    def __init__(self, 
                 translator, 
                 text_output=None, 
                 engine_command_callback=None):
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
        self.engine_command_callback = engine_command_callback
        self.keystrokes = ''
        self.key_combos = []
        self.translator.add_callback(self.consume_translation)

    def consume_translation(self, translation, overflow):
        """Process a Translation object.

        Arguments:

        translation -- A Translation object to be converted to text.

        overflow -- None, or a Translation object that is no longer
        being kept track of due to space limitations.

        """
        cmd = self._get_engine_command(translation)
        if cmd: 
            if self.engine_command_callback:
                self.engine_command_callback(cmd)
            return

        num_backspaces = 0
        non_backspaces = ''
        if overflow:
            tBuffer = [overflow] + self.translator.translations
        else:
            tBuffer = self.translator.translations
        new_keystrokes, new_key_combos = self._translations_to_string(tBuffer)
        old_length = len(self.keystrokes)
        new_length = len(new_keystrokes)
        
        # XXX: There is some code duplication here with
        # TranslationBuffer.consume_stroke. Might be worth
        # generalizing and consolidating.
        
        # Compare old keystrokes to new keystrokes and reconcile them
        # by emitting zero or more backspaces and zero or more
        # keystrokes.
        for i in range(min(old_length, new_length)):
            if self.keystrokes[i] != new_keystrokes[i]:
                num_backspaces += old_length - i
                non_backspaces = new_keystrokes[i:]
                break
        else:
            # The old keystrokes and new keystrokes don't differ except
            # for one is the same as the other with additional keystrokes
            # appended.  As such, keystrokes must be removed or added,
            # depending on which string is longer.
            if old_length > new_length:
                num_backspaces += old_length - new_length
            else:
                non_backspaces = new_keystrokes[old_length:]

        # Don't send key combinations again if they've already been
        # sent.
        skip_count = new_length - len(non_backspaces)
        while new_key_combos and self.key_combos:
            if new_key_combos[0] == self.key_combos[0]:
                skip_count += 1
                new_key_combos.pop(0)
                self.key_combos.pop(0)
            else:
                break
            
        # Output any corrective backspaces and new characters or key
        # combinations.
        if self.text_output:
            self.text_output.send_backspaces(num_backspaces)
            prev_i = 0
            for i, combo in new_key_combos:
                i -= skip_count
                skip_count += 1
                self.text_output.send_string(non_backspaces[prev_i:i])
                self.text_output.send_key_combination(combo)
                prev_i = i
            self.text_output.send_string(non_backspaces[prev_i:])

        # Keep track of the current state in preparation for the next
        # call to this method.
        self.keystrokes, self.key_combos = self._translations_to_string( \
                                                  self.translator.translations)

    def _translations_to_string(self, translations):
        """ Converts a list of Translation objects into printable text.

        Argument:

        translations -- A list of Translation objects.

        Returns a two-tuple, the first element of which is a printable
        string and the second element of which is a list of index, key
        combination pairs. Each key combination should be invoked
        after the sum of the number of emulated characters of the
        printable string and the number of emulated key combinations
        is equal to index.

        """
        text_length = 0
        text = []
        key_combinations = []
        previous_atom = None
        for translation in translations:
            
            if self._get_engine_command(translation):
                continue
            # Reduce the translation to atoms. An atom is in
            # irreducible string that is either entirely a single meta
            # command or entirely text containing no meta commands.
            if translation.english is not None:
                to_atomize = translation.english
                if to_atomize.isdigit():
                    to_atomize = self._apply_glue(to_atomize)
                atoms = META_RE.findall(to_atomize)
            else:
                to_atomize = translation.rtfcre
                if to_atomize.isdigit():
                    to_atomize = self._apply_glue(to_atomize)
                atoms = [to_atomize]
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
                    old_text = ''
                    if meta == META_ED_SUFFIX:
                        if text:
                            old_text = text.pop()
                            english = orthography.add_ed_suffix(old_text)
                    elif meta == META_ER_SUFFIX:
                        if text:
                            old_text = text.pop()
                            english = orthography.add_er_suffix(old_text)
                    elif meta == META_ING_SUFFIX:
                        if text:
                            old_text = text.pop()
                            english = orthography.add_ing_suffix(old_text)
                    elif meta in META_COMMAS or meta in META_STOPS:
                        pass  # Space is already deleted.
                    elif meta == META_PLURALIZE:
                        if text:
                            old_text = text.pop()
                            english = orthography.pluralize_with_s(old_text)
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
                        combo = meta[1:]
                        key_combinations.append((text_length, combo))
                        text_length += 1
                    text_length -= len(old_text)
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
                    elif previous_meta.startswith(META_KEY_COMBINATION):
                        space = NO_SPACE

                new_text = space + english
                text_length += len(new_text)
                text.append(new_text)
                previous_atom = atom

        return (''.join(text), key_combinations)

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

    def _get_engine_command(self, translation):
        # Return the steno engine command, if any, represented by the
        # given translation.
        cmd = translation.english
        if (cmd and 
            cmd.startswith(META_START + META_COMMAND) and
            cmd.endswith(META_END)):
            return cmd[len(META_COMMAND) + 1:-1]
        return None

    def _apply_glue(self, s):
        # Mark the given string as a glue stroke.
        return META_START + META_GLUE_FLAG + s + META_END
