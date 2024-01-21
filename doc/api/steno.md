# `plover.steno` -- Steno data model

This module deals with the fundamental concept in stenography: the _stroke_.
A stroke is a combination of keys all pressed at once; an _outline_ is a series
of strokes performed in succession.

Many Plover actions deal with steno strokes, and this will be especially useful
to authors of system and dictionary plugins.

(steno_notation)=

## Steno Notation

Steno notation refers to the way steno strokes are written textually, such as
on the paper tape or in dictionaries. Each stroke is written as a concatenation
of several keys, sometimes with a hyphen.

Steno notation is also sometimes referred to as _RTF/CRE_ (Rich Text Format
with Court Reporting Extensions) _notation_, named after the dictionary format
that popularized it.

Each steno system has a _steno order_, or a canonical ordering of all the keys
on the layout. For most systems, this is the ordering of the keys from left to
right, starting with the left bank, then the thumb keys, then the right bank,
but others may use a different order. Well-formed steno notation **must** have
all keys in steno order.

The full list of keys and rules for expressing strokes in steno notation are
defined for each steno system. See {doc}`system` for more information.

### Keys

Combinations of keys can be expressed by concatenating the letters representing
them; for example, `S-`, `-E` and `-T` together can be written `SET`,
and `K-` and `W-` together can be written `KW-`. All but one hyphen is
removed to separate the left and right bank keys, but the hyphen may be
omitted completely if a stroke includes certain keys, such as the `-E` in
`SET`, or the `*` in `R*R`.

Strokes are often written with a hyphen, because without one it may not be
fully clear which side each key is on. For example, the `P` in `KPT` may
refer to _either_ left-hand `P-` _or_ right-hand `-P`; writing `KP-T` or
`K-PT` respectively is unambiguous. Strokes that consist entirely of left
bank keys may be written without a hyphen, e.g. `KW-` can be written `KW`.

Some strokes may still be resolvable when not completely well-formed, i.e.
the hyphen is in the wrong place or doesn't exist when it should, or the keys
aren't fully in steno order, but it's not guaranteed to work.

### Numbers

When a part of a stroke represents a number we don't write the number key;
instead, we replace the letter keys with the corresponding numbers.

For example, to express the stroke represented by pressing the `S-` and
`T-` keys together with the number bar (`#`) in steno notation, we write
`12-`, since `S-` represents the number `1-` and `T-` represents `2-`.

If a stroke consists _only_ of a number key, or none of the other pressed keys
represent numbers, we still write the number key. For example, `#` and `#-R`
are both valid steno notation, since `-R` does not represent a number, but
`#P-` is not (write `3-` instead).

### Multiple Strokes

We use the stroke delimiter, `/`, to separate successive strokes in a single
outline. For example, to write the 3-stroke outline for `New York Times`, we
write:

    TPHU/KWRORBG/TAOEUPLS

Note that `TPHU`, `KWRORBG` and `TAOEUPLS` are all separate strokes, but
the `/` indicates that they are written in sequence.

## Steno Stroke API

```{py:module} plover.steno

```

````{class} Stroke
An object representing a stroke. This class is a subclass of
{class}`BaseStroke<plover_stroke.BaseStroke>`.

```{classmethod} normalize_stroke(steno: str[, strict = False]) -> str
Return the {ref}`normalized steno notation<canonical>` for the singular
stroke `steno`. Raises an exception if the steno was not parsed
correctly, and `strict` is `True`.
```

```{classmethod} normalize_steno(steno: str[, strict = False]) -> Tuple[str]
Return the {ref}`normalized steno notation<canonical>` for the possibly
multi-stroke outline `steno`, where each stroke may be separated by `/`.
Each element in the tuple is one stroke in the outline. Raises an
exception if the steno was not parsed correctly, and `strict` is `True`.
```

```{classmethod} steno_to_sort_key(steno: str[, strict = False]) -> bytes
Return a byte string used to place the steno stroke `steno` in order
in a dictionary. Raises an exception if the steno was not parsed
correctly, and `strict` is `True`.
```

```{attribute} steno_keys
:type: List[str]

A *sorted* list of the steno keys that compose this stroke.
```

```{attribute} rtfcre
:type: str

The normalized (or *canonical*) steno notation for this stroke.

(canonical)=

The canonical steno notation for a stroke has the following properties:

  * All of the keys are in steno order

  * There is a hyphen *only if* at least one key on the right bank is
    pressed *and* this key is not an implicit separator

  * Number keys are written as numbers rather than using the number
    key (for example, `-8` rather than `#-L`)
```

```{attribute} is_correction
:type: bool

Whether this stroke is a `correction` stroke, and can be used to undo
the previous stroke.
```
````

```{function} normalize_stroke(steno: str[, strict = False]) -> str
Same as {meth}`Stroke.normalize_stroke`.
```

```{function} normalize_steno(steno: str[, strict = False]) -> Tuple[str]
Same as {meth}`Stroke.normalize_steno`.
```

```{function} steno_to_sort_key(steno: str[, strict = False]) -> bytes
Same as {meth}`Stroke.steno_to_sort_key`.
```

```{function} sort_steno_strokes(strokes_list: List[Tuple[str]]) -> List[Tuple[str]]
Return a new list of outlines sorted by the number of strokes first, and
then the length of each stroke (number of keys).
```
