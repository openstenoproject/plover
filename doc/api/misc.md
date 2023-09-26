# `plover.misc` -- Miscellaneous

```{py:module} plover.misc
```

This module provides miscellaneous utility functions.

```{function} popcount_8(v: int) -> int
Returns the number of `1` bits in the 8-bit number `v`.
```

```{function} expand_path(path: str) -> str
Returns an expanded version of `path`, in which paths relative to either
the home directory `~` or the configuration directory
{data}`CONFIG_DIR<plover.oslayer.config.CONFIG_DIR>` are fully qualified.

If `path` is an {ref}`asset path<asset-paths>`, it is returned as is.
```

```{function} shorten_path(path: str) -> str
Returns a shortened version of `path`, in which paths within the home
directory are abbreviated to contain `~`, and paths within the
configuration directory {data}`CONFIG_DIR<plover.oslayer.config.CONFIG_DIR>`
are expressed relative to it.

Relative paths such as those returned by this function are assumed to be
relative to {data}`CONFIG_DIR<plover.oslayer.config.CONFIG_DIR>`.

If `path` is an {ref}`asset path<asset-paths>`, it is returned as is.
```

```{function} normalize_path(path: str) -> str
Returns a normalized version of `path`, resolving the full path if it
refers to a symbolic link, and normalizing the case where necessary.

If `path` is an {ref}`asset path<asset-paths>`, it is returned as is.
```

```{function} boolean(value: any) -> bool
Returns `value` converted to a Boolean value, or raises `ValueError` if
this is not possible.

If `value` is a string, the values `1`, `yes`, `true` and `on` and
their case variants are converted to `True`, and `0`, `no`, `false`
and `off` and their case variants are converted to `False`. If it is
*not* a string, the return value is resolved by casting to `bool`.
```

```{function} to_surrogate_pair(char: str) -> List[int]
Returns a list of numbers corresponding to the UTF-16 encoding for the
string `char`. `char` may have multiple characters.

If each character in `char` has a Unicode codepoint between `U+0000` and
`U+FFFF`, its corresponding element in the return value is the codepoint
as a hexadecimal number; if it is above `U+FFFF`, it is converted to
two elements in the list, the high and low bytes respectively.

For example, the string `"🥺?"` (`U+1F97A` followed by `U+003F`) returns the list
`[55358, 56698, 63]` (`[D83E, DD7A, 003F]` in hexadecimal).
```
