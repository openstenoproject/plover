``plover.oslayer.keyboardcontrol`` -- Keyboard control
======================================================

.. py:module:: plover.oslayer.keyboardcontrol

This module handles platform-specific operations relating to the keyboard,
both for capturing keyboard input (using the keyboard to write steno) and
keyboard emulation (writing the output from steno translation).

.. class:: KeyboardCapture

    Encapsulates logic for capturing keyboard input. An instance of this is
    used internally by Plover's built-in keyboard plugin.

    Define the :meth:`key_down` and :meth:`key_up` methods below to implement
    custom behavior that gets executed when a key is pressed or released.

    .. data:: SUPPORTED_KEYS_LAYOUT

        A human-readable text representation of the layout of keys on the
        keyboard. This is the same across platforms.

        :type: str

    .. data:: SUPPORTED_KEYS

        A tuple containing the list of individual keys from
        :data:`SUPPORTED_KEYS_LAYOUT`.

        :type: Tuple[str]

    .. method:: suppress_keyboard([suppressed_keys=()])

        Suppresses the specified keys, preventing them from returning any
        output through regular typing. This allows us to intercept keyboard
        events when using keyboard input.

        :type suppressed_keys: List[str]

    .. method:: key_down(key)

        A custom method that is called when a key is pressed. `key` is a string
        representing the name of the key, and must be in :data:`SUPPORTED_KEYS`.
        Does nothing by default.

    .. method:: key_up(key)

        A custom method that is called when a key is released. `key` is a string
        representing the name of the key, and must be in :data:`SUPPORTED_KEYS`.
        Does nothing by default.


.. class:: KeyboardEmulation

    Encapsulates logic for sending keystrokes. Pass an instance of this to
    the :class:`StenoEngine<plover.engine.StenoEngine>` when it is initialized.

    .. method:: send_backspaces(number_of_backspaces)

        Sends the specified number of backspace keys.

    .. method:: send_string(s)

        Sends the sequence of keys that would produce the specified string.

    .. method:: send_key_combination(combo_string)

        Sends the specified key combination. `combo_string` is a string in the
        key combo format described in :mod:`plover.key_combo`.
