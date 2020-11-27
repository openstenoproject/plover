``plover.registry`` -- Plugin registry
======================================

.. py:module:: plover.registry

.. class:: Plugin(plugin_type, name, obj)

    .. attribute:: plugin_type
    .. attribute:: name
    .. attribute:: obj

.. class:: PluginDistribution(dist, plugins)

    .. attribute:: dist
    .. attribute:: plugins

.. class:: Registry([suppress_errors=True])

    .. data:: PLUGIN_TYPES

    .. method:: register_plugin(plugin_type, name, obj)
    .. method:: register_plugin_from_entrypoint(plugin_type, entrypoint)
    .. method:: get_plugin(plugin_type, plugin_name)
    .. method:: list_plugins(plugin_type)
    .. method:: list_distributions()

    .. method:: update()

.. data:: registry
