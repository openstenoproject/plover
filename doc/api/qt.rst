``plover.gui_qt`` -- Qt plugins
===============================

.. py:module:: plover.gui_qt

This module provides the Qt-based steno engine, which is necessary for
developing GUI tool plugins.

.. class:: Engine

    This is largely just a subclass of
    :class:`StenoEngine<plover.engine.StenoEngine>`,
    except for some Qt-specific logic, such as the signals below.

    Since Qt's signals will fit better into the Qt processing model than
    Plover's default :ref:`engine hooks<engine_hooks>`, GUI plugins should
    use the API provided by this engine over the built-in one where possible.

    .. method:: signal_connect(name, callback)

        Registers `callback` as a callback to be called when the `name`
        hook is triggered. The callback is called with the arguments shown
        in :ref:`engine_hooks` when the hook is triggered.

    The individual Qt signals are also available below for convenience, for
    example if you need to trigger them manually. For example,
    ``engine.signal_lookup.emit()`` would trigger the ``lookup`` hook.
    The arguments for each signal are shown in :ref:`engine_hooks`.

    .. attribute:: signal_stroked

        The signal version of the ``stroked`` hook.

    .. attribute:: signal_translated

        The signal version of the ``translated`` hook.

    .. attribute:: signal_machine_state_changed

        The signal version of the ``machine_state_changed`` hook.

    .. attribute:: signal_output_changed

        The signal version of the ``output_changed`` hook.

    .. attribute:: signal_config_changed

        The signal version of the ``config_changed`` hook.

    .. attribute:: signal_dictionaries_loaded

        The signal version of the ``dictionaries_loaded`` hook.

    .. attribute:: signal_send_string

        The signal version of the ``send_string`` hook.

    .. attribute:: signal_send_backspaces

        The signal version of the ``send_backspaces`` hook.

    .. attribute:: signal_send_key_combination

        The signal version of the ``send_key_combination`` hook.

    .. attribute:: signal_add_translation

        The signal version of the ``add_translation`` hook.

    .. attribute:: signal_focus

        The signal version of the ``focus`` hook.

    .. attribute:: signal_configure

        The signal version of the ``configure`` hook.

    .. attribute:: signal_lookup

        The signal version of the ``lookup`` hook.

    .. attribute:: signal_quit

        The signal version of the ``quit`` hook.


.. _qt_tools:

Tools
-----

.. py:module:: plover.gui_qt.tool

Plover provides a helper class for creating GUI tools:

.. class:: Tool(engine)

    A subclass of ``QDialog`` for creating GUI tools. When writing a GUI tool,
    you would typically subclass both :class:`Tool` *and* some generated code
    class (named ``Ui_YourTool`` or something) to take care of the UI setup.

    .. method:: setupUi(widget)

        Sets up the user interface for this tool. You would typically call this
        in the ``__init__`` method of your subclass to actually build the UI.
        Make sure to pass ``self`` in if you do.

    .. attribute:: TITLE

        The title that would show up in the main window's toolbar and the
        tools list in the main menu.

    .. attribute:: ICON

        The path to the icon for this tool, usually of the form ``:/icon.svg``.
        This file should be included as a resource in the GUI plugin.

    .. attribute:: ROLE

        A unique name to identify this tool when saving and loading state.

    .. attribute:: SHORTCUT

        A keyboard shortcut to activate this window, for example ``Ctrl+F``.

    .. method:: _save_state(settings)

        Saves the current state of this tool to `settings`.
        Call ``settings.setValue(key, value)`` to store individual properties
        in this settings object.

        :type settings: ``QSettings``

    .. method:: _restore_state(settings)

        Restores the current state of this tool from `settings`.
        Call ``settings.value(key)`` to retrieve values for the desired
        properties.

        :type settings: ``QSettings``

.. _qt_machine_options:

Machine Options
---------------

.. py:module:: plover.gui_qt.machine_options

.. class:: MachineOption

    Represents the user interface for manipulating machine-specific
    configuration options. Each :class:`MachineOption` class is also a subclass
    of a ``QWidget`` and is set up with a UI, similar to :class:`Tool` above.

    This isn't itself a real class, though; in order to support a machine
    options UI for your machine, subclass ``QWidget`` and your UI class of
    choice and implement the method and attribute below.

    .. method:: setValue(value)

        Sets the contained value to `value`.

    .. attribute:: valueChanged

        A signal that gets emitted when the contained value is changed.
        Callbacks are called with the new value.

        :type: ``QSignal``

.. class:: KeyboardOption

    A :class:`MachineOption` class for keyboard-specific options.

.. class:: SerialOption

    A :class:`MachineOption` class for serial connection-specific options.

Utilities
---------

.. py:module:: plover.gui_qt.utils

.. function:: ToolBar(*action_list)

    Returns a toolbar with a button for each of the specified actions.

    :type action_list: List[``QAction``]
    :rtype: QToolBar

.. function:: find_menu_actions(menu)

    Returns a dictionary mapping action names to action objects in `menu`.
    This traverses the entire menu tree recursively.

    :type menu: ``QMenu``
    :rtype: Dict[str, ``QAction``]
