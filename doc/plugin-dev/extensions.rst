Extensions
==========

Extension plugins are implemented as **classes**. The initializer should take
only a :class:`StenoEngine<plover.engine.StenoEngine>` as a parameter.

.. code-block:: ini

    [options.entry_points]
    plover.extension =
      example_extension = plover_my_plugin.extension:Extension

.. highlight:: python

::

    # plover_my_plugin/extension.py

    class Extension:
      def __init__(self, engine):
        # Called once to initialize an instance which lives until Plover exits.
        pass

      def start(self):
        # Called to start the extension or when the user enables the extension.
        # It can be used to start a new thread for example.
        pass

      def stop(self):
        # Called when Plover exits or the user disables the extension.
        pass

.. TODO:
    - demonstrate hooks
