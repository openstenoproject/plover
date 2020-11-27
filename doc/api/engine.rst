``plover.engine`` -- Steno engine
==================================

.. py:module:: plover.engine

.. class:: StartingStrokeState(attach, capitalize)

    .. attribute:: attach
    .. attribute:: capitalize

.. class:: MachineParams(type, options, keymap)

    .. attribute:: type
    .. attribute:: options
    .. attribute:: keymap

.. class:: ErroredDictionary(path, exception)

.. class:: StenoEngine(config, keyboard_emulation)

    .. data:: HOOKS

    .. attribute:: machine_state
    .. attribute:: output
    .. attribute:: config
    .. attribute:: translator_state
    .. attribute:: starting_stroke_state
    .. attribute:: dictionaries

    .. method:: _in_engine_thread()
    .. method:: run()
    .. method:: send_backspaces(b)
    .. method:: send_string(s)
    .. method:: send_key_combination(c)
    .. method:: send_engine_command(command)
    .. method:: toggle_output
    .. method:: set_output(enabled)
    .. method:: __getitem__(setting)
    .. method:: __setitem__(setting, value)
    .. method:: reset_machine()
    .. method:: load_config()
    .. method:: start()
    .. method:: quit([code=0])
    .. method:: restart()
    .. method:: join()
    .. method:: lookup(translation)
    .. method:: raw_lookup(translation)
    .. method:: lookup_from_all(translation)
    .. method:: raw_lookup_from_all(translation)
    .. method:: reverse_lookup(translation)
    .. method:: casereverse_lookup(translation)
    .. method:: add_dictionary_filter(dictionary_filter)
    .. method:: remove_dictionary_filter(dictionary_filter)
    .. method:: get_suggestions(translation)
    .. method:: clear_translator_state([undo=False])
    .. method:: add_translation(strokes, translation[, dictionary_path=None])
    .. method:: hook_connect(hook, callback)
    .. method:: hook_disconnect(hook, callback)

.. _engine_hooks:

Engine Hooks
------------

.. js:function:: stroked(steno_keys)
.. js:function:: translated(old, new)
.. js:function:: machine_state_changed(machine_type, machine_state)
.. js:function:: output_changed(enabled)
.. js:function:: config_changed(config)
.. js:function:: dictionaries_loaded(dictionaries)
.. js:function:: send_string(s)
.. js:function:: send_backspaces(b)
.. js:function:: send_key_combination(c)
.. js:function:: add_translation()
.. js:function:: focus()
.. js:function:: configure()
.. js:function:: lookup()
.. js:function:: quit()
