# Systems

To define a new system called `Example System`, add it as an entry point:

```ini
[options.entry_points]
plover.system =
  Example System = plover_my_plugin.system
```

If you have any dictionaries, also add the following line to your
`MANIFEST.in`, to ensure that the dictionaries are copied when you distribute
the plugin:

    include plover_my_plugin/dictionaries/*

System plugins are implemented as **modules** with all of the necessary fields
to create a custom key layout.

```python
# plover_my_plugin/system.py

KEYS: Tuple[str, ...]
IMPLICIT_HYPHEN_KEYS: Tuple[str, ...]

SUFFIX_KEYS: Tuple[str, ...]

NUMBER_KEY: Optional[str]
NUMBERS: Dict[str, str]

UNDO_STROKE_STENO: str

ORTHOGRAPHY_RULES: List[Tuple[str, str]]
ORTHOGRAPHY_RULES_ALIASES: Dict[str, str]
ORTHOGRAPHY_WORDLIST: Optional[str]

KEYMAPS: Dict[str, Dict[str, Union[str, Tuple[str, ...]]]]

DICTIONARIES_ROOT: str
DEFAULT_DICTIONARIES: Tuple[str, ...]
```

Note that there are a lot of possible fields in a system plugin. You must set
them all to something but you don't necessarily have to set them to something
*meaningful* (i.e. some can be empty), so they can be pretty straightforward.

Since it is a Python file rather than purely declarative you can run code for
logic as needed, but Plover will try to directly access all of these fields,
which does not leave much room for that. However, it does mean that if for
example you wanted to make a slight modification on the standard English system
to add a key, you could import it and set your system's fields to its fields
as desired with changes to `KEYS` only; or, you could make a base system
class that you import and expand with slightly different values in the various
fields for multiple system plugins like Michela does for Italian.

See the documentation for {mod}`plover.system` for information on all the fields.

% TODO:
% - more details on individual system fields
