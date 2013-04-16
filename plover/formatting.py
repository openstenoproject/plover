# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""This module converts translations to printable text.

This module defines and implements plover's custom dictionary language.

"""

from os.path import commonprefix
from collections import namedtuple
import orthography
import re

class Formatter(object):
    """Convert translations into output.

    The main entry point for this class is format, which takes in translations
    to format. Output is sent via an output class passed in through set_output.
    Other than setting the output, the formatter class is stateless. 

    The output class can define the following functions, which will be called if
    available:

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

    def __init__(self):
        self.set_output(None)

    def set_output(self, output):
        """Set the output class."""
        noop = lambda x: None
        output_type = type(self).output_type
        fields = output_type._fields
        self._output = output_type(*[getattr(output, f, noop) for f in fields])

    def format(self, undo, do, prev):
        """Format the given translations.

        Arguments:

        undo -- A sequence of translations that should be undone. The formatting
        parameter of the translations will be used to undo the actions that were
        taken, if possible.

        do -- The new actions to format. The formatting attribute will be filled
        in with the result.

        prev -- The last translation before the new actions in do. This
        translation's formatting attribute provides the context for the new
        rendered translations. If there is no context then this may be None.

        """
        for t in do:
            last_action = _get_last_action(prev.formatting if prev else None)
            if t.english:
                t.formatting = _translation_to_actions(t.english, last_action)
            else:
                t.formatting = _raw_to_actions(t.rtfcre[0], last_action)
            prev = t

        old = [a for t in undo for a in t.formatting]
        new = [a for t in do for a in t.formatting]
        
        min_length = min(len(old), len(new))
        for i in xrange(min_length):
            if old[i] != new[i]:
                break
        else:
            i = min_length

        _undo(old[i:], self._output)
        _render_actions(new[i:], self._output)


def _get_last_action(actions):
    """Return last action in actions if possibleor return a blank action."""
    return actions[-1] if actions else _Action()

def _undo(actions, output):
    """Send instructions to output to undo actions."""
    for a in reversed(actions):
        if a.text:
            output.send_backspaces(len(a.text))
        if a.replace:
            output.send_string(a.replace)

def _render_actions(actions, output):
    """Send instructions to output to render new actions."""
    for a in actions:
        if a.replace:
            output.send_backspaces(len(a.replace))
        if a.text:
            output.send_string(a.text)
        if a.combo:
            output.send_key_combination(a.combo)
        if a.command:
            output.send_engine_command(a.command)

class _Action(object):
    """A hybrid class that stores instructions and resulting state.

    A single translation may be formatted into one or more actions. The
    instructions are used to render the current action and the state is used as
    context to render future translations.

    """
    def __init__(self, attach=False, glue=False, word='', capitalize=False,
                 text='', replace='', combo='', command=''):
        """Initialize a new action.

        Arguments:

        attach -- True if there should be no space between this and the next
        action.

        glue -- True if there be no space between this and the next action if
        the next action also has glue set to True.

        word -- The current word. This is context for future actions whose
        behavior depends on the previous word such as suffixes.

        capitalize -- True if the next action should be capitalized.

        text -- The text that should be rendered for this action.

        replace -- Text that should be deleted for this action.

        combo -- The key combo, in plover's key combo language, that should be
        executed for this action.

        command -- The command that should be executed for this actions.

        """
        # State variables
        self.attach = attach
        self.glue = glue
        self.word = word
        self.capitalize = capitalize
                
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
        return a
        
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return 'Action(%s)' % str(self.__dict__)

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

def _translation_to_actions(translation, last_action):
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
        atoms = [x.strip() for x in META_RE.findall(translation) if x.strip()]

    if not atoms:
        return [last_action.copy_state()]

    for atom in atoms:
        action = _atom_to_action(atom, last_action)
        actions.append(action)
        last_action = action

    return actions


SPACE = ' '
NO_SPACE = ''
META_STOPS = ('.', '!', '?')
META_COMMAS = (',', ':', ';')
META_CAPITALIZE = '-|'
META_GLUE_FLAG = '&'
META_ATTACH_FLAG = '^'
META_KEY_COMBINATION = '#'
META_COMMAND = 'PLOVER:'

def _raw_to_actions(stroke, last_action):
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
        return _translation_to_actions(no_dash, last_action)
    else:
        return [_Action(text=(SPACE + stroke), word=stroke)]

def _atom_to_action(atom, last_action):
    """Convert an atom into an action.

    Arguments:

    atom -- A string holding an atom. An atom is an irreducible string that is
    either entirely a single meta command or entirely text containing no meta
    commands.

    last_action -- The context in which the new action takes place.

    Returns: An action for the atom.

    """
    action = _Action()
    last_word = last_action.word
    last_glue = last_action.glue
    last_attach = last_action.attach
    last_capitalize = last_action.capitalize
    meta = _get_meta(atom)
    if meta is not None:
        meta = _unescape_atom(meta)
        if meta in META_COMMAS:
            action.text = meta
        elif meta in META_STOPS:
            action.text = meta
            action.capitalize = True
        elif meta == META_CAPITALIZE:
            action = last_action.copy_state()
            action.capitalize = True
        elif meta.startswith(META_COMMAND):
            action = last_action.copy_state()
            action.command = meta[len(META_COMMAND):]
        elif meta.startswith(META_GLUE_FLAG):
            action.glue = True
            glue = last_glue or last_attach
            space = NO_SPACE if glue else SPACE
            text = meta[len(META_GLUE_FLAG):]
            if last_capitalize:
                text = _capitalize(text)
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
            if (begin and not end) or (begin and end and ' ' in meta):
                new = orthography.add_suffix(last_word.lower(), meta)
                common = commonprefix([last_word.lower(), new])
                action.replace = last_word[len(common):]
                meta = new[len(common):]
            if last_capitalize:
                meta = _capitalize(meta)
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
        space = NO_SPACE if last_attach else SPACE
        action.text = space + text
        action.word = _rightmost_word(text)
    return action

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
    """Capitalize s."""
    return s[0:1].upper() + s[1:]

def _rightmost_word(s):
    """Get the rightmost word in s."""
    return s.rpartition(' ')[2]
