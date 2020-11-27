``plover.steno_dictionary`` -- Steno dictionary
===============================================

.. py:module:: plover.steno_dictionary

.. class:: StenoDictionary

    .. attribute:: reverse
    .. attribute:: casereverse
    .. attribute:: filters
    .. attribute:: timestamp
    .. attribute:: readonly
    .. attribute:: enabled
    .. attribute:: path

    .. classmethod:: create(resource)
    .. classmethod:: load(resource)

    .. method:: save()

    .. method:: _save()
    .. method:: _load()

    .. attribute:: longest_key

    .. method:: __getitem__(key)
    .. method:: __setitem__(key, value)
    .. method:: __delitem__(key)
    .. method:: __contains__(key)

    .. method:: clear()
    .. method:: items()
    .. method:: get(key[, fallback=None])
    .. method:: update(*args, **kwargs)

    .. method:: reverse_lookup(value)
    .. method:: casereverse_lookup(value)

    .. method:: add_longest_key_listener(callback)
    .. method:: remove_longest_key_listener(callback)

.. class:: StenoDictionaryCollection([dicts=None])

    .. attribute:: dicts
    .. attribute:: filters
    .. attribute:: longest_key
    .. attribute:: longest_key_callbacks

    .. method:: set_dicts(dicts)

    .. method:: lookup(key)
    .. method:: raw_lookup(key)
    .. method:: lookup_from_all(key)
    .. method:: raw_lookup_from_all(key)
    .. method:: reverse_lookup(value)
    .. method:: casereverse_lookup(value)

    .. method:: first_writable()

    .. method:: set(key, value[, path=None])
    .. method:: save([path_list=None])
    .. method:: get(path)
    .. method:: __getitem__(path)

    .. method:: add_filter(f)
    .. method:: remove_filter(f)
    .. method:: add_longest_key_listener(callback)
    .. method:: remove_longest_key_listener(callback)
