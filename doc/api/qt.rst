``plover.gui_qt`` -- Qt plugins
===============================

.. py:module:: plover.gui_qt

.. class:: Engine(config, keyboard_emulation)

    .. method:: signal_connect(name, callback)

    .. attribute:: signal_stroked
    .. attribute:: signal_translated
    .. attribute:: signal_machine_state_changed
    .. attribute:: signal_output_changed
    .. attribute:: signal_config_changed
    .. attribute:: signal_dictionaries_loaded
    .. attribute:: signal_send_string
    .. attribute:: signal_send_backspaces
    .. attribute:: signal_send_key_combination
    .. attribute:: signal_add_translation
    .. attribute:: signal_focus
    .. attribute:: signal_configure
    .. attribute:: signal_lookup
    .. attribute:: signal_quit

.. _qt_tools:

Tools
-----

.. py:module:: plover.gui_qt.tool

.. class:: Tool(engine)

    .. attribute:: TITLE
    .. attribute:: ICON
    .. attribute:: ROLE
    .. attribute:: SHORTCUT

    .. method:: setupUi(widget)

    .. method:: _save_state(settings)
    .. method:: _restore_state(settings)

.. _qt_machine_options:

Machine Options
---------------

.. py:module:: plover.gui_qt.machine_options

.. class:: MachineOption

    .. attribute:: valueChanged
    .. method:: setValue(value)

Internationalization (i18n)
---------------------------

.. py:module:: plover.gui_qt.i18n

.. function:: get_language()
.. function:: install_gettext()
.. function:: get_gettext([package='plover', resource_dir='gui_qt/messages'])

Utilities
---------

.. py:module:: plover.gui_qt.utils

.. function:: ToolBar(*action_list)

.. function:: find_menu_actions(menu)
