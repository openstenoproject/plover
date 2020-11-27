``plover.config`` -- Configuration
==================================

.. py:module:: plover.config

.. class:: DictionaryConfig

    .. attribute:: path
    .. attribute:: enabled
    .. attribute:: short_path
    .. staticmethod:: from_dict(d)
    .. method:: to_dict()
    .. method:: replace(**kwargs)

.. class:: Config

    .. method:: load()
    .. method:: clear()
    .. method:: save()
    .. method:: __getitem__(key)
    .. method:: __setitem__(key, value)
    .. method:: as_dict()
    .. method:: update()

.. exception:: InvalidConfigOption(raw_value, fixed_value[, message=None])

    .. attribute:: raw_value
    .. attribute:: fixed_value
    .. attribute:: message
