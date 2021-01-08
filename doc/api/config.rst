``plover.config`` -- Configuration
==================================

.. py:module:: plover.config

This modules handles reading and writing Plover's configuration files, as well
as updating the configuration on-the-fly while Plover is running.

.. class:: Config

    An object containing the entire Plover configuration. The config object
    maintains a cache for any changes that are made while Plover is running.

    .. method:: load()

        Reads and parses the configuration from the configuration file.
        Raises an :exc:`InvalidConfigurationError<plover.exception.InvalidConfigurationError>`
        if the configuration could not be parsed correctly.

    .. method:: clear()

        Clears the configuration and returns to the base state.

    .. method:: save()

        Writes the current state of the configuration to the configuration file.

    .. method:: __getitem__(key)

        Returns the value of the specified `key` in the cache, or in the
        full configuration if not available.

    .. method:: __setitem__(key, value)

        Sets the property `key` in the configuration to the specified value.

    .. method:: as_dict()

        Returns the ``dict`` representation of the current state of the
        configuration.

    .. method:: update()

        Update the cache to reflect the contents of the full configuration.

.. exception:: InvalidConfigOption(raw_value, fixed_value[, message=None])

    An exception raised when a configuration option has been set to an invalid
    value, such as one of the wrong type. `fixed_value` is the value that
    Plover is falling back on if `raw_value` can't be parsed correctly.

.. class:: DictionaryConfig

    Represents the configuration for one dictionary.

    .. attribute:: path

        The fully qualified path to the dictionary file.

        :type: str

    .. attribute:: short_path

        The shortened path to the dictionary file. This is automatically
        calculated from :attr:`path`.

        :type: str

    .. attribute:: enabled

        Whether the dictionary is enabled.

        :type: bool

    .. staticmethod:: from_dict(d)

        Returns a :class:`DictionaryConfig` constructed from its ``dict``
        representation.

    .. method:: to_dict()

        Returns the ``dict`` representation of the dictionary configuration.

    .. method:: replace(**kwargs)

        Replaces the values of :attr:`path` and :attr:`enabled` with those in `kwargs`.
