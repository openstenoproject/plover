# `plover.formatting` -- Formatting Actions

```{py:module} plover.formatting
```

This module handles parsing Plover's dictionary entry mini-language and
converting it into *actions* that the translation engine can execute.

```{data} ATOM_RE
:type: re.re

A regular expression for detecting individual formatting items in a
dictionary entry. Each *atom* is either raw text, possibly containing some
escaped braces (`\{` and `\}`), or a "meta" formatting or translation
command enclosed in braces (e.g. `{*<}`).
```

```{data} WORD_RX
:type: re.re

A regular expression for detecting words in translation output. Each *word*
consists of either an uninterrupted series of letters or numbers, or
a punctuation character that may be surrounded by whitespace characters on
either side.
```

% TODO: complete the remainder of this module

```{eval-rst}
.. class:: RetroFormatter(previous_translations)

    A helper class for iterating over the results of previous translations.
    It supports iterating over previous actions or translated text.

    .. attribute:: previous_translations

    .. data:: FRAGMENT_RX

        A regular expression for detecting fragments in a string of text.
        Each *fragment* is a series of non-whitespace characters followed by
        zero or more trailing whitespace characters.

    .. method:: iter_last_actions()
    .. method:: iter_last_fragments()
    .. method:: last_fragments([count=1])
    .. method:: iter_last_words([strip=False, rx=WORD_RX])
    .. method:: last_words([count=1, strip=False, rx=WORD_RX])
    .. method:: last_text(size)

.. class:: _Context(previous_translations, last_action)

    .. attribute:: previous_translations
    .. attribute:: last_action
    .. attribute:: translated_actions
    .. method:: new_action()
    .. method:: copy_last_action()
    .. method:: translated(action)
    .. method:: iter_last_actions()

.. class:: Formatter

    .. class:: output

        .. attribute:: send_backspaces
        .. attribute:: send_string
        .. attribute:: send_key_combination
        .. attribute:: send_engine_command

    .. attribute:: spaces_after
    .. attribute:: last_output_spaces_after
    .. attribute:: start_capitalized
    .. attribute:: start_attached

    .. method:: add_listener(callback)
    .. method:: remove_listener(callback)
    .. method:: set_output(output)
    .. method:: set_space_placement(s)
    .. method:: format(undo, do, prev)

.. class:: TextFormatter(spaces_after)

    .. attribute:: spaces_after
    .. attribute:: replaced_text
    .. attribute:: appended_text
    .. attribute:: trailing_space

    .. method:: render(action_list, last_action)
    .. method:: reset(trailing_space)

.. class:: OutputHelper(output, before_spaces_after, after_spaces_after)

    .. attribute:: output
    .. attribute:: before
    .. attribute:: after

    .. method:: flush()
    .. method:: render(last_action, undo, do)

.. class:: _Action([prev_attach=False, prev_replace='', glue=False, word=None, orthography=True, space_char=' ', upper_carry=False, case=None, text=None, trailing_space='', combo=None, command=None, next_attach=False, next_case=None])

    .. data:: DEFAULT

    .. attribute:: prev_attach
    .. attribute:: glue
    .. attribute:: word
    .. attribute:: upper_carry
    .. attribute:: orthography
    .. attribute:: next_attach
    .. attribute:: next_case
    .. attribute:: space_char
    .. attribute:: case
    .. attribute:: trailing_space
    .. attribute:: prev_replace
    .. attribute:: text
    .. attribute:: combo
    .. attribute:: command

    .. method:: copy_state()
    .. method:: new_state()

.. class:: Case

    .. data:: CAP_FIRST_WORD
    .. data:: LOWER
    .. data:: LOWER_FIRST_CHAR
    .. data:: TITLE
    .. data:: UPPER
    .. data:: UPPER_FIRST_WORD

.. function:: apply_case(text, case)

.. function:: apply_mode(text, case, space_char, begin, last_action)

.. function:: apply_mode_case(text, case, appended)

.. function:: apply_mode_space_char(text, space_char)

.. function:: capitalize_first_word(s)

.. function:: capitalize_all_words(s)

.. function:: lower_first_character(s)

.. function:: upper_all_words(s)

.. function:: upper_first_word(s)

.. function:: rightmost_word(s)

.. function:: has_word_boundary(s)
```
