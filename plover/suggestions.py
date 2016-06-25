import collections

Suggestion = collections.namedtuple('Suggestion', 'text steno_list')


class Suggestions(object):
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def find(self, translation):
        suggestions = []

        mods = [
            u'%s',  # Same
            u'{^%s}',  # Prefix
            u'{^}%s',
            u'{^%s^}',  # Infix
            u'{^}%s{^}',
            u'{%s^}',  # Suffix
            u'%s{^}',
            u'{&%s}',  # Fingerspell
            u'{#%s}',  # Command
        ]

        possible_translations = set([translation])

        # Only strip spaces, so patterns with \n or \t are correctly handled.
        stripped_translation = translation.strip(' ')
        if stripped_translation and stripped_translation != translation:
            possible_translations.add(stripped_translation)

        lowercase_translation = translation.lower()
        if lowercase_translation != translation:
            possible_translations.add(lowercase_translation)

        similar_words = self.dictionary.casereverse_lookup(translation.lower())
        if similar_words:
            possible_translations |= similar_words

        for t in possible_translations:
            for modded_translation in [mod % t for mod in mods]:
                strokes_list = self.dictionary.reverse_lookup(modded_translation)
                if not strokes_list:
                    continue
                # Return suggestions, sorted by fewest strokes, then fewest keys
                strokes_list = sorted(
                    strokes_list,
                    key=lambda x: (len(x), sum(map(len, x)))
                )
                suggestion = Suggestion(modded_translation, strokes_list)
                suggestions.append(suggestion)

        return suggestions
