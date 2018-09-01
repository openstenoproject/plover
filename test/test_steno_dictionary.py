# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for steno_dictionary.py."""

import os
import re
import stat
import tempfile

import pytest

from plover.steno_dictionary import StenoDictionary, StenoDictionaryCollection


def test_dictionary():
    notifications = []
    def listener(longest_key):
        notifications.append(longest_key)

    d = StenoDictionary()
    assert d.longest_key == 0
    assert len(d) == 0
    assert not d

    d.add_longest_key_listener(listener)
    d[('S',)] = 'a'
    assert d.longest_key == 1
    assert ('S',) in d
    assert notifications == [1]
    assert len(d) == 1
    assert d
    d[('S', 'S', 'S', 'S')] = 'b'
    assert d.longest_key == 4
    assert notifications == [1, 4]
    assert len(d) == 2
    d[('S', 'S')] = 'c'
    assert d.longest_key == 4
    assert d[('S', 'S')] == 'c'
    assert notifications == [1, 4]
    assert len(d) == 3
    del d[('S', 'S', 'S', 'S')]
    assert d.longest_key == 2
    assert notifications == [1, 4, 2]
    assert len(d) == 2
    del d[('S',)]
    assert d.longest_key == 2
    assert ('S',) not in d
    assert notifications == [1, 4, 2]
    assert len(d) == 1
    assert d.reverse_lookup('c') == [('S', 'S')]
    assert d.casereverse_lookup('c') == ['c']
    d.clear()
    assert d.longest_key == 0
    assert notifications == [1, 4, 2, 0]
    assert len(d) == 0
    assert not d
    assert d.reverse_lookup('c') == []
    assert d.casereverse_lookup('c') == []

    d.remove_longest_key_listener(listener)
    d[('S', 'S')] = 'c'
    assert d.longest_key == 2
    assert notifications == [1, 4, 2, 0]


def test_dictionary_update():
    d = StenoDictionary()
    d.update([(('S-G',),'something'), (('SPH-G',), 'something'), (('TPHOG',), 'nothing')])
    assert d[('S-G',)] == 'something'
    assert d[('SPH-G',)] == 'something'
    assert d[('TPHOG',)] == 'nothing'
    assert d.reverse_lookup('something') == [('S-G',), ('SPH-G',)]
    assert d.reverse_lookup('nothing') == [('TPHOG',)]
    d.update([(('S-G',), 'string')])
    assert d[('S-G',)] == 'string'
    assert d.reverse_lookup('something') == [('SPH-G',)]
    assert d.reverse_lookup('string') == [('S-G',)]
    d.clear()
    d.update([(('EFG',), 'everything'), (('EFG',), 'everything???')])
    assert d[('EFG',)] == 'everything???'
    assert d.reverse_lookup('everything') == []
    assert d.reverse_lookup('everything???') == [('EFG',)]


def test_dictionary_collection():
    d1 = StenoDictionary()
    d1[('S',)] = 'a'
    d1[('T',)] = 'b'
    d1.path = 'd1'
    d2 = StenoDictionary()
    d2[('S',)] = 'c'
    d2[('W',)] = 'd'
    d2.path = 'd2'
    dc = StenoDictionaryCollection([d2, d1])
    assert dc.lookup(('S',)) == 'c'
    assert dc.lookup(('W',)) == 'd'
    assert dc.lookup(('T',)) == 'b'
    f = lambda k, v: v == 'c'
    dc.add_filter(f)
    assert dc.lookup(('S',)) is None
    assert dc.raw_lookup(('S',)) == 'c'
    assert dc.lookup(('W',)) == 'd'
    assert dc.lookup(('T',)) == 'b'
    assert dc.reverse_lookup('c') == {('S',)}

    dc.remove_filter(f)
    assert dc.lookup(('S',)) == 'c'
    assert dc.lookup(('W',)) == 'd'
    assert dc.lookup(('T',)) == 'b'

    assert dc.reverse_lookup('c') == {('S',)}

    dc.set(('S',), 'e')
    assert dc.lookup(('S',)) == 'e'
    assert d2[('S',)] == 'e'

    dc.set(('S',), 'f', path='d1')
    assert dc.lookup(('S',)) == 'e'
    assert d1[('S',)] == 'f'
    assert d2[('S',)] == 'e'

    # Iterating on a StenoDictionaryCollection is
    # the same as iterating on its dictionaries' paths.
    assert list(dc) == ['d2', 'd1']

    # Test get and [].
    assert dc.get('d1') == d1
    assert dc['d1'] == d1
    assert dc.get('invalid') is None
    with pytest.raises(KeyError):
        dc['invalid']


