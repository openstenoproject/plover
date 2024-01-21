# `plover.engine` -- Steno engine

```{py:module} plover.engine

```

The steno engine is the core of Plover; it handles communication between the
machine and the translation and formatting subsystems, and manages configuration
and dictionaries.

````{class} StenoEngine(config, controller, keyboard_emulation)
```{attribute} config
:type: Dict[str, any]
:noindex:

A dictionary containing configuration options.
```

```{attribute} controller
:type: plover.oslayer.controller.Controller
:noindex:

An instance of {class}`Controller<plover.oslayer.controller.Controller>`
for managing commands sent to this Plover instance. This is provided
during startup.
```

```{attribute} keyboard_emulation
:type: plover.oslayer.keyboardcontrol.KeyboardEmulation
:noindex:

An instance of {class}`KeyboardEmulation<plover.oslayer.keyboardcontrol.KeyboardEmulation>`
provided during startup.
```

```{data} HOOKS
:type: List[str]

A list of all the possible engine hooks. See {ref}`engine-hooks` below for
a list of valid hooks.
```

```{attribute} machine_state
:type: str

The connection state of the current machine. One of `stopped`,
`initializing`, `connected` or `disconnected`.
```

```{attribute} output
:type: bool

`True` if steno output is enabled, `False` otherwise.
```

```{attribute} config
:type: plover.config.Config

A {class}`Config<plover.config.Config>` object containing the engine's
configuration.
```

```{attribute} translator_state
:type: plover.translation._State

A {class}`_State<plover.translation._State>` object containing the
current state of the translator.
```

```{attribute} starting_stroke_state
:type: StartingStrokeState

A {class}`StartingStrokeState` representing the initial state of the
formatter.
```

```{attribute} dictionaries
:type: plover.steno_dictionary.StenoDictionaryCollection

A
{class}`StenoDictionaryCollection<plover.steno_dictionary.StenoDictionaryCollection>`
of all the dictionaries Plover has loaded for the current system.
This includes disabled dictionaries and dictionaries that failed to load.
```

```{method} _in_engine_thread() -> bool
Returns whether we are currently in the same thread that the engine
is running on. This is useful because event listeners for machines and
others are run on separate threads, and we want to be able to run
engine events on the same thread as the main engine.
```

```{method} start()
Starts the steno engine.
```

```{method} quit([code=0])
Quits the steno engine, ensuring that all pending tasks are completed
before exiting.
```

```{method} restart()
Quits and restarts the steno engine, ensuring that all pending tasks
are completed.
```

```{method} run()
Starts the steno engine, translating any strokes that are input.
```

```{method} join()
Joins any sub-threads if necessary and returns an exit code.
```

```{method} load_config() -> bool
Loads the Plover configuration file and returns `True` if it was
loaded successfully, `False` if not.
```

```{method} reset_machine()
Resets the machine state and Plover's connection with the machine, if
necessary, and loads all the configuration and dictionaries.
```

```{method} send_engine_command(command: str)
Runs the specified Plover command, which can be either a built-in
command like `set_config` or one from an external plugin.

`command` is a string containing the command and its argument (if any),
separated by a colon. For example, `lookup` sends the
`lookup` command (the same as stroking `{PLOVER:LOOKUP}`), and
`run_shell:foo` sends the `run_shell` command with the argument
`foo`.
```

```{method} toggle_output()
Toggles steno mode. See {attr}`output` to get the current state, or
{meth}`set_output` to set the state to a specific value.
```

```{method} set_output(enabled: bool)
Enables or disables steno mode. Set `enabled` to `True` to enable
steno mode, or `False` to disable it.
```

```{method} __getitem__(setting: str) -> any
Returns the value of the configuration property `setting`.
```

```{method} __setitem__(setting: str, value: any)
Sets the configuration property `setting` to `value`.
```

```{method} get_suggestions(translation: str) -> List[plover.suggestions.Suggestion]
Returns a list of suggestions for the specified `translation`.
```

```{method} clear_translator_state([undo=False])
Resets the translator to an empty state, as if Plover had just started up,
clearing the entire translation stack. If `undo` is `True`, this also reverts
all previous translations on the stack (which could include a lot of backspaces).
```

```{method} hook_connect(hook: str, callback: Function)
Adds `callback` to the list of handlers that are called when the `hook`
hook gets triggered. Raises a `KeyError` if `hook` is not in
{data}`HOOKS`.

The expected signature of the callback is depends on the hook; see
{ref}`engine-hooks` for more information.
```

```{method} hook_disconnect(hook: str, callback: Function)
Removes `callback` from the list of handlers that are called when
the `hook` hook is triggered. Raises a `KeyError` if `hook` is not in
{data}`HOOKS`, and a `ValueError` if `callback` was never added as
a handler in the first place.
```

The following methods simply provide a way to access the underlying
{class}`StenoDictionaryCollection<plover.steno_dictionary.StenoDictionaryCollection>`.
See the documentation there for more complete information.

```{method} lookup(translation: Tuple[str]) -> str
Returns the first translation for the steno outline `translation` using
all the filters.
```

