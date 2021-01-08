``plover.registry`` -- Plugin registry
======================================

.. py:module:: plover.registry

The Plover registry collects plugins from the local Python environment via
the |entry_points|_ mechanism. This module exposes an interface to access the
list of available plugins, as well as possibly adding new ones.

.. |entry_points| replace:: ``entry_points``
.. _entry_points: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins

.. data:: registry

    A global instance of the Plover registry, initialized by Plover
    at startup.

.. class:: Registry([suppress_errors=True])

    .. data:: PLUGIN_TYPES

        A tuple of valid plugin types, such as ``machine`` for machine plugins
        and ``gui.qt.tool`` for GUI tools.

        :type: Tuple[str]

    .. method:: list_plugins(plugin_type)

        Returns a list of available plugins of the specified type. `plugin_type`
        should be in :data:`PLUGIN_TYPES`, otherwise this raises a ``KeyError``.

        :type plugin_type: str
        :rtype: List[:class:`Plugin`]

    .. method:: get_plugin(plugin_type, plugin_name)

        Returns a :class:`Plugin` object containing information about the plugin
        with the specified name, of the specified type. `plugin_type` is
        case-sensitive, but `plugin_name` is not. Raises a ``KeyError`` if such
        a plugin could not be found.

        :type plugin_type: str
        :type plugin_name: str
        :rtype: :class:`Plugin`

    .. method:: update()

        Re-scans the Python environment to look for plugins, and registers any
        that were previously not loaded.

    .. method:: register_plugin_from_entrypoint(plugin_type, entrypoint)

        Adds a plugin of the specified type discovered through the entry point
        mechanism to the registry.

        :type entrypoint: |EntryPoint|_

        .. |EntryPoint| replace:: ``pkg_resources.EntryPoint``
        .. _EntryPoint: https://setuptools.readthedocs.io/en/latest/pkg_resources.html#entrypoint-objects

    .. method:: register_plugin(plugin_type, name, obj)

        Adds a plugin named `name` of the specified type to the registry.
        `obj` is the Python object that provides the functionality of the
        plugin, and could be a function, class, or module -- the exact type
        depends on the type of plugin (see :doc:`../plugin_dev` for more information).

        If `plugin_type` is not a valid plugin type (i.e. not in :data:`PLUGIN_TYPES`),
        this raises a ``KeyError``.

    .. method:: list_distributions()

        Returns the list of distributions that Plover has found to contain
        Plover plugins. If :meth:`update` has not been called, this will
        return an empty list.

        :rtype: List[:class:`PluginDistribution`]

.. class:: Plugin(plugin_type, name, obj)

    .. attribute:: plugin_type

        The type of the plugin. This will be one of :data:`PLUGIN_TYPES<Registry.PLUGIN_TYPES>`.

        :type: str

    .. attribute:: name

        The name of the plugin. This will be the same as the entrypoint name
        provided when creating a plugin.

        :type: str

    .. attribute:: obj

        The Python object providing the plugin's functionality, could be a
        function, class, or module.

.. class:: PluginDistribution(dist, plugins)

    .. attribute:: dist

        A |Distribution|_ providing information on a single package either
        bundled with Plover, or installed from the plugins manager, for
        example, the main Plover package ``plover 4.0.0-dev8``. Each
        distribution may contain multiple plugins.

        .. |Distribution| replace:: ``pkg_resources.Distribution``
        .. _Distribution: https://setuptools.readthedocs.io/en/latest/pkg_resources.html#distribution-objects

    .. attribute:: plugins

        The list of plugins contained in this distribution.

        :type: List[:class:`Plugin`]