def test_dictionary_collection_writeable():
    d1 = StenoDictionary()
    d1[('S',)] = 'a'
    d1[('T',)] = 'b'
    d2 = StenoDictionary()
    d2[('S',)] = 'c'
    d2[('W',)] = 'd'
    d2.readonly = True
    dc = StenoDictionaryCollection([d2, d1])
    assert dc.first_writable() == d1
    dc.set(('S',), 'A')
    assert d1[('S',)] == 'A'
    assert d2[('S',)] == 'c'


def test_dictionary_collection_longest_key():

    k1 = ('S',)
    k2 = ('S', 'T')
    k3 = ('S', 'T', 'R')

    dc = StenoDictionaryCollection()
    assert dc.longest_key == 0

    d1 = StenoDictionary()
    d1.path = 'd1'
    d1[k1] = 'a'

    dc.set_dicts([d1])
    assert dc.longest_key == 1

    d1[k2] = 'a'
    assert dc.longest_key == 2

    d2 = StenoDictionary()
    d2.path = 'd2'
    d2[k3] = 'c'

    dc.set_dicts([d2, d1])
    assert dc.longest_key == 3

    del d1[k2]
    assert dc.longest_key == 3

    dc.set_dicts([d1])
    assert dc.longest_key == 1

    dc.set_dicts([])
    assert dc.longest_key == 0


def test_casereverse_del():
    d = StenoDictionary()
    d[('S-G',)] = 'something'
    d[('SPH-G',)] = 'something'
    assert d.casereverse_lookup('something') == ['something']
    del d[('S-G',)]
    assert d.casereverse_lookup('something') == ['something']
    del d[('SPH-G',)]
    assert d.casereverse_lookup('something') == []


def test_reverse_lookup():
    dc = StenoDictionaryCollection()

    d1 = StenoDictionary()
    d1[('PWAOUFL',)] = 'beautiful'
    d1[('WAOUFL',)] = 'beautiful'

    d2 = StenoDictionary()
    d2[('PW-FL',)] = 'beautiful'

    d3 = StenoDictionary()
    d3[('WAOUFL',)] = 'not beautiful'

    # Simple test.
    dc.set_dicts([d1])
    assert dc.reverse_lookup('beautiful') == {('PWAOUFL',), ('WAOUFL',)}

    # No duplicates.
    d2_copy = StenoDictionary()
    d2_copy.update(d2)
    dc.set_dicts([d2_copy, d2])
    assert dc.reverse_lookup('beautiful') == {('PW-FL',)}

    # Don't stop at the first dictionary with matches.
    dc.set_dicts([d2, d1])
    assert dc.reverse_lookup('beautiful') == {('PW-FL',), ('PWAOUFL',), ('WAOUFL',)}

    # Ignore keys overridden by a higher precedence dictionary.
    dc.set_dicts([d3, d2, d1])
    assert dc.reverse_lookup('beautiful') == {('PW-FL',), ('PWAOUFL',)}


