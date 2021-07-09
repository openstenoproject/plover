# `plover.machine` -- Steno machine protocols

```{py:module} plover.machine.base
```

% TODO: complete the remainder of this module

```{eval-rst}
.. data:: STATE_STOPPED

.. data:: STATE_INITIALIZING

.. data:: STATE_RUNNING

.. data:: STATE_ERROR

.. class:: StenotypeBase

    .. attribute:: KEYS_LAYOUT
    .. attribute:: ACTIONS
    .. attribute:: KEYMAP_MACHINE_TYPE

    .. attribute:: keymap
    .. attribute:: stroke_subscribers
    .. attribute:: state_subscribers
    .. attribute:: state

    .. method:: set_keymap(keymap)
    .. method:: start_capture()
    .. method:: stop_capture()

    .. method:: add_stroke_callback(callback)
    .. method:: remove_stroke_callback(callback)
    .. method:: add_state_callback(callback)
    .. method:: remove_state_callback(callback)

    .. method:: _notify(steno_keys)

    .. method:: set_suppression(enabled)
    .. method:: suppress_last_stroke(send_backspaces)

    .. method:: _stopped()
    .. method:: _initializing()
    .. method:: _ready()
    .. method:: _error()

    .. classmethod:: get_actions()
    .. classmethod:: get_keys()
    .. classmethod:: get_option_info()


.. class:: ThreadedStenotypeBase

.. class:: SerialStenotypeBase

    .. data:: SERIAL_PARAMS

    .. attribute:: serial_port
    .. attribute:: serial_params

    .. method:: _close_port()
    .. method:: _iter_packets(packet_size)

    .. classmethod:: get_option_info()
```
