# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""This module converts translations to printable text.

This module defines and implements plover's custom dictionary language.

"""

from os.path import commonprefix
from collections import namedtuple
from plover import orthography
import re
import string


class Formatter(object):
    """Convert translations into output.

    The main entry point for this class is format, which takes in translations
    to format. Output is sent via an output class passed in through set_output.
    Other than setting the output, the formatter class is stateless.

    The output class can define the following functions, which will be called
    if available:

    send_backspaces -- Takes a number and deletes back that many characters.

    send_string -- Takes a string and prints it verbatim.

    send_key_combination -- Takes a string the dictionary format for specifying
    key combinations and issues them.

    send_engine_command -- Takes a string which names the special command to
    execute.

    """

    output_type = namedtuple(
        'output', ['send_backspaces', 'send_string', 'send_key_combination',
                   'send_engine_command'])
    start_capitalized = False
    start_attached = False

    def __init__(self):
        self.set_output(None)
        self.spaces_after = False
        self._listeners = set()

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

    def set_output(self, output):
        """Set the output class."""
        noop = lambda x: None
        output_type = self.output_type
        fields = output_type._fields
        self._output = output_type(*[getattr(output, f, noop) for f in fields])

    def set_space_placement(self, s):
        # Set whether spaces will be inserted
        # before the output or after the output
        self.spaces_after = bool(s == 'After Output')

    def format(self, undo, do, prev):
        """Format the given translations.

        Arguments:

        undo -- A sequence of translations that should be undone. The
        formatting parameter of the translations will be used to undo the
        actions that were taken, if possible.

        do -- The new actions to format. The formatting attribute will be
        filled in with the result.

        prev -- The last translation before the new actions in do. This
        translation's formatting attribute provides the context for the new
        rendered translations. If there is no context then this may be None.

        """
        prev_formatting = prev.formatting if prev else None

        for t in do:
            last_action = self._get_last_action(prev.formatting if prev else None)
            if t.english:
                t.formatting = _translation_to_actions(t.english, last_action,
                                                       self.spaces_after)
            else:
                t.formatting = _raw_to_actions(t.rtfcre[0], last_action,
                                               self.spaces_after)
            prev = t

        old = [a for t in undo for a in t.formatting]
        new = [a for t in do for a in t.formatting]

        for callback in self._listeners:
            callback(old, new)

        OutputHelper(self._output, prev_formatting).render(old, new)

    def _get_last_action(self, actions):
        """Return last action in actions if possible or return a default action."""
        if actions:
            return actions[-1]
        return _Action(attach=self.start_attached, capitalize=self.start_capitalized)


class OutputHelper(object):
    """A helper class for minimizing the amount of change on output.

    This class figures out the current state, compares it to the new output and
    optimizes away extra backspaces and typing.

    """
    def __init__(self, output, initial_formatting=None):
        if initial_formatting is None:
            self.initial_formatting = []
        else:
            self.initial_formatting = initial_formatting
        self.before = None
        self.after = None
        self.output = output

    def commit(self):
        # Python narrow Unicode is useless for long characters
        # UTF-32 is a good container to count characters
        before_32 = self.before.encode('utf-32-be')
        after_32 = self.after.encode('utf-32-be')
        # Get the closest multiple of 4 for length
        offset = len(commonprefix([before_32, after_32]))//4*4
        if before_32[offset:]:
            self.output.send_backspaces(len(before_32[offset:])//4)
        if after_32[offset:]:
            # Convert back to Unicode for the send_string method
            self.output.send_string(after_32[offset:].decode('utf-32-be'))
        self.before = ''
        self.after = ''

    @staticmethod
    def _actions_to_text(action_list, text=u''):
        for a in action_list:
            if a.replace and text.endswith(a.replace):
                text = text[:-len(a.replace)]
            # With numbers, it's possible to have a.text='2' with a.word='1.2'
            # folowing by an action that replaces '1.2' by '$1.20'...
            if len(a.word) > len(a.text) and a.word.endswith(text):
                text = a.word
            else:
                text += a.text
        return text

    def render(self, undo, do):

        initial_text = self._actions_to_text(self.initial_formatting)

        min_length = min(len(undo), len(do))
        for i in range(min_length):
            if undo[i] != do[i]:
                break
        else:
            i = min_length

        if i > 0:
            initial_text = self._actions_to_text(undo[:i], initial_text)
            undo = undo[i:]
            do = do[i:]

        self.before = initial_text
        self.after = initial_text[:]

        self.before = self._actions_to_text(undo, self.before)

        for a in do:
            if a.replace and self.after.endswith(a.replace):
                self.after = self.after[:-len(a.replace)]
            self.after += a.text
            if a.combo:
                self.commit()
                self.output.send_key_combination(a.combo)
            if a.command:
                self.commit()
                self.output.send_engine_command(a.command)
        self.commit()


class _Action(object):
    """A hybrid class that stores instructions and resulting state.

    A single translation may be formatted into one or more actions. The
    instructions are used to render the current action and the state is used as
    context to render future translations.

    """

    CASE_NONE, CASE_UPPER, CASE_LOWER, CASE_TITLE = range(4)

    def __init__(self, attach=False, glue=False, word='', capitalize=False,
                 lower=False, orthography=True, space_char=' ',
                 upper=False, upper_carry=False,
                 case=CASE_NONE, text='', replace='', combo='',
                 command=''):
        """Initialize a new action.

        Arguments:

        attach -- True if there should be no space between this and the next
        action.

        glue -- True if there be no space between this and the next action if
        the next action also has glue set to True.

        word -- The current word. This is context for future actions whose
        behavior depends on the previous word such as suffixes.

        capitalize -- True if the next action should be capitalized.

        lower -- True if the next action should be lower cased.

        upper -- True if the entire next action should be uppercase.

        upper_carry -- True if we are uppercasing the current word.

        othography -- True if orthography rules should be applies when adding
        a suffix to this action.

        space_char -- this character will replace spaces after all other
        formatting has been applied

        case -- an integer to determine which case to output after formatting

        text -- The text that should be rendered for this action.

        replace -- Text that should be deleted for this action.

        combo -- The key combo, in plover's key combo language, that should be
        executed for this action.

        command -- The command that should be executed for this action.

        """
        # State variables
        self.attach = attach
        self.glue = glue
        self.word = word
        self.capitalize = capitalize
        self.lower = lower
        self.upper = upper
        self.upper_carry = upper_carry
        self.orthography = orthography

        # Persistent state variables
        self.space_char = space_char
        self.case = case

        # Instruction variables
        self.text = text
        self.replace = replace
        self.combo = combo
        self.command = command

    def copy_state(self):
        """Clone this action but only clone the state variables."""
        a = _Action()
        a.attach = self.attach
        a.glue = self.glue
        a.word = self.word
        a.capitalize = self.capitalize
        a.lower = self.lower
        a.upper = self.upper
        a.upper_carry = self.upper_carry
        a.orthography = self.orthography
        a.case = self.case
        a.space_char = self.space_char
        return a

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return 'Action(%s)' % ', '.join('%s=%r' % (k, v) for k, v
                                        in sorted(self.__dict__.items()))

    def __repr__(self):
        return str(self)

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


def _translation_to_actions(translation, last_action, spaces_after):
    """Create actions for a translation.

    Arguments:

    translation -- A string with the translation to render.

    last_action -- The action in whose context this translation is formatted.

    Returns: A list of actions.

    """
    actions = []
    # Reduce the translation to atoms. An atom is an irreducible string that is
    # either entirely a single meta command or entirely text containing no meta
    # commands.
    if translation.isdigit():
        # If a translation is only digits then glue it to neighboring digits.
        atoms = [_apply_glue(translation)]
    else:
        atoms = [
            x.strip(' ') for x in META_RE.findall(translation) if x.strip(' ')
        ]

    if not atoms:
        return [last_action.copy_state()]

    for atom in atoms:
        action = _atom_to_action(atom, last_action, spaces_after)
        actions.append(action)
        last_action = action
    return actions


SPACE = ' '
NO_SPACE = ''
META_STOPS = ('.', '!', '?')
META_COMMAS = (',', ':', ';')
META_CAPITALIZE = '-|'
META_CARRY_CAPITALIZATION = '~|'
META_LOWER = '>'
META_UPPER = '<'
META_RETRO_CAPITALIZE = '*-|'
META_RETRO_LOWER = '*>'
META_RETRO_UPPER = '*<'
META_RETRO_FORMAT = '*('
META_GLUE_FLAG = '&'
META_ATTACH_FLAG = '^'
META_KEY_COMBINATION = '#'
META_COMMAND = 'PLOVER:'
META_MODE = 'MODE:'
MODE_CAPS = 'CAPS'
MODE_TITLE = 'TITLE'
MODE_LOWER = 'LOWER'
MODE_SNAKE = 'SNAKE'
MODE_SET_SPACE = 'SET_SPACE:'
MODE_RESET_SPACE = 'RESET_SPACE'
MODE_RESET_CASE = 'RESET_CASE'
MODE_CAMEL = 'CAMEL'
MODE_RESET = 'RESET'


def _raw_to_actions(stroke, last_action, spaces_after):
    """Turn a raw stroke into actions.

    Arguments:

    stroke -- A string representation of the stroke.

    last_action -- The context in which the new actions are created

    Returns: A list of actions.

    """
    # If a raw stroke is composed of digits then remove the dash (if
    # present) and glue it to any neighboring digits. Otherwise, just
    # output the raw stroke as is.
    no_dash = stroke.replace('-', '', 1)
    if no_dash.isdigit():
        return _translation_to_actions(no_dash, last_action, spaces_after)
    else:
        if spaces_after:
            return [_Action(text=(stroke + SPACE), word=stroke, case=last_action.case,
                            space_char=last_action.space_char)]
        else:
            return [_Action(text=(SPACE + stroke), word=stroke, case=last_action.case,
                            space_char=last_action.space_char)]


def _atom_to_action(atom, last_action, spaces_after):
    """Convert an atom into an action.

    Arguments:

    atom -- A string holding an atom. An atom is an irreducible string that is
    either entirely a single meta command or entirely text containing no meta
    commands.

    last_action -- The context in which the new action takes place.

    Returns: An action for the atom.

    """

    if spaces_after:
        return _atom_to_action_spaces_after(atom, last_action)
    else:
        return _atom_to_action_spaces_before(atom, last_action)


def _atom_to_action_spaces_before(atom, last_action):
    """Convert an atom into an action.

    Arguments:

    atom -- A string holding an atom. An atom is an irreducible string that is
    either entirely a single meta command or entirely text containing no meta
    commands.

    last_action -- The context in which the new action takes place.

    Returns: An action for the atom.

    """

    action = _Action(space_char=last_action.space_char, case=last_action.case)
    last_word = last_action.word
    last_glue = last_action.glue
    last_attach = last_action.attach
    last_capitalize = last_action.capitalize
    last_lower = last_action.lower
    last_upper = last_action.upper
    last_upper_carry = last_action.upper_carry
    last_orthography = last_action.orthography
    begin = False  # for meta attach
    meta = _get_meta(atom)
    if meta is not None:
        meta = _unescape_atom(meta)
        if meta in META_COMMAS:
            action.text = meta
        elif meta in META_STOPS:
            action.text = meta
            action.capitalize = True
            action.lower = False
            action.upper = False
        elif meta == META_CAPITALIZE:
            action = last_action.copy_state()
            action.capitalize = True
            action.lower = False
            action.upper = False
        elif meta == META_LOWER:
            action = last_action.copy_state()
            action.lower = True
            action.upper = False
            action.capitalize = False
        elif meta == META_UPPER:
            action = last_action.copy_state()
            action.lower = False
            action.upper = True
            action.capitalize = False
        elif meta == META_RETRO_CAPITALIZE:
            action = last_action.copy_state()
            action.word = _capitalize(action.word)
            if len(last_action.text) < len(last_action.word):
                action.replace = last_action.word
                action.text = _capitalize(last_action.word)
            else:
                action.replace = last_action.text
                action.text = _capitalize_nowhitespace(last_action.text)
        elif meta == META_RETRO_LOWER:
            action = last_action.copy_state()
            action.word = _lower(action.word)
            if len(last_action.text) < len(last_action.word):
                action.replace = last_action.word
                action.text = _lower(last_action.word)
            else:
                action.replace = last_action.text
                action.text = _lower_nowhitespace(last_action.text)
        elif meta == META_RETRO_UPPER:
            action = last_action.copy_state()
            action.word = _upper(action.word)
            action.upper_carry = True
            if len(last_action.text) < len(last_action.word):
                action.replace = last_action.word
                action.text = _upper(last_action.word)
            else:
                action.replace = last_action.text
                action.text = _upper(last_action.text)
        elif (meta.startswith(META_CARRY_CAPITALIZATION) or
              meta.startswith(META_ATTACH_FLAG + META_CARRY_CAPITALIZATION)):
            action = _apply_carry_capitalize(meta, last_action)
        elif meta.startswith(META_RETRO_FORMAT):
            if meta.startswith(META_RETRO_FORMAT) and meta.endswith(')'):
                action = _apply_currency(meta, last_action)
        elif meta.startswith(META_COMMAND):
            action = last_action.copy_state()
            action.command = meta[len(META_COMMAND):]
        elif meta.startswith(META_MODE):
            action = last_action.copy_state()
            action = _change_mode(meta[len(META_MODE):], action)
        elif meta.startswith(META_GLUE_FLAG):
            action.glue = True
            glue = last_glue or last_attach
            space = NO_SPACE if glue else SPACE
            text = meta[len(META_GLUE_FLAG):]
            if last_capitalize:
                text = _capitalize(text)
            if last_lower:
                text = _lower(text)
            action.text = space + text
            action.word = _rightmost_word(last_word + action.text)
        elif (meta.startswith(META_ATTACH_FLAG) or
              meta.endswith(META_ATTACH_FLAG)):
            begin = meta.startswith(META_ATTACH_FLAG)
            end = meta.endswith(META_ATTACH_FLAG)
            if begin:
                meta = meta[len(META_ATTACH_FLAG):]
            if end and len(meta) >= len(META_ATTACH_FLAG):
                meta = meta[:-len(META_ATTACH_FLAG)]
            space = NO_SPACE if begin or last_attach else SPACE
            if end:
                action.attach = True
            if begin and end and meta == '':
                # We use an empty connection to indicate a "break" in the
                # application of orthography rules. This allows the
                # stenographer to tell plover not to auto-correct a word.
                action.orthography = False
            if (((begin and not end) or (begin and end and ' ' in meta)) and
                    last_orthography):
                new = orthography.add_suffix(last_word.lower(), meta)
                common = commonprefix([last_word.lower(), new])
                action.replace = last_word[len(common):]
                meta = new[len(common):]
            if last_capitalize:
                meta = _capitalize(meta)
            if last_lower:
                meta = _lower(meta)
            if last_upper_carry:
                meta = _upper(meta)
                action.upper_carry = True
            action.text = space + meta
            action.word = _rightmost_word(
                last_word[:len(last_word)-len(action.replace)] + action.text)
        elif meta.startswith(META_KEY_COMBINATION):
            action = last_action.copy_state()
            action.combo = meta[len(META_KEY_COMBINATION):]
    else:
        text = _unescape_atom(atom)
        if last_capitalize:
            text = _capitalize(text)
        if last_lower:
            text = _lower(text)
        if last_upper:
            text = _upper(text)
            action.upper_carry = True
        space = NO_SPACE if last_attach else SPACE
        action.text = space + text
        action.word = _rightmost_word(text)

    action.text = _apply_mode(action.text, action.case, action.space_char,
                              begin, last_attach, last_glue,
                              last_capitalize, last_upper, last_lower)

    return action


def _atom_to_action_spaces_after(atom, last_action):
    """Convert an atom into an action.

    Arguments:

    atom -- A string holding an atom. An atom is an irreducible string that is
    either entirely a single meta command or entirely text containing no meta
    commands.

    last_action -- The context in which the new action takes place.

    Returns: An action for the atom.

    """

    action = _Action(space_char=last_action.space_char, case=last_action.case)
    last_word = last_action.word
    last_glue = last_action.glue
    last_attach = last_action.attach
    last_capitalize = last_action.capitalize
    last_lower = last_action.lower
    last_upper = last_action.upper
    last_upper_carry = last_action.upper_carry
    last_orthography = last_action.orthography
    last_space = SPACE if last_action.text.endswith(SPACE) else NO_SPACE
    was_space = len(last_space) is not 0
    begin = False  # for meta attach
    meta = _get_meta(atom)
    if meta is not None:
        meta = _unescape_atom(meta)
        if meta in META_COMMAS:
            action.text = meta + SPACE
            if last_action.text != '':
                if was_space:
                    action.replace = SPACE
                else:
                    action.replace = NO_SPACE
            if last_attach:
                action.replace = NO_SPACE
        elif meta in META_STOPS:
            action.text = meta + SPACE
            action.capitalize = True
            action.lower = False
            if last_action.text != '':
                if was_space:
                    action.replace = SPACE
                else:
                    action.replace = NO_SPACE
            if last_attach:
                action.replace = NO_SPACE
        elif meta == META_CAPITALIZE:
            action = last_action.copy_state()
            action.capitalize = True
            action.lower = False
        elif meta == META_LOWER:
            action = last_action.copy_state()
            if was_space:
                # Persist space state
                action.replace = SPACE
                action.text = SPACE
            action.lower = True
            action.capitalize = False
        elif meta == META_UPPER:
            action = last_action.copy_state()
            action.lower = False
            action.upper = True
            action.capitalize = False
        elif (meta.startswith(META_CARRY_CAPITALIZATION) or
              meta.startswith(META_ATTACH_FLAG + META_CARRY_CAPITALIZATION)):
            action = _apply_carry_capitalize(meta, last_action, spaces_after=True)
        elif meta == META_RETRO_CAPITALIZE:
            action = last_action.copy_state()
            action.word = _capitalize(action.word)
            if len(last_action.text) < len(last_action.word):
                action.replace = last_action.word + SPACE
                action.text = _capitalize(last_action.word + SPACE)
            else:
                action.replace = last_action.text
                action.text = _capitalize_nowhitespace(last_action.text)
        elif meta == META_RETRO_LOWER:
            action = last_action.copy_state()
            action.word = _lower(action.word)
            if len(last_action.text) < len(last_action.word):
                action.replace = last_action.word + SPACE
                action.text = _lower(last_action.word + SPACE)
            else:
                action.replace = last_action.text
                action.text = _lower_nowhitespace(last_action.text)
        elif meta == META_RETRO_UPPER:
            action = last_action.copy_state()
            action.word = _upper(action.word)
            action.upper_carry = True
            if len(last_action.text) < len(last_action.word):
                action.replace = last_action.word + SPACE
                action.text = _upper(last_action.word + SPACE)
            else:
                action.replace = last_action.text
                action.text = _upper(last_action.text)
        elif meta.startswith(META_RETRO_FORMAT):
            if meta.startswith(META_RETRO_FORMAT) and meta.endswith(')'):
                action = _apply_currency(meta, last_action, spaces_after=True)
        elif meta.startswith(META_COMMAND):
            action = last_action.copy_state()
            action.command = meta[len(META_COMMAND):]
        elif meta.startswith(META_MODE):
            action = last_action.copy_state()
            action = _change_mode(meta[len(META_MODE):], action)
        elif meta.startswith(META_GLUE_FLAG):
            action.glue = True
            text = meta[len(META_GLUE_FLAG):]
            if last_capitalize:
                text = _capitalize(text)
            if last_lower:
                text = _lower(text)
            action.text = text + SPACE
            action.word = _rightmost_word(text)
            if last_glue:
                if was_space:
                    action.replace = SPACE
                else:
                    action.replace = NO_SPACE
                action.word = _rightmost_word(last_word + text)
            if last_attach:
                action.replace = NO_SPACE
                action.word = _rightmost_word(last_word + text)
        elif (meta.startswith(META_ATTACH_FLAG) or
              meta.endswith(META_ATTACH_FLAG)):
            begin = meta.startswith(META_ATTACH_FLAG)
            end = meta.endswith(META_ATTACH_FLAG)
            if begin:
                meta = meta[len(META_ATTACH_FLAG):]
            if end and len(meta) >= len(META_ATTACH_FLAG):
                meta = meta[:-len(META_ATTACH_FLAG)]

            space = NO_SPACE if end else SPACE
            replace_space = NO_SPACE if last_attach else SPACE

            if end:
                action.attach = True
            if begin and end and meta == '':
                # We use an empty connection to indicate a "break" in the
                # application of orthography rules. This allows the
                # stenographer to tell plover not to auto-correct a word.
                action.orthography = False
                if last_action.text != '':
                    action.replace = replace_space
            if (((begin and not end) or (begin and end and ' ' in meta)) and
                    last_orthography):
                new = orthography.add_suffix(last_word.lower(), meta)
                common = commonprefix([last_word.lower(), new])
                if last_action.text == '':
                    replace_space = NO_SPACE
                action.replace = last_word[len(common):] + replace_space
                meta = new[len(common):]
            if begin and end:
                if last_action.text != '':
                    action.replace = replace_space
            if last_capitalize:
                meta = _capitalize(meta)
            if last_lower:
                meta = _lower(meta)
            if last_upper_carry:
                meta = _upper(meta)
                action.upper_carry = True
            action.text = meta + space
            action.word = _rightmost_word(
                last_word[:len(last_word + last_space)-len(action.replace)]
                + meta)
            if end and not begin and last_space == SPACE:
                action.word = _rightmost_word(meta)
        elif meta.startswith(META_KEY_COMBINATION):
            action = last_action.copy_state()
            action.combo = meta[len(META_KEY_COMBINATION):]
    else:
        text = _unescape_atom(atom)
        if last_capitalize:
            text = _capitalize(text)
        if last_lower:
            text = _lower(text)
        if last_upper:
            text = _upper(text)
            action.upper_carry = True

        action.text = text + SPACE
        action.word = _rightmost_word(text)

    action.text = _apply_mode(action.text, action.case, action.space_char,
                              begin, last_attach, last_glue,
                              last_capitalize, last_upper, last_lower)
    return action


def _apply_mode(text, case, space_char, begin, last_attach,
                last_glue, last_capitalize, last_upper, last_lower):
    # Should title case be applied to the beginning of the next string?
    lower_title_case = ((begin or
                         last_attach or
                         last_glue) and not
                        (last_capitalize or
                         last_upper))
    # Apply case, then replace space character
    text = _apply_case(text, case, lower_title_case)
    text = _apply_space_char(text, space_char)

    # Title case is sensitive to lower flag
    if last_lower and len(text) > 0:  # Check for text
        if case is _Action.CASE_TITLE:
            text = _lower(text)

    return text


def _apply_currency(meta, last_action, spaces_after=False):
    dict_format = meta[len(META_RETRO_FORMAT):-len(')')]
    action = last_action.copy_state()
    cast_input = None
    try:
        cast_input = float(last_action.word)
    except ValueError:
        pass
    else:
        currency_format = dict_format.replace('c', '{:,.2f}')
    try:
        cast_input = int(last_action.word)
    except ValueError:
        pass
    else:
        currency_format = dict_format.replace('c', '{:,}')
    if cast_input is not None:
        action.replace = last_action.word
        action.word = currency_format.format(cast_input)
        action.text = action.word
        if spaces_after:
            action.replace += SPACE
            action.text += SPACE
    return action


def _apply_carry_capitalize(meta, last_action, spaces_after=False):
    # Meta format: ^~|content^ (attach flags are optional)
    attach_last = meta.startswith(META_ATTACH_FLAG)
    attach_next = meta.endswith(META_ATTACH_FLAG)

    content_start = meta.index(META_CARRY_CAPITALIZATION) + len(META_CARRY_CAPITALIZATION)
    content_end = -len(META_ATTACH_FLAG) if attach_next else None
    meta_content = meta[content_start:content_end]

    action = last_action.copy_state()
    action.attach = attach_next

    # Spaces after: delete last space if we're attaching.
    replace_last = last_action.text.endswith(SPACE) and attach_last
    action.replace = SPACE if replace_last else NO_SPACE

    if meta_content:
        action.word = meta_content

        # Only prefix a space if spaces are before, last action wasn't attach, and no attach_last flag.
        prefix = NO_SPACE if attach_last or spaces_after or last_action.attach else SPACE
        # Only suffix a space if spaces are after or there's an attach_next flag.
        suffix = NO_SPACE if attach_next or not spaces_after else SPACE
        action.text = prefix + meta_content + suffix

    return action

def _change_mode(command, action):

    """
    command should be:
        CAPS, LOWER, TITLE, CAMEL, SNAKE, RESET_SPACE,
            RESET_CASE, SET_SPACE or RESET

        CAPS: UPPERCASE
        LOWER: lowercase
        TITLE: Title Case
        CAMEL: titleCase, no space, initial lowercase
        SNAKE: Underscore_space
        RESET_SPACE: Space resets to ' '
        RESET_CASE: Reset to normal case
        SET_SPACE:xy: Set space to xy
        RESET: Reset to normal case, space resets to ' '
    """

    if command == MODE_CAPS:
        action.case = _Action.CASE_UPPER

    elif command == MODE_TITLE:
        action.case = _Action.CASE_TITLE

    elif command == MODE_LOWER:
        action.case = _Action.CASE_LOWER

    elif command == MODE_SNAKE:
        action.space_char = '_'
    elif command == MODE_CAMEL:
        action.case = _Action.CASE_TITLE
        action.space_char = ''
        action.lower = True

    elif command == MODE_RESET:
        action.space_char = SPACE
        action.case = _Action.CASE_NONE

    elif command == MODE_RESET_SPACE:
        action.space_char = SPACE

    elif command == MODE_RESET_CASE:
        action.case = _Action.CASE_NONE

    elif command.startswith(MODE_SET_SPACE):
        action.space_char = command[len(MODE_SET_SPACE):]

    return action


def _apply_case(input_text, case, appended):
    text = input_text
    if case is _Action.CASE_LOWER:
        text = text.lower()
    elif case is _Action.CASE_UPPER:
        text = text.upper()
    elif case is _Action.CASE_TITLE:
        # Do nothing to appended output
        if not appended:
            text = string.capwords(text, " ")
    return text


def _apply_space_char(text, space_char):
    if space_char != ' ':
        return text.replace(' ', space_char)
    else:
        return text


def _get_meta(atom):
    """Return the meta command, if any, without surrounding meta markups."""
    if (atom is not None and
        atom.startswith(META_START) and
        atom.endswith(META_END)):
        return atom[len(META_START):-len(META_END)]
    return None


def _apply_glue(s):
    """Mark the given string as a glue stroke."""
    return META_START + META_GLUE_FLAG + s + META_END


def _unescape_atom(atom):
    """Replace escaped meta markups with unescaped meta markups."""
    return atom.replace(META_ESC_START, META_START).replace(META_ESC_END,
                                                            META_END)


def _get_engine_command(atom):
    """Return the steno engine command, if any, represented by the atom."""
    if (atom and
        atom.startswith(META_START + META_COMMAND) and
        atom.endswith(META_END)):
        return atom[len(META_START) + len(META_COMMAND):-len(META_END)]
    return None


def _capitalize(s):
    """Capitalize the first letter of s."""
    return s[0:1].upper() + s[1:]


def _lower(s):
    """Lowercase the first letter of s."""
    return s[0:1].lower() + s[1:]


def _capitalize_nowhitespace(s):
    """Capitalize the first letter of s (ignoring spaces)."""
    word_list = s.split(' ')
    final_list = []
    first_word = True
    for word in word_list:
        if len(word) > 0:
            if first_word is True:
                word = word[0:1].upper() + word[1:]
                first_word = False
        final_list.append(word)
    return ' '.join(final_list)


def _lower_nowhitespace(s):
    """Lowercase the first letter of s (ignoring spaces)."""
    word_list = s.split(' ')
    final_list = []
    first_word = True
    for word in word_list:
        if len(word) > 0:
            if first_word is True:
                word = word[0:1].lower() + word[1:]
                first_word = False
        final_list.append(word)
    return ' '.join(final_list)


def _upper(s):
    """Uppercase the entire s."""
    return s.upper()


def _rightmost_word(s):
    """Get the rightmost word in s."""
    return s.rpartition(' ')[2]
