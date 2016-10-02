
import unittest

from plover.steno import normalize_steno
from plover.steno_dictionary import StenoDictionary, StenoDictionaryCollection
from plover.suggestions import Suggestion, Suggestions


class SuggestionsTest(unittest.TestCase):

    def test_suggestions(self):
        def s(steno):
            return normalize_steno(steno)
        def sg(text, *steno_list):
            return Suggestion(text, [s(steno) for steno in steno_list])
        dictionary = StenoDictionaryCollection()
        dictionary.set_dicts([StenoDictionary({
            s('S*EUFPL')   : u'simple',
            s('TPUL/STOP') : u'{.}',
            s('TKOT')      : u'.',
            s('PREFBGS')   : u'{prefix^}',
            s('PREFBGS/S') : u'prefix{^}',
            s('STWEUBGS')  : u'{^infix^}',
            s('STWEUBGS/S'): u'{^}infix{^}',
            s('SUFBGS')    : u'{^suffix}',
            s('SUFBGS/S')  : u'{^}suffix',
        })])
        suggestions = Suggestions(dictionary)
        self.assertEqual(suggestions.find(u'no match'), [])
        for text in (
            # Word.
            u'''
            SIMPLE
            simple S*EUFPL
            ''',
            # Punctuation.
            '''
            .
            .   TKOT
            {.} TPUL/STOP
            ''',
            # Prefix.
            '''
            PRefix
            {prefix^} PREFBGS
            prefix{^} PREFBGS/S
            ''',
            # Infix.
            '''
            iNFix
            {^infix^} STWEUBGS
            {^}infix{^} STWEUBGS/S
            ''',
            # Suffix.
            '''
            SufFIX
            {^suffix} SUFBGS
            {^}suffix SUFBGS/S
            ''',
        ):
            lines = text.strip().split('\n')
            lookup = lines[0].strip()
            expected = [sg(*result.strip().split())
                        for result in lines[1:]]
            self.assertEqual(suggestions.find(lookup), expected)
