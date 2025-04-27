# `plover.system` -- Steno systems

`plover.system` provides a way of accessing properties of the current steno
system. This module is a bit of a special one; every time the steno system is
changed, Plover automatically changes the values of the data members below
based on the system module that is about to be loaded. So rather than letting
you access all installed systems, `system` itself always refers to the one
that is currently active.

```{py:module} plover.system

```

```{function} setup(name: str)
Find a system plugin named `name`, then change the values of the
data members such that they all refer to the steno system described by that
plugin.

Raises a KeyError if there is no plugin by this name.
```

## Plugin-Defined Fields

The fields below all refer to the values based on the active steno system.
Authors of system plugins will also need to define these.

```{data} KEYS
:type: Tuple[str]

A tuple of all the keys in the system. This should be given in
{ref}`steno order<steno_notation>`, i.e. the order they should appear on
the paper tape, and the order they should be used to form strokes in.

Each key **must** be one of the following:

  * a *left-hand key*, which has a hyphen following the letter
    (e.g. `S-`);

  * a *right-hand key*, which has a hyphen preceding the letter
    (e.g. `-F`);

  * a key that does not belong to either hand and does not have a hyphen
    (e.g. `#` or `*`).

Key names **must** be one letter long, excluding the hyphen, and may
consist of any letter or symbol except space, `-` and `/`.

Key names *may* be either lowercase or uppercase, but uppercase key names
are preferred unless required to disambiguate between letters on the same
side, or the official documents for the steno theory use this notation.
For example, the Spanish Melani system uses casing to disambiguate between
the thumb key vowels (`I-`, `A-`, `-E`, `-O`) and the final bank
vowels (`-i`, `-e`, `-a`, `-o`), but the Italian Michela system
uses uppercase on all left-bank keys and lowercase on all right-bank keys.
```

```{data} IMPLICIT_HYPHEN_KEYS
:type: Tuple[str]

A tuple of all keys in {data}`KEYS` that, when included in a stroke, will
cause the string representation of that stroke to not have a hyphen.

Many systems require a hyphen to separate the left and right sides of a
stroke in steno notation; for example, `K-R` in English Stenotype is
interpreted as pressing the *left*-hand `K-` key and the *right*-hand
`-R` key. However, if one of the keys in that stroke is also in
{data}`IMPLICIT_HYPHEN_KEYS`, then the hyphen is omitted, such as the
`A-` key in `KAT` (`K-`, `A-`, `-T`).

If you want your system to simply display all the keys in order without a
hyphen, *and* there are no keys of the same label on either side, set this
field to be equivalent to {data}`KEYS`.
```

```{data} NUMBER_KEY
:type: str | None

If the system has a designated key that is used to enter numbers, this
is the name of that key. On systems using the standard Stenotype layout
with a number bar, for example, this will be `#`, but systems may choose
a different number key, or none at all.
```

```{data} NUMBERS
:type: Dict[str, str]

A dictionary mapping steno key labels to the numeric representations.
This is used in conjunction with {data}`NUMBER_KEY` to interpret steno
strokes that include numbers. For example, if `S-` is mapped to `1-`
(``{"S-": "1-"}``), then pressing `#` and `S-` together is interpreted
as `1-`.

If the system does *not* support numbers, this dictionary may be left empty.
```

```{data} FERAL_NUMBER_KEY
:type: bool | None

If `True`, steno notation with a number key anywhere outside the standard
steno order will still be considered valid, for example `1-8#` in the English
Stenotype layout. `False` if not defined.
```

```{data} UNDO_STROKE_STENO
:type: str | None

If the system has a designated stroke for undoing the last stroke, this is
the string representation of that stroke. English Stenotype, for example,
uses `*`, but systems may choose to not have one, since undoing can be
implemented as a dictionary entry.
```

```{data} SUFFIX_KEYS
:type: Tuple[str]