def test_search():
    dc = StenoDictionaryCollection()

    # Similarity is based on string equality after removing case and stripping special characters from the ends.
    d1 = StenoDictionary()
    d1[('WAOUFL',)] = 'beautiful'
    d1[('PWAOUFL',)] = 'Beautiful'
    d1[('PWAOUT', '-FL')] = '{^BEAUTIFUL}  '
    d1[('ULG',)] = 'ugly'
    dc.set_dicts([d1])
    assert dc.find_similar('beautiful') == [('Beautiful',      {('PWAOUFL',)}),
                                            ('beautiful',      {('WAOUFL',)}),
                                            ('{^BEAUTIFUL}  ', {('PWAOUT', '-FL')})]

    assert dc.find_similar('{#BEAUtiful}{^}') == [('Beautiful',      {('PWAOUFL',)}),
                                                  ('beautiful',      {('WAOUFL',)}),
                                                  ('{^BEAUTIFUL}  ', {('PWAOUT', '-FL')})]

    # Translations found in multiple dicts should combine non-overlapping keys in the results.
    d2 = StenoDictionary()
    del d1[('PWAOUT', '-FL')]
    d2[('PW-FL',)] = 'beautiful'
    dc.set_dicts([d1, d2])
    assert dc.find_similar('beautiful') == [('Beautiful', {('PWAOUFL',)}),
                                            ('beautiful', {('WAOUFL',), ('PW-FL',)})]

    # If all possible keys for a translation are overridden, that translation should not be returned.
    d3 = StenoDictionary()
    d3[('PW-FL',)] = 'not beautiful'
    d3[('WAOUFL',)] = 'not beautiful'
    dc.set_dicts([d3, d1, d2])
    assert dc.find_similar('beautiful') == [('Beautiful', {('PWAOUFL',)})]

    # For partial word search, similar words will be returned first, but if the count is greater than that,
    # the next words in sorted order which are supersets are returned. Also stops at the end of the dictionary.
    dc.set_dicts([d1])
    d1[('PWAOU',)] = 'beau'
    d1[('PWAOUFL', 'HREU')] = 'beautifully'
    d1[('UG', 'HREU', '-PBS')] = 'ugliness'
    assert dc.find_partial('beau', count=4) == [('beau',        {('PWAOU',)}),
                                                ('Beautiful',   {('PWAOUFL',)}),
                                                ('beautiful',   {('WAOUFL',)}),
                                                ('beautifully', {('PWAOUFL', 'HREU')})]
    assert dc.find_partial('UGLY', count=2) == [('ugly', {('ULG',)})]

    # Even if a word isn't present, the search will return words going forward
    # from the index where it would be found if it was there.
    assert dc.find_partial('beaut', count=3) == [('Beautiful',   {('PWAOUFL',)}),
                                                 ('beautiful',   {('WAOUFL',)}),
                                                 ('beautifully', {('PWAOUFL', 'HREU')})]

    # Regex search is straightforward; return up to count entries in order that match the given regular expression.
    # If no regex metacharacters are present, should just be a case-sensitive starts-with search.
    assert dc.find_regex('beau', count=4) == [('beau',        {('PWAOU',)}),
                                              ('beautiful',   {('WAOUFL',)}),
                                              ('beautifully', {('PWAOUFL', 'HREU')})]
    assert dc.find_regex('beautiful.?.?', count=2) == [('beautiful',   {('WAOUFL',)}),
                                                       ('beautifully', {('PWAOUFL', 'HREU')})]
    assert dc.find_regex(' beautiful', count=3) == []
    assert dc.find_regex('(b|u).{3}$', count=2) == [('beau', {('PWAOU',)}),
                                                    ('ugly', {('ULG',)})]
    assert dc.find_regex('.*ly', count=5) == [('beautifully', {('PWAOUFL', 'HREU')}),
                                              ('ugly', {('ULG',)})]

    # Regex errors won't raise if the algorithm short circuits a pattern with no possible matches.
    assert dc.find_regex('an open group that doesn\'t raise(', count=5) == []
    with pytest.raises(re.error):
        print(dc.find_regex('beautiful...an open group(', count=1))


def test_dictionary_enabled():
    dc = StenoDictionaryCollection()
    d1 = StenoDictionary()
    d1.path = 'd1'
    d1[('TEFT',)] = 'test1'
    d1[('TEFGT',)] = 'Testing'
    d2 = StenoDictionary()
    d2[('TEFT',)] = 'test2'
    d2[('TEFT', '-G')] = 'Testing'
    d2.path = 'd2'
    dc.set_dicts([d2, d1])
    assert dc.lookup(('TEFT',)) == 'test2'
    assert dc.raw_lookup(('TEFT',)) == 'test2'
    assert dc.casereverse_lookup('testing') == ['Testing']
    assert dc.reverse_lookup('Testing') == {('TEFT', '-G'), ('TEFGT',)}
    d2.enabled = False
    assert dc.lookup(('TEFT',)) == 'test1'
    assert dc.raw_lookup(('TEFT',)) == 'test1'
    assert dc.casereverse_lookup('testing') == ['Testing']
    assert dc.reverse_lookup('Testing') == {('TEFGT',)}
    d1.enabled = False
    assert dc.lookup(('TEST',)) is None
    assert dc.raw_lookup(('TEFT',)) is None
    assert dc.casereverse_lookup('testing') == []
    assert dc.reverse_lookup('Testing') == set()


def test_dictionary_readonly():
    class FakeDictionary(StenoDictionary):
        def _load(self, filename):
            pass
        def _save(self):
            raise NotImplementedError
    tf = tempfile.NamedTemporaryFile(delete=False)
    try:
        tf.close()
        d = FakeDictionary.load(tf.name)
        # Writable file: not readonly.
        assert not d.readonly
        # Readonly file: readonly dictionary.
        os.chmod(tf.name, stat.S_IREAD)
        d = FakeDictionary.load(tf.name)
        assert d.readonly
    finally:
        # Deleting the file will fail on Windows
        # if we don't restore write permission.
        os.chmod(tf.name, stat.S_IWRITE)
        os.unlink(tf.name)
    # Assets are always readonly.
    d = FakeDictionary.load('asset:plover:assets/main.json')
    assert d.readonly
