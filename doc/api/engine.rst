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

    A placeholder class for a dictionary that failed to load. This is a subclass
    of :class:`StenoDictionary<plover.steno_dictionary.StenoDictionary>`.

    :param path: The path to the dictionary file.
    :param exception: The exception that caused the dictionary loading to fail.

.. class:: StenoEngine(config, keyboard_emulation)

    .. data:: HOOKS

        A list of all the possible engine hooks. See "Engine Hooks" below for
        a list of valid hooks.

    .. attribute:: machine_state

        The connection state of the current machine. One of ``stopped``,
        ``initializing``, ``connected`` or ``disconnected``.

    .. attribute:: output

        ``True`` if steno output is enabled, ``False`` otherwise.

    .. attribute:: config
    .. attribute:: translator_state
    .. attribute:: starting_stroke_state

    .. attribute:: dictionaries

        A
        :class:`StenoDictionaryCollection<plover.steno_dictionary.StenoDictionaryCollection>`
        of all the dictionaries Plover has loaded for the current system.
        This includes disabled dictionaries and dictionaries that failed to load.

    .. method:: _in_engine_thread()
    .. method:: run()

    .. method:: send_backspaces(b)

        Send backspaces over keyboard output. `b` is the number of backspaces.

    .. method:: send_string(s)

        Send the string `s` over keyboard output.

    .. method:: send_key_combination(c)

        Send a keyboard combination over keyboard output. `c` is a string
        representing a keyboard combination, for example ``Alt_L(Tab)``.

    .. method:: send_engine_command(command)

        Run the specified Plover command, which can be either a built-in
        command like ``set_config`` or one from an external plugin.

        `command` is a string containing the command and its argument (if any),
        separated by a colon. For example, ``lookup`` sends the
        ``lookup`` command (the same as stroking ``{PLOVER:LOOKUP}``), and
        ``run_shell:foo`` sends the ``run_shell`` command with the argument
        ``foo``.

    .. method:: toggle_output

        Toggle steno mode. See :attr:`output` to get the current state, or
        :meth:`set_output` to set the state to a specific value.

    .. method:: set_output(enabled)

        Enable or disable steno mode. Set `enabled` to ``True`` to enable
        steno mode, or ``False`` to disable it.

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

        Add `callback` to the list of handlers that are called when the `hook`
        hook gets triggered. Raises a ``KeyError`` if `hook` is not in
        :data:`HOOKS`.

    .. method:: hook_disconnect(hook, callback)

        Removes `callback` from the list of handlers that are called when
        the `hook` hook is triggered. Raises a ``KeyError`` if `hook` is not in
        :data:`HOOKS`, and a ``ValueError`` if `callback` was never added as
        a handler in the first place.

.. _engine_hooks:

Engine Hooks
------------

Plover uses engine hooks to allow plugins to listen to engine events. By
calling :meth:`engine.hook_connect<StenoEngine.hook_connect>` and passing the
name of one of the hooks below and a function, you can write handlers that are
called when Plover hooks get triggered.

.. js:function:: stroked(steno_keys)

    The user just sent a stroke. `steno_keys` is a list of steno keys, for
    example ``['K-', 'A-', '-T']``.

.. js:function:: translated(old, new)

.. js:function:: machine_state_changed(machine_type, machine_state)

    Either the machine type was changed by the user, or the connection state
    of the machine changed. `machine_type` is the name of the machine
    (e.g. ``Gemini PR``), and `machine_state` is one of ``stopped``,
    ``initializing``, ``connected`` or ``disconnected``.

.. js:function:: output_changed(enabled)

    The user requested to either enable or disable steno output. `enabled` is
    ``True`` if output is enabled, ``False`` otherwise.

.. js:function:: config_changed(config)

    The configuration was changed, or it was loaded for the first time.
    `config` is a dictionary containing *only* the changed fields. Call the
    hook function with the
    :meth:`StenoEngine.config<plover.engine.StenoEngine.config>`
    to initialize your plugin based on the full configuration.

.. js:function:: dictionaries_loaded(dictionaries)

    The dictionaries were loaded, either when Plover starts up or the system
    is changed or when the engine is reset. `dictionaries` is a
    :class:`StenoDictionaryCollection<plover.steno_dictionary.StenoDictionaryCollection>`.

.. js:function:: send_string(s)

    Plover just sent the string `s` over keyboard output.

.. js:function:: send_backspaces(b)

    Plover just sent backspaces over keyboard output. `b` is the number of
    backspaces sent.

.. js:function:: send_key_combination(c)

    Plover just sent a keyboard combination over keyboard output. `c` is a
    string representing the keyboard combination, for example ``Alt_L(Tab)``.

.. js:function:: add_translation()

    The Add Translation command was activated -- open the Add Translation tool.

.. js:function:: focus()

    The Show command was activated -- reopen Plover's main window and bring it
    to the front.

.. js:function:: configure()

    The Configure command was activated -- open the configuration window.

.. js:function:: lookup()

    The Lookup command was activated -- open the Lookup tool.

.. js:function:: quit()

    The Quit command was activated -- wrap up any pending tasks and quit Plover.
