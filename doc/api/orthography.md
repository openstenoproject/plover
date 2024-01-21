# `plover.orthography` -- Orthography rules

```{py:module} plover.orthography
```

This module provides functionality for generating candidates from attaching
orthographic suffixes to translated words. The functions below depend on the
orthography rules for the *current* steno system -- see {doc}`system`, and
especially the documentation for
{data}`ORTHOGRAPHY_RULES<plover.system.ORTHOGRAPHY_RULES>`, for more information.

```{function} make_candidates_from_rules(word: str, suffix: str[, check: Function[str, bool]]) -> List[str]
Using the orthography rules of the current system, calculate the possible
results of attaching `suffix` to the root `word`.

Not all of these may be valid words in the system's language;
{func}`add_suffix` will automatically look up candidate words to find the
orthographically-correct translation.

Pass a `check` function to filter out candidate words. In most cases this
will not be needed; by default this is set to `lambda x: True`, returning
*all* candidates.
```

```{function} add_suffix(word: str, suffix: str) -> str
Add the `suffix` to the `word`, calculating candidates from
{func}`make_candidates_from_rules`. If
{data}`ORTHOGRAPHY_WORDS<plover.system.ORTHOGRAPHY_WORDS>` exists, this
looks up the best candidate from the list; if not, Plover does a simple
join and attaches the suffix as is without any spelling changes.

Returns the result of attaching the suffix to the word respecting
orthographic rules.
```
