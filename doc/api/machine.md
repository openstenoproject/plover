# `plover.machine` -- Steno machine protocols

This module provides functionality for interacting with steno machines and
keyboards.

```{py:module} plover.machine.base

```

`````{class} StenotypeBase
The base class for all steno machines. Do not use this directly; instead subclass
either {class}`ThreadedStenotypeBase` or {class}`SerialStenotypeBase` depending
on the type of protocol you want to implement.

New machine implementations must define {attr}`KEYS_LAYOUT` and {attr}`ACTIONS`.

```{attribute} KEYS_LAYOUT
:type: str
A human-readable representation of the arrangement of physical keys on the machine.
For example, a conventional steno machine supporting exactly 23 keys should show
key labels arranged in the standard steno layout:

    #  #  #  #  #  #  #  #  #  #
    S- T- P- H- * -F -P -L -T -D
    S- K- W- R- * -R -B -G -S -Z
          A- O-   -E -U

Key labels may appear more than once within this string, since these are automatically
removed when the keymap is created.
```

```{data} ACTIONS
:type: Tuple[str]

Any actions that this machine implements, in addition to the keys shown above.
For example, the `Keyboard` machine supports the `arpeggiate` action to handle
arpeggiating.

Do *not* include `no-op` as an action -- this is automatically added.
```

```{data} KEYMAP_MACHINE_TYPE
:type: str | None
A fallback machine type to use for finding a compatible keymap if one is not
already available for this machine type.

For example, a standard steno machine layout with one `S-` key and one `*` key
may choose to fall back on the TX Bolt protocol for a keymap, since the
layout is identical, so we would write `TX Bolt` here.
```

```{classmethod} get_keys() -> Tuple[str]
Returns the keys this machine supports.
```

```{classmethod} get_actions() -> Tuple[str]
Returns the non-key actions this machine supports.
```

```{attribute} keymap
:type: plover.machine.keymap.Keymap
The active keymap on this machine, which binds physical keys from
{attr}`KEYS_LAYOUT` and actions from {attr}`ACTIONS` to steno keys in the
current steno system.
```

```{method} set_keymap(keymap: plover.machine.keymap.Keymap)
Sets the active keymap to `keymap`.
```

```{attribute} state
:type: str
The current connection state of the machine. This starts at {data}`STATE_STOPPED`
at initialization, but may transition into any of the [other states](machine-states)
throughout the lifetime of the machine.
```

```{method} add_state_callback(callback: Function[(str)])
Adds `callback` to the list of functions called when the machine's state
changes. The state is passed in as one of the [possible state values](machine-states).
```

```{method} remove_state_callback(callback: Function[(str)])
Removes `callback` from the list of functions called when the machine's state
changes.
```

```{method} add_stroke_callback(callback: Function[(List[str])])
Adds `callback` to the list of functions called when a stroke is sent from
the machine. The stroke is represented as a list of the steno key labels from
{data}`KEYS_LAYOUT`.
```

```{method} remove_stroke_callback(callback: Function[(List[str])])
Removes `callback` from the list of functions called when a stroke is sent.
```

The following API is provided for machine implementors:

```{method} _notify_keys(steno_keys: List[str])
Notifies the engine that a stroke was sent by the machine. `steno_keys` is a
list of the *physical* steno keys that were pressed on the machine; this
function automatically handles translating the keys to actions using the
active keymap.
```

```{method} _notify(steno_keys: List[str])
Notifies the engine that a stroke was sent by the machine. `steno_keys` is a
list of actions and/or *logical* steno keys that exist on the steno system.

*Deprecated*: Use {meth}`_notify_keys` instead.
```

```{method} _stopped()
Changes the state of the machine to {data}`STATE_STOPPED`.
```

```{method} _initializing()
Changes the state of the machine to {data}`STATE_INITIALIZING`.
```

```{method} _ready()
Changes the state of the machine to {data}`STATE_RUNNING`.
```

```{method} _error()
Changes the state of the machine to {data}`STATE_ERROR`.
```

Machine implementors should also implement the following:

````{classmethod} get_option_info() -> Dict[str, (T, Function[(str), T])]
Returns a dictionary of configuration options, where the keys are option names,
and the values consist of the default value for that option and a function to
convert from the string representation to the correct type.

For example, the Boolean option `arpeggiate` might be represented as:

```
from plover.misc import boolean

class Keyboard(ThreadedStenotypeBase):
  @classmethod
  def get_option_info(cls):
    return {
      "arpeggiate": (False, boolean),
    }
```

which sets the default value to `False`, and uses {func}`plover.misc.boolean` to
convert from a string to a Boolean value.
````

```{method} start_capture()
The engine has started -- implement this method to attempt to connect to a
machine and start capturing strokes.
```

```{method} stop_capture()
The engine is shutting down -- implement this method to stop capturing strokes,
and cleanly disconnect from a machine if needed.
`````

(machine-states)=

```{data} STATE_STOPPED
The value of {attr}`state<StenotypeBase.state>` when the machine is not connected.
```

```{data} STATE_INITIALIZING
The value of {attr}`state<StenotypeBase.state>` when the machine is attempting to connect.
```

```{data} STATE_RUNNING
The value of {attr}`state<StenotypeBase.state>` when the machine has successfully connected.
```

```{data} STATE_ERROR
The value of {attr}`state<StenotypeBase.state>` when there is an error connecting to the machine.
```

In addition to the {class}`StenotypeBase` class, this module also provides
skeletons for implementing new machine types. Prefer to use these when possible.

````{class} ThreadedStenotypeBase
A machine listener that uses a thread to capture stroke data.

Override {meth}`start_capture<StenotypeBase.start_capture>` and
{meth}`stop_capture<StenotypeBase.stop_capture>` to implement connection and
disconnection if needed.

```{method} run()
Implement this method to handle receiving data from the machine, or leave it
empty to use your own implementation.
```
````

````{class} SerialStenotypeBase(serial_params: Dict[str, any])
A machine listener for supporting machines using serial connections.

Override {meth}`start_capture<StenotypeBase.start_capture>` and
{meth}`stop_capture<StenotypeBase.stop_capture>` to implement connection and
disconnection if needed.

```{data} SERIAL_PARAMS
:type: Dict[str, any]
The dictionary of parameters for serial connections and default values for each.
```

```{attribute} serial_params
:type: Dict[str, any]
The dictionary of parameters for the *current* serial connection. Not to be
confused with {data}`SERIAL_PARAMS`, which provides default values.
```

```{attribute} serial_port
:type: serial.Serial
A handle to the serial port that this listener is connected to.
```

```{method} run()
Implement this method to handle receiving data from the machine, or leave it
empty to use your own implementation.
```

The following helpers are also provided for implementing specific serial protocols:

```{method} _iter_packets(packet_size: int) -> Generator[bytes]
Yields packets of the specified size until the machine is stopped. Call this
method to handle serial protocols with fixed-length packets.
```

```{method} _close_port()
Closes the connection to the serial port. This is automatically called when
{meth}`stop_capture<StenotypeBase.stop_capture>` is called.
```
````