```{method} raw_lookup(translation: Tuple[str]) -> str
Like {meth}`lookup`, but without any of the filters.
```

```{method} lookup_from_all(translation: Tuple[str]) -> List[str]
Returns all translations for the steno outline `translation` using
all the filters.
```

```{method} raw_lookup_from_all(translation: Tuple[str]) -> List[str]
Like {meth}`lookup_from_all`, but without any of the filters.
```

```{method} reverse_lookup(translation: str) -> List[Tuple[str]]
Returns the list of steno outlines that translate to `translation`.
```

```{method} casereverse_lookup(translation: str) -> List[Tuple[str]]
Like {meth}`reverse_lookup`, but performs a case-insensitive lookup.
```

```{method} add_dictionary_filter(dictionary_filter: Function[(Tuple[str], str), bool])
Adds `dictionary_filter` to the list of dictionary filters.
See {attr}`StenoDictionaryCollection.filters<plover.steno_dictionary.StenoDictionaryCollection.filters>`
for more information.
```

```{method} remove_dictionary_filter(dictionary_filter: Function[(Tuple[str], str), bool])
Removes `dictionary_filter` from the list of dictionary filters.
```

```{method} add_translation(strokes: Tuple[str], translation: str[, dictionary_path: str = None])
Adds a steno entry mapping the steno outline `strokes` to
`translation` in the dictionary at `dictionary_path`, if specified,
or the first writable dictionary.
```
````

````{class} StartingStrokeState(attach, capitalize)
An object representing the starting state of the formatter before any
strokes are input.

```{attribute} attach
:type: bool

Whether to delete the space before the translation when the initial
stroke is translated.
```

```{attribute} capitalize
:type: bool

Whether to capitalize the translation when the initial stroke is
translated.
```
````

````{class} MachineParams(type, options, keymap)
An object representing the current state of the machine.

```{attribute} type
:type: str

The name of the machine. This is the same as the name of the plugin
that provides the machine's functionality. `Keyboard` by default.
```

```{attribute} options
:type: Dict[str, any]

A dictionary of machine specific options. See {mod}`plover.config`
for more information.
```

```{attribute} keymap
:type: plover.machine.keymap.Keymap

A {class}`Keymap<plover.machine.keymap.Keymap>` mapping the current
system to this machine.
```
````

````{class} ErroredDictionary(path, exception)
A placeholder class for a dictionary that failed to load. This is a subclass
of {class}`StenoDictionary<plover.steno_dictionary.StenoDictionary>`.

```{attribute} path
:type: str

The path to the dictionary file.
```

```{attribute} exception
:type: any

The exception that caused the dictionary loading to fail.
```
````

(engine-hooks)=

## Engine Hooks

Plover uses engine hooks to allow plugins to listen to engine events. By
calling {meth}`engine.hook_connect<StenoEngine.hook_connect>` and passing the
name of one of the hooks below and a function, you can write handlers that are
called when Plover hooks get triggered.

```{plover:hook} stroked(stroke: plover.steno.Stroke)
The user just sent a stroke.
```

```{plover:hook} translated(old, new)
% TODO
```

```{plover:hook} machine_state_changed(machine_type: str, machine_state: str)
Either the machine type was changed by the user, or the connection state
of the machine changed. `machine_type` is the name of the machine
(e.g. `Gemini PR`), and `machine_state` is one of `stopped`,
`initializing`, `connected` or `disconnected`.
```

```{plover:hook} output_changed(enabled: bool)
The user requested to either enable or disable steno output. `enabled` is
`True` if output is enabled, `False` otherwise.
```

```{plover:hook} config_changed(config: Dict[str, any])
The configuration was changed, or it was loaded for the first time.
`config` is a dictionary containing *only* the changed fields. Call the
hook function with the
{attr}`StenoEngine.config<plover.engine.StenoEngine.config>`
to initialize your plugin based on the full configuration.
```

```{plover:hook} dictionaries_loaded(dictionaries: plover.steno_dictionary.StenoDictionaryCollection)
The dictionaries were loaded, either when Plover starts up or the system
is changed or when the engine is reset.
```

```{plover:hook} send_string(s: str)
Plover just sent the string `s` over keyboard output.
```

```{plover:hook} send_backspaces(b: int)
Plover just sent backspaces over keyboard output. `b` is the number of
backspaces sent.
```

```{plover:hook} send_key_combination(c: str)
Plover just sent a keyboard combination over keyboard output. `c` is a
string representing the keyboard combination, for example `Alt_L(Tab)`.
```

```{plover:hook} add_translation()
The Add Translation command was activated -- open the Add Translation tool.
```

```{plover:hook} focus()
The Show command was activated -- reopen Plover's main window and bring it
to the front.
```

```{plover:hook} configure()
The Configure command was activated -- open the configuration window.
```

```{plover:hook} lookup()
The Lookup command was activated -- open the Lookup tool.
```

```{plover:hook} suggestions()
The Suggestions command was activated -- open the Suggestions tool.
```

```{plover:hook} quit()
The Quit command was activated -- wrap up any pending tasks and quit Plover.
```
