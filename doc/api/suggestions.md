# `plover.suggestions` -- Suggestions

```{py:module} plover.suggestions
```

In many steno theories, there may be multiple ways to stroke a certain word.
By providing the user with suggestions while they are writing, this may help
them learn briefs or otherwise shorter outlines for the same input, which leads
to faster, more fluent writing. This module handles providing suggestions.

````{class} Suggestions(dictionary)
An object that handles finding suggestions using the given dictionary.

```{attribute} dictionary
:type: plover.steno_dictionary.StenoDictionaryCollection

A {class}`StenoDictionaryCollection<plover.steno_dictionary.StenoDictionaryCollection>`
containing all of the dictionaries to look up translations from.
```

```{method} find(translation: str) -> List[Suggestion]
Returns the list of suggestions for the word provided in `translation`,
and other words similar to it. Each item in the list is a
{class}`Suggestion` containing possible outlines for a single word.
```
````

````{class} Suggestion(text, steno_list)
An object representing a possible suggestion.

```{attribute} text
:type: str

The translation to get possible suggestion strokes for.
```

```{attribute} steno_list
:type: List[Tuple[str]]

The list of outlines that translate to {attr}`text`, provided in order
of the number of strokes.
````
