# `plover.exception` -- Exceptions

```{py:module} plover.exception
```

```{exception} InvalidConfigurationError
Raised when there is something wrong in the configuration.
```

```{exception} DictionaryLoaderException(path, exception)
Raised when the dictionary file at `path` could not be loaded.
`exception` is the underlying error that caused the loading to fail.
```