A list of singular keys that can be used as suffixes without being written
into a separate stroke. For example, `-G` is mapped to the suffix `-ing`,
so you can write `TPAEULG` (`failing`) in one stroke, rather than
`TPAEUL/-G` in two strokes, without defining a separate dictionary entry.
```

````{data} KEYMAPS
:type: Dict[str, Dict[str, str | Tuple[str]]]

A dictionary mapping steno machine names to keymaps mapping system
(logical) keys, or *actions*, to machine (physical) keys.

You should *at least* define a keymap for the `Keyboard` machine so the
system can be used out of the box by someone with a keyboard, but defining
one for every built-in machine type that can physically support your system
would be ideal.

The values in each keymap can be either a string, if only one machine key
is mapped to each action, or a tuple of strings, if multiple keys can be
used for the same action. For example, in the Gemini PR keymap below, the
`S1-` and `S2-` keys on the machine can be used to write the `P-`
steno key, and the `T-` key on the machine can be used to write `L-`.

```python
{
  "Gemini PR": {
    "P-":  ("S1-", "S2-"),
    "L-":  "T-",
    # ...
  },
  # ...
}
```

When multiple keys are mapped to the same action, only one of the provided
keys needs to be pressed to register as part of the stroke.

In addition to the steno keys defined in {data}`KEYS`, other valid actions
are `no-op` for all machines, and `arpeggiate` for Keyboard only.
Arpeggiate mode for keyboards will only work if the `arpeggiate` action
is mapped.
````

````{data} ORTHOGRAPHY_RULES
:type: List[(str, str)]

A list of rules to transform spellings of words when adding suffixes based
on the language's orthography. When a suffix is defined in a dictionary,
Plover will by default attach it to the end of the previous word without a
spelling change, but some rules will need to be defined in languages where
a change is required.

Each item in the list is a tuple consisting of two regular expression
strings. The left string is the pattern of the original word and the added
suffix, and the right string is what it should be replaced with. (If you
are not familiar with Python's regular expression syntax, see the official
documentation for the [`re`](https://docs.python.org/3/library/re.html) module.)

For example, to describe the orthography rule used to generate the word
`lying` (`lie` + `-ing`) in English, we start by writing a regular
expression to describe the pattern:

```python
r"^lie \^ ing$"
```

Note the `^` in the middle, with spaces around it -- this is the pattern
for attaching suffixes to words.

Of course, there are other words that follow this pattern (like `die` and
`vie`), so we can change this to catch the entire class of words:

```python
r"^(.+)ie \^ ing$"
```

We can then write a substitution rule to replace `ie` with `y`:

```python
r"\1ying"
```

So the entire rule is written as:

```python
[
  # ...
  (r"^(.+)ie \^ ing$", r"\1ying"),
  # ...
]
```
````

```{data} DICTIONARIES_ROOT
:type: str | None

The path to the default dictionaries for this system. This may be written
either as a relative path, or using an {ref}`asset path<asset-paths>`.
Typically you would want this directory to be included in your plugin code.

If there are no dictionaries to include, set this to `None`.
```

```{data} DEFAULT_DICTIONARIES
:type: Tuple[str]

A tuple of the file names of default dictionaries for this system, relative
to {data}`DICTIONARIES_ROOT`. If there are no dictionaries to include, set
this to an empty tuple.
```

```{data} ORTHOGRAPHY_RULES_ALIASES
:type: Dict[str, str]

A dictionary mapping a suffix to a possible variation of that suffix,
if the spelling changes depending on the root word.

Plover attempts to use both suffixes when constructing the final word, and
looks up the candidates in {data}`ORTHOGRAPHY_WORDS` to select the final
translation. See {data}`ORTHOGRAPHY_WORDS` for more information.

For example, `-able` and `-ible` are variants of the same suffix, so we
can define a mapping ``{"able": "ible"}`` so that writing, say,
`read{^able}` (`readable`) and `discern{^able}` (`discernible`) will
both resolve to their correct spellings without having to define separate
strokes.

If no such ambiguity is present in the language, this may be empty.
```

```{data} ORTHOGRAPHY_WORDLIST
:type: str | None

A file name containing an orthography dictionary for this system, primarily
for disambiguating orthography substitutions, relative to
{data}`DICTIONARIES_ROOT`. If there is no word list, set this to `None`.

Each line in this word list consists of a word and a number, separated by
a space. See {data}`ORTHOGRAPHY_WORDS` for more information.
```

## Computed Fields

The fields below are automatically calculated from the values defined by
plugin authors, and will not need to be defined separately.

```{data} NAME
:type: str

The full name of the current system. Given the default English Stenotype
system, this name would be ``English Stenotype``. This name will match the
name provided in the entry point for the system.
```

```{data} IMPLICIT_HYPHENS
:type: Set[str]

A set containing the same items as {data}`IMPLICIT_HYPHEN_KEYS`, but
without the hyphens. This is calculated by Plover to be used for steno
stroke normalization and should rarely be accessed instead of
{data}`IMPLICIT_HYPHEN_KEYS`.
```

```{data} KEY_ORDER
:type: Dict[str, int]

A dictionary mapping steno key labels (both the keys themselves and
number equivalents) to their index in the steno order defined in
{data}`KEYS`. The first key (`#` in English Stenotype) will map to 0,
the second key (`S-`, as well as its numeric equivalent `1-`) to 1,
and so on.
```

```{data} ORTHOGRAPHY_WORDS
:type: Dict[str, int]

A dictionary mapping words to their priority in the orthography
dictionary (lower means higher priority).

Plover uses this dictionary to select a translation candidate when it
encounters a suffix attachment. After attempting to join the root word and
the suffix using dictionary lookup, {data}`ORTHOGRAPHY_RULES` or a simple
join, the candidate with the highest priority in the dictionary is selected
as the final translation.

If {data}`ORTHOGRAPHY_WORDLIST` is `None`, this will be empty.
```
