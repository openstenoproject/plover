import collections

from plover.steno import sort_steno_strokes

Suggestion = collections.namedtuple('Suggestion', 'text steno_list')


def find_suggestions(dictionary, translation):
    # List of base translations to try looking up, including stripped and case variations.
    # To remove duplicates while preserving list order, run it through an OrderedDict as a key list.
    base = collections.OrderedDict.fromkeys([
        translation,               # Self
        translation.strip(' '),    # Strip spaces (patterns with \n or \t are correctly handled)
        translation.lower(),       # All lowercase
        translation.capitalize(),  # First letter capitalized
        translation.upper(),       # All uppercase
    ]).keys()

    # List of modifications to apply to each base to find prefixes, suffixes, commands etc.
    mods = [
        lambda s: s,               # No modification
        lambda s: '{^%s}' % s,     # Prefix
        lambda s: '{^}%s' % s,
        lambda s: '{^%s^}' % s,    # Infix
        lambda s: '{^}%s{^}' % s,
        lambda s: '{%s^}' % s,     # Suffix
        lambda s: '%s{^}' % s,
        lambda s: '{&%s}' % s,     # Fingerspell
        lambda s: '{#%s}' % s,     # Raw keystrokes
    ]

    # Run each non-empty base translation through each mod in turn.
    possible_translations = [mod(t) for t in base if t for mod in mods]

    # Look up every possibility and return a suggestion for each one with a non-empty result.
    suggestions = []
    for t in possible_translations:
        strokes_list = dictionary.reverse_lookup(t)
        if not strokes_list:
            continue
        strokes_list = sort_steno_strokes(strokes_list)
        suggestion = Suggestion(t, strokes_list)
        suggestions.append(suggestion)
    return suggestions
