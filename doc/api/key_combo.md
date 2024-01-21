# `plover.key_combo` -- Key codes

```{py:module} plover.key_combo
```

This module provides utility functions for translating key combination
descriptions as written in translations, as well as mappings between Unicode
symbols and logical key names.

A key combo is specified as a sequence of keys, separated by spaces, some of
which may be surrounded by parentheses and preceded by a modifier key. Key
combos are case-insensitive. For example, the following key combo:

    a ctrl_l(z shift(z))

is equivalent to pressing `A`, then `Ctrl+Z`, then `Ctrl+Shift+Z`.

```{data} KEYNAME_TO_CHAR
:type: Dict[str, str]

A dictionary mapping logical key names to Unicode characters they represent.
The logical key names are derived from X11 keysym names. This mapping does
not include modifiers.
```

```{data} CHAR_TO_KEYNAME
:type: Dict[str, str]

The reverse of {data}`KEYNAME_TO_CHAR`: a dictionary mapping Unicode
characters to the logical key names that would produce them when pressed.
```

The two functions below will also be useful to implementors of keyboard
emulation for new platforms:

```{function} parse_key_combo(combo_string[, key_name_to_key_code=None]) -> List[Tuple[Any, bool]]

Converts `combo_string`, representing a key combination or series of key
combinations, to a list of key events to be emulated. Each key event is a
tuple containing a key code and a boolean value indicating whether
the key is to be pressed (`True`) or released (`False`).

Pass a function to `key_name_to_key_code` to specify the mapping of key
names to key codes as appropriate for your platform; otherwise, the default
is to return the name as is.
```

```{function} add_modifiers_aliases(dictionary)
Adds aliases for modifier keys to the specified `dictionary`, which is a
mapping of key names to key codes.

Typically one would define the key codes for `control_l`, `shift_l`,
`super_l` and `alt_l` in the dictionary and use this function to add
aliases for the remaining variants (such as `alt` and `option` as
aliases of `alt_l`).
```
