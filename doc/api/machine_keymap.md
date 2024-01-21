# `plover.machine.keymap` -- Machine key bindings

```{py:module} plover.machine.keymap
```

This module handles *keymaps*, mappings between keys on a physical machine and
*actions* that produce steno strokes for a certain steno system. Keymaps exist
for each combination of machine and system.

Keymaps are bidirectional, so we make a distinction between *bindings* and
*mappings*: a key is *bound* to an action, i.e. when a key is pressed Plover
performs the corresponding action, and an action is *mapped* to one or more
keys. Each action *should* be mapped to at least one key, and each key to an
action; otherwise, the behavior when stroking is undefined.

````{class} Keymap(keys, actions)

```{attribute} keys
:type: List[str]

A list of possible keys on the physical machine. For a serial steno
protocol like TX Bolt, this would be the steno keys themselves
(`S-`, `T-`, etc.); for the keyboard, this would be keyboard keys
(`q`, `w`, etc.).
```

```{attribute} actions
:type: List[str]

A list of possible actions in the steno system.

In addition to the steno keys in the current system (see
{attr}`system.KEYS<plover.system.KEYS>` for more information),
the actions may include `no-op`, a special action that does nothing,
and `arpeggiate`, a special action for arpeggiate mode that is only
available if the current machine is a keyboard.
```

```{method} get_keys() -> List[str]
Returns the list of possible keys.
```

```{method} get_actions() -> List[str]
Returns the list of possible actions.
```

```{method} get_bindings() -> Dict[str, str]
Returns the dictionary of bindings from keys to actions.
```

```{method} get_mappings() -> Dict[str, List[str]]
Returns the dictionary of mappings from actions to keys.
```

```{method} get_action(key: str[, default=None]) -> str | None
Given `key`, returns the action that would be performed by pressing
the machine key, or `default` if the key is not bound to an action.
```

```{method} __getitem__(key: str) -> List[str]
Returns the list of keys that are bound to the action `key`.
(Confusing, I know.)
```

```{method} __setitem__(action: str, key_list: List[str])
Maps `action` to all the keys in `key_list`. Also unbinds each key in
`key_list` if already bound.
```

```{method} set_bindings(bindings: Dict[str, str])
Use `bindings` as the new keymap. `bindings` is a dictionary mapping
*keys* to *actions*. This also calculates the mappings and calls
{meth}`set_mappings`.
```

```{method} set_mappings(mappings: Dict[str, str | List[str]])
Use `mappings` as the new keymap. `mappings` is a dictionary mapping
*actions* to either a single key or a list of keys that are bound to
that action. This also calculates the bindings and calls :meth:`set_bindings`.

Where `mappings` contains some consistency issues, such as keys
bound multiple times or nonexistent keys or actions, this shows a
warning and the keymap behavior is undefined.
```

```{method} keys_to_actions(key_list: List[str]) -> List[str]
Returns the actions that would be performed by pressing all of the keys
in `key_list`. Raises an error if any element `key_list` is not a valid
machine key (i.e. not in {attr}`keys`).
````
