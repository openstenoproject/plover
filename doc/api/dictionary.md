# `plover.dictionary` - Dictionary management

This module provides utility functions for managing dictionaries.

```{py:module} plover.dictionary.base
```

```{function} create_dictionary(resource: str, threaded_save: bool = True)
Creates a new *empty* dictionary at the path specified by `resource`. The type
of dictionary is inferred from the file extension, for example `.json`
automatically creates a JSON dictionary.
If `threaded_save` is `True`, saving the dictionary is done on a new thread.
```

```{function} load_dictionary(resource: str, threaded_save: bool = True)
Loads an existing dictionary at the path specified by `resource`. The type
of dictionary is inferred from the file extension.

If `threaded_save` is `True`, saving the dictionary is done on a new thread.
If the dictionary is read-only, saving is disabled.
```

```{py:module} plover.dictionary.loading_manager
```

````{class} DictionaryLoadingManager
A helper class used by the engine for loading dictionaries. At initialization,
there are no dictionaries loaded; call {meth}`load` to load new dictionaries,
and {meth}`unload_outdated` to remove outdated ones if needed.

```{method} load(filenames: List[str])
Loads a collection of dictionaries located at the paths in `filenames`.
```

```{method} unload_outdated
Removes any dictionaries that need reloading from the internal collection.
```

```{method} start_loading(filename: str)
Loads the dictionary at the path `filename`. If the dictionary was modified
in the file system since the last load, it is considered outdated and will
need to be reloaded by initializing a {class}`DictionaryLoadingOperation`
```

```{method} __len__() -> int
Returns the number of dictionaries loaded.
```

```{method} __getitem__(filename: str) -> StenoDictionary
Loads the dictionary at the path `filename` and returns the corresponding
dictionary object. This may take a while if the dictionary has not yet been loaded.
```

```{method} __contains__(filename: str) -> bool
Returns `True` if there is a dictionary in the collection that has the path
`filename`.
````

````{class} DictionaryLoadingOperation(filename: str)
A helper class tracking information about a dictionary on the file system.

```{method} needs_reloading() -> bool
Returns whether the dictionary has been changed since the last load.

Dictionary objects contain information about the last time they were loaded
in the {attr}`timestamp<plover.steno_dictionary.StenoDictionary.timestamp>` field.
This is compared with the last-modified time on the file system; if the file
system's timestamp is newer, this means the dictionary was changed and needs
reloading.
```

```{method} load()
Loads the dictionary. Access the result with {meth}`get`.
```

```{method} get() -> plover.steno_dictionary.StenoDictionary | plover.exception.DictionaryLoaderException
Returns the object that results from loading the dictionary at the path
`filename`. If the file has been loaded successfully, this should return a
dictionary object; if it failed, it returns a {class}`DictionaryLoaderException<plover.exception.DictionaryLoaderException>`
with more information about the failure.
````

This module also provides the following dictionary classes:

```{class} plover.dictionary.json_dict.JSONDictionary
A specialization of {class}`StenoDictionary<plover.steno_dictionary.StenoDictionary>`
for handling reading from and writing to JSON dictionaries (file extension `.json`).
This is Plover's native dictionary format, and most user dictionaries should be
in this format.
```

```{class} plover.dictionary.rtfcre_dict.RTFDictionary
A specialization of {class}`StenoDictionary<plover.steno_dictionary.StenoDictionary>`
for handling reading from and writing to RTF dictionaries (file extension `.rtf`).

RTF is the standard interchange format for dictionaries in the court reporting
industry, and Plover supports most standard RTF dictionary features as well as
many vendor extensions.
```
