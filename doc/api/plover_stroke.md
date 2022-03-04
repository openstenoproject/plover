# `plover_stroke` -- Steno stroke helpers

The `plover_stroke` library provides helpers for working with steno outlines,
such as converting between string representations and lists of keys, or
calculating stroke ordering.

```{note}
This library is a separate package from `plover`; note the underscore
in the name.
```

```{py:module} plover_stroke
```

In order to use this class, create a subclass of the {class}`BaseStroke`
class, and call its {meth}`setup<plover_stroke.BaseStroke.setup>` method.

````{class} BaseStroke
Represents a single steno stroke. {class}`BaseStroke` objects are instances
of `int`, and support most operations one might do to an integer.

```{classmethod} setup(keys: Tuple[str][, implicit_hyphen_keys: List[str] = None, number_key: str = None, numbers: Dict[str, str] = None, feral_number_key: bool = False])

This method is called to provide the parameters for valid steno notation.
{data}`keys<plover.system.KEYS>`,
{data}`implicit_hyphen_keys<plover.system.IMPLICIT_HYPHEN_KEYS>`,
{data}`number_key<plover.system.NUMBER_KEY>`, and
{data}`numbers<plover.system.NUMBERS>` have the same type and function
as in the {mod}`plover.system`.

Set `feral_number_key` to `True` if you want the number key to appear
anywhere in the stroke, for example `1#8`, `18#` and `#18` all parse
correctly to the same value. This is especially useful for parsing RTF
dictionaries.
```

```{classmethod} from_steno(steno: str) -> BaseStroke
Converts the steno notation string into a stroke object.
```

```{classmethod} from_keys(keys: List[str]) -> BaseStroke
Converts the list of steno keys into a stroke object.
```

```{classmethod} from_integer(integer: int) -> BaseStroke
Converts the integer representing a steno stroke into a stroke object.
```

```{method} first() -> str
Returns the name of the first key in the stroke.
```

```{method} last() -> str
Returns the name of the last key in the stroke.
```

```{method} keys() -> Tuple[str]
Returns a tuple of all keys in the stroke.
```

```{method} has_digit() -> bool
Returns `True` if at least one of the keys pressed corresponds to a digit
and the number key is also pressed.
```

```{method} is_number() -> bool
Returns `True` if the stroke represents a number, i.e. the number key is
pressed, and all other keys represent digits.
```

```{method} is_prefix(other: BaseStroke) -> bool
Returns `True` if this stroke is a prefix of `other`. For example,
`STR` is a prefix of `STROEBG`.
```

```{method} is_suffix(other: BaseStroke) -> bool
Returns `True` if this stroke is a suffix of `other`. For example,
`-BG` is a suffix of `STROEBG`.
```

Some of the operator methods below perform key-wise operations on strokes:

```{method} __add__(other: BaseStroke) -> BaseStroke
Returns a stroke with the *union* of the keys in this stroke and `other`.
For example, `HRAT + ER = HRAERT`.
```

```{method} __or__(other: BaseStroke) -> BaseStroke
Identical to {meth}`__add__`.
```

```{method} __and__(other: BaseStroke) -> BaseStroke
Returns a stroke with the *intersection* of the keys in both this stroke
and `other`. For example, `HRAT & KAT = AT`.
```

```{method} __sub__(other: BaseStroke) -> BaseStroke
Returns a stroke with keys that are in this stroke, but not `other`.
For example, `HRAT - KAT = HR`.
```

```{method} __invert__() -> BaseStroke
Returns a stroke with all keys that are not in this stroke.
For example, `~STKPWHRAO = *EUFRPBLGTSDZ`.
```

```{method} __contains__(other: BaseStroke) -> bool
Returns `True` if `other` contains all of the keys in this stroke.
For example, `-T in KAT = True`.
```
````
