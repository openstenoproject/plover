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

# The keys in your system, defined in steno order
KEYS: Tuple[str, ...]
# Keys that serve as an implicit hyphen between the two sides of a stroke
IMPLICIT_HYPHEN_KEYS: Tuple[str, ...]

# Singular keys that are defined with suffix strokes in the dictionary
# to allow for folding them into a stroke without an explicit definition
SUFFIX_KEYS: Tuple[str, ...]

# The key that serves as the "number key" like # in English
NUMBER_KEY: Optional[str]
# A mapping of keys to number aliases, e.g. {"S-": "1-"} means "#S-" can be
# written as "1-"
NUMBERS: Dict[str, str]

# The stroke to undo the last stroke
UNDO_STROKE_STENO: str

# A list of rules mapping regex inputs to outputs for orthography.
ORTHOGRAPHY_RULES: List[Tuple[str, str]]
# Aliases for similar or interchangeable suffixes, e.g. "able" and "ible"
ORTHOGRAPHY_RULES_ALIASES: Dict[str, str]
# Name of a file containing words that can be used to resolve ambiguity
# when applying suffixes.
ORTHOGRAPHY_WORDLIST: Optional[str]

# Default key mappins for machine plugins to system keys.
KEYMAPS: Dict[str, Dict[str, Union[str, Tuple[str, ...]]]]

# Root location for default dictionaries
DICTIONARIES_ROOT: str
# File names of default dictionaries
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
