``plover.oslayer.keyboardcontrol`` -- Keyboard control
======================================================

.. py:module:: plover.oslayer.keyboardcontrol

.. class:: KeyboardCapture

    .. data:: SUPPORTED_KEYS_LAYOUT
    .. data:: SUPPORTED_KEYS

    .. method:: suppress_keyboard([suppressed_keys=()])
    .. method:: key_down(key)
    .. method:: key_up(key)


.. class:: KeyboardEmulation

    .. attribute:: keyboard_layout
    .. method:: send_backspaces(number_of_backspaces)
    .. method:: send_string(s)
    .. method:: send_key_combination(combo_string)
