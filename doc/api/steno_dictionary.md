# `plover.steno_dictionary` -- Steno dictionary

```{py:module} plover.steno_dictionary

```

This module handles _dictionaries_, which Plover uses to look up translations
for input steno strokes. Plover's steno engine uses a {class}`StenoDictionaryCollection`
to look up possible translations across multiple dictionaries, which can be
configured by the user.

````{class} StenoDictionary
Represents a single steno dictionary.

```{classmethod} create(resource: str) -> StenoDictionary
Creates a new empty steno dictionary, saved at the path `resource`.
If `resource` refers to an [asset path](asset-paths) or the
dictionary class is read-only (i.e. {attr}`readonly` is true), this
call will fail.
```

```{classmethod} load(resource: str) -> StenoDictionary
Loads a dictionary from the file at `resource` and returns the
dictionary object. If `resource` refers to an [asset path](asset-paths)
or the file is not writable by the user, the dictionary will be
read-only.
```

```{method} save()
Saves the contents of the dictionary to the file it was loaded from.
This may need to be called after adding dictionary entries.
```

```{attribute} enabled
:type: bool

`True` if the dictionary is enabled, which means Plover can use it to
look up translations, `False` otherwise.
```

```{attribute} readonly
:type: bool

`True` if the dictionary is read-only, either because the dictionary
class does not support it or the file itself is read-only.
For most dictionaries this will be `False`.
```

```{attribute} timestamp
:type: int

The Unix timestamp in seconds when the file was last loaded or saved.
```

```{attribute} path
:type: str

The path to the dictionary file.
```

```{method} clear()
Removes all entries in the dictionary.
```

```{method} items() -> List[Tuple[Tuple[str], str]]
Returns the list of items in the dictionary.
```

```{method} update(*args: Iterable[Iterable[Tuple[Tuple[str], str]], **kwargs: Iterable[Tuple[Tuple[str], str]])

Adds the entries provided in `args` and `kwargs` to the dictionary.
Each item in `args` is an iterable containing steno entries (perhaps
batch-loaded from other dictionaries); each key-value pair in `kwargs`
corresponds to one steno entry.
```

The following methods are available to perform various lookup functionality:

```{method} __getitem__(key: Tuple[str]) -> str
Returns the translation for the steno outline `key`, or raises a
`KeyError` if it is not in the dictionary.
```

```{method} __setitem__(key: Tuple[str], value: str)
Sets the translation for the steno outline `key` to `value`.
Fails if the dictionary is read-only.
```

```{method} __delitem__(key: Tuple[str])
Deletes the translation for the steno outline `key`.
Fails if the dictionary is read-only.
```

```{method} __contains__(key: Tuple[str]) -> bool
Returns `True` if the dictionary contains a translation for the
steno outline `key`.
```

```{method} get(key: Tuple[str][, fallback=None]) -> str | None
Returns the translation for the steno outline `key`, or `fallback` if
it is not in the dictionary.
```

```{attribute} reverse
:type: Dict[str, List[Tuple[str]]]

A dictionary mapping translations to possible steno outlines.
```

```{attribute} casereverse
:type: Dict[str, List[Tuple[str]]]

A case-insensitive version of {attr}`reverse`.
```

```{method} reverse_lookup(value: str) -> List[Tuple[str]]
Returns the list of steno outlines that translate to `value`.
```

```{method} casereverse_lookup(value: str) -> List[Tuple[str]]
Like {meth}`reverse_lookup`, but performs a case-insensitive lookup.
```

```{attribute} longest_key
:type: int
The number of strokes in the longest key in this dictionary. This can be used
to automatically filter out some dictionaries to speed up lookups.
```

In addition, dictionary implementors *should* implement the following
methods for reading and writing to dictionary files:

```{method} _load(filename: str)
Reads the dictionary at `filename` and loads its contents into
the current dictionary. This is only called when the dictionary is
first initialized so it is guaranteed to be empty.
```

```{method} _save(filename: str)
Writes the contents of the dictionary to `filename`.
```
````

````{class} StenoDictionaryCollection([dicts: List[StenoDictionary] = None])
A collection of steno dictionaries for the same steno system. Plover would
typically look up outlines in these dictionaries in order until it can
find a translation, but the interface also allows you to access translations
from all dictionaries.

```{attribute} dicts
:type: List[StenoDictionary]

A list of {class}`StenoDictionary` objects, in decreasing order of priority.
```

```{method} set_dicts(dicts: List[StenoDictionary])
Sets the list of dictionaries to `dicts`.
```

```{method} first_writable() -> StenoDictionary
Returns the first dictionary that is writable, or raises `KeyError`
if none of the dictionaries are writable.
```

```{method} set(key: Tuple[str], value: str[, path: str = None])
Adds a dictionary entry mapping the steno outline `key` to the
translation `value`. If `path` is specified, the entry is added there,
otherwise, it is added to the first writable dictionary.
```

```{method} save([path_list: List[str] = None])
Saves all of the dictionaries whose paths are in `path_list`.
If `path_list` is not specified, all writable dictionaries are saved.
Fails if any of the dictionaries are read-only.
```

```{method} __getitem__(path: str) -> StenoDictionary
Returns the dictionary at the specified path, or raises a `KeyError`
if that dictionary is not part of this collection.
```

```{method} get(path: str) -> StenoDictionary | None
Returns the dictionary at the specified path, or ``None`` if it is not
part of this collection.
```

{class}`StenoDictionaryCollection` supports *filters*, to remove words that
satisfy certain criteria from lookup results. The interface to work with
them is as follows:

```{attribute} filters
:type: List[Function[(Tuple[str], str), bool]]

The list of filters currently active. Each filter is a function that
takes a steno outline and a translation and returns a Boolean value.
If a filter returns `True`, the corresponding entry is **removed**
from lookup results.
```

```{method} add_filter(f: Function[(Tuple[str], str), bool])
Adds `f` to the list of filters.
```

```{method} remove_filter(f: Function[(Tuple[str], str), bool])
Removes `f` from the list of filters.
```

To look up dictionary entries, the interface is similar to
{class}`StenoDictionary`:

```{method} lookup(key: Tuple[str]) -> str | None
Returns the first available translation for the steno outline `key`
from the highest-priority dictionary that is not filtered out by
{attr}`filters`. If none of the dictionaries have an entry for this
outline, returns `None`.
```

```{method} raw_lookup(key: Tuple[str]) -> str | None
Like {meth}`lookup`, but returns the first translation from the
highest-priority dictionary regardless of the active filters.
```

```{method} lookup_from_all(key: Tuple[str]) -> List[Tuple[str, StenoDictionary]]
Returns the list of translations for the steno outline `key` from
*all* dictionaries, except those that are filtered out by :attr:`filters`.
Each translation also contains information on which dictionary it was from.
```

```{method} raw_lookup_from_all(key: Tuple[str]) -> List[Tuple[str, StenoDictionary]]
Like {meth}`lookup_from_all`, but returns *all* results, including the ones that
have been filtered out by {attr}`filters`.
```

```{method} reverse_lookup(value: str) -> List[Tuple[str]]
Returns the list of steno outlines from all dictionaries that translate
to `value`.
```

```{method} casereverse_lookup(value: str) -> List[Tuple[str]]
Like {meth}`reverse_lookup`, but performs a case-insensitive lookup.
```

You can also access the longest key across all dictionaries:

```{attribute} longest_key
:type: int

The longest key across all dictionaries.
```
````
