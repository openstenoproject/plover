# `plover.config` -- Configuration

```{py:module} plover.config

```

This modules handles reading and writing Plover's configuration files, as well
as updating the configuration on-the-fly while Plover is running.

````{class} Config

An object containing the entire Plover configuration. The config object
maintains a cache for any changes that are made while Plover is running.

```{method} load()
Reads and parses the configuration from the configuration file.
Raises an {exc}`InvalidConfigurationError<plover.exception.InvalidConfigurationError>`
if the configuration could not be parsed correctly.
```

```{method} clear()
Clears the configuration and returns to the base state.
```

```{method} save()
Writes the current state of the configuration to the configuration file.
```

```{method} __getitem__(key: str) -> any
Returns the value of the specified `key` in the cache, or in the
full configuration if not available.
```

```{method} __setitem__(key: str, value: any)
Sets the property `key` in the configuration to the specified value.
```

```{method} as_dict() -> Dict[str, any]
Returns the `dict` representation of the current state of the
configuration.
```

```{method} update()
Update the cache to reflect the contents of the full configuration.
```
````

```{exception} InvalidConfigOption(raw_value, fixed_value[, message=None])
An exception raised when a configuration option has been set to an invalid
value, such as one of the wrong type. `fixed_value` is the value that
Plover is falling back on if `raw_value` can't be parsed correctly.
```

````{class} DictionaryConfig
Represents the configuration for one dictionary.

```{attribute} path
:type: str

The fully qualified path to the dictionary file.
```

```{attribute} short_path
:type: str

The shortened path to the dictionary file. This is automatically
calculated from {attr}`path`.
```

```{attribute} enabled
:type: bool

Whether the dictionary is enabled.
```

```{staticmethod} from_dict(d: Dict[str, any]) -> DictionaryConfig
Returns a {class}`DictionaryConfig` constructed from its `dict`
representation.
```

```{method} to_dict() -> Dict[str, any]
Returns the `dict` representation of the dictionary configuration.
```

```{method} replace(**kwargs: Dict[str, any])
Replaces the values of {attr}`path` and {attr}`enabled` with those in `kwargs`.
```
````

(config-keys)=

## Configuration Options

Below is the list of all available configuration keys:

### Output

```{describe} space_placement
When writing translations, whether to add spaces before or after each
translation. Possible values are `Before Output` and `After Output`.
By default, will add spaces *before* translations.
```

```{describe} start_attached
Whether to delete the space before the translation when the initial
stroke is translated. `False` by default.
```

```{describe} start_capitalized
Whether to capitalize the translation when the initial stroke is
translated. ``False`` by default.
```

```{describe} undo_levels
The maximum number of translations Plover is allowed to undo. 100 by default.

Each stroke that performs a translation is added onto an undo stack, and
undo strokes (such as ``*``) remove translations from this stack.
`undo_levels` defines the maximum number of translations in the stack.
```

### Logging

```{describe} log_file_name
The path to the stroke log file, either absolute or expressed relative to
{data}`CONFIG_DIR<plover.oslayer.config.CONFIG_DIR>`. `strokes.log` by default.

This only sets the path for stroke logs; main Plover logs are always
written to `plover.log`.
```

```{describe} enable_stroke_logging
Whether to log strokes. `False` by default.
```

```{describe} enable_translation_logging
Whether to log translations. `False` by default.
```

### Interface

```{describe} start_minimized
Whether to hide the main window when Plover starts up. `False` by default.
```

```{describe} show_stroke_display
Whether to show the paper tape when Plover starts up. `False` by default.
```

```{describe} show_suggestions_display
Whether to show the suggestions window when Plover starts up. `False` by default.
```

```{describe} translation_frame_opacity
The opacity of the Add Translation tool, in percent. 100 by default.
```

```{describe} classic_dictionaries_display_order
The order the dictionaries are displayed in the main window.
`True` displays the highest priority dictionary at the bottom;
`False` displays it at the top. `False` by default.
```

### Plugins

```{describe} enabled_extensions
The list of extensions that are enabled.
```

### Machine

```{describe} auto_start
Whether to enable Plover output when it starts up. `False` by default.
```

```{describe} machine_type
The name of the currently active machine. `Keyboard` by default.
```

````{describe} machine_specific_options
A dictionary of configuration options specific to the current machine.
Consult your machine plugin's documentation to see the available properties.
For the default machine plugins, the following options are available:

```{describe} arpeggiate
Whether to enable arpeggiate mode on the keyboard. `False` by default.
```

```{describe} port
The serial port for serial connections. No default value.

The value will most likely be different between platforms; Windows uses COM
ports, e.g. `COM3`, whereas Unix-like platforms use device paths, e.g.
`/dev/cu.usbmodem14403` or `/dev/ttyACM0`.
```

```{describe} baudrate
The baud rate for serial connections. 9600 by default.
```

```{describe} bytesize
The number of bits in a byte for serial connections. 8 by default.
```

```{describe} parity
The parity bit mode for serial connections, one of
`N` (none), `O` (odd), `E` (even), `M` (mark) or `S` (space).
`N` by default.
```

```{describe} stopbits
The number of stop bits for serial connections. 1 by default.
```

```{describe} timeout
The read timeout for serial connections in seconds, may be ``None`` to
disable read timeouts altogether. 2.0 (2 seconds) by default.
```

```{describe} xonxoff
Whether to use XON/XOFF flow control for serial connections.
`False` by default.
```

```{describe} rtscts
Whether to use RTS/CTS flow control for serial connections.
`False` by default.
```
````

### System

```{describe} system_name
The name of the current steno system. This is the same system that
{mod}`plover.system` refers to. ``English Stenotype`` by default.
```

```{describe} system_keymap
A {class}`Keymap<plover.machine.keymap.Keymap>` mapping between machine
keys and steno keys in the current steno system.

If the system defines a keymap in {data}`KEYMAPS<plover.system.KEYMAPS>`
for the current machine type, that will be the default value; otherwise,
the machine may define a
{attr}`KEYMAP_MACHINE_TYPE<plover.machine.base.StenotypeBase.KEYMAP_MACHINE_TYPE>`
that describes a similar machine to fall back on. If that is not available
either, the default value is an empty keymap.
```

```{describe} dictionaries
A list of {class}`DictionaryConfig` representing the list of dictionaries
Plover uses to translate strokes for the current steno system. The
dictionaries should be listed in order of decreasing priority.
```
