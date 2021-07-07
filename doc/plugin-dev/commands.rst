Commands
========

To define a new command called ``example_command``, add this name as an
entry point in ``setup.cfg``:

.. code-block:: ini

    [options.entry_points]
    plover.command =
      example_command = plover_my_plugin.command:example

The command can be used in dictionary entries:

.. code-block:: json

    {
      "S-": "{PLOVER:EXAMPLE_COMMAND:argument}",
      "T-": "{PLOVER:EXAMPLE_COMMAND}"
    }

Command plugins are implemented as **functions** that take a
:class:`StenoEngine<plover.engine.StenoEngine>` and an optional string
argument. If an argument is not passed in the dictionary entry, it will be
``''``.

.. highlight:: python

::

    # plover_my_plugin/command.py

    def example(engine, argument):
      pass

Commands can access any of the properties and methods in the engine object
passed to it, such as in |plover_system_switcher|_:

::

    def switch_system(engine, system):
      engine.config = {"system_name": system}

They can also interact with the rest of the Python environment, and even other
programs, such as |plover_vlc_commands|_ sending HTTP requests to VLC:

::

    def stop(_, _):
      _vlc_request("?command=pl_stop")

.. |plover_system_switcher| replace:: ``plover_system_switcher``
.. |plover_vlc_commands| replace:: ``plover_vlc_commands``
.. _`plover_system_switcher`: https://github.com/nsmarkop/plover_system_switcher/blob/master/plover_system_switcher.py
.. _`plover_vlc_commands`: https://github.com/benoit-pierre/plover_vlc_commands/blob/master/plover_vlc_commands.py
