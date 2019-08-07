# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for steno_dictionary.py."""

import os
import stat
import tempfile

import pytest

from plover.steno_dictionary import StenoDictionary, StenoDictionaryCollection

from . import parametrize


def test_dictionary():
    notifications = []
    def listener(longest_key):
        notifications.append(longest_key)

    d = StenoDictionary()
    assert d.longest_key == 0

    d.add_longest_key_listener(listener)
    d[('S',)] = 'a'
    assert d.longest_key == 1
    assert notifications == [1]
    d[('S', 'S', 'S', 'S')] = 'b'
    assert d.longest_key == 4
    assert notifications == [1, 4]
    d[('S', 'S')] = 'c'
    assert d.longest_key == 4
    assert d[('S', 'S')] == 'c'
    assert notifications == [1, 4]
    del d[('S', 'S', 'S', 'S')]
    assert d.longest_key == 2
    assert notifications == [1, 4, 2]
    del d[('S',)]
    assert d.longest_key == 2
    assert notifications == [1, 4, 2]
    assert d.reverse_lookup('c') == {('S', 'S')}
    assert d.casereverse_lookup('c') == {'c'}
    d.clear()
    assert d.longest_key == 0
    assert notifications == [1, 4, 2, 0]
    assert d.reverse_lookup('c') == set()
    assert d.casereverse_lookup('c') == set()

    d.remove_longest_key_listener(listener)
    d[('S', 'S')] = 'c'
    assert d.longest_key == 2
    assert notifications == [1, 4, 2, 0]


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
    assert dc.lookup_from_all(('S',)) == [('c', d2), ('a', d1)]
    assert dc.lookup_from_all(('W',)) == [('d', d2)]
    assert dc.lookup_from_all(('T',)) == [('b', d1)]
    f = lambda k, v: v == 'c'
    dc.add_filter(f)
    assert dc.lookup(('S',)) == 'a'
    assert dc.raw_lookup(('S',)) == 'c'
    assert dc.lookup_from_all(('S',)) == [('a', d1)]
    g = lambda k, v: v == 'a'
    dc.add_filter(g)
    assert dc.lookup(('S',)) is None
    assert dc.lookup_from_all(('S',)) == []
    assert dc.raw_lookup(('S',)) == 'c'
    assert dc.lookup(('W',)) == 'd'
    assert dc.lookup(('T',)) == 'b'
    assert dc.raw_lookup(('W',)) == 'd'
    assert dc.raw_lookup(('T',)) == 'b'
    assert dc.raw_lookup_from_all(('S',)) == [('c', d2), ('a', d1)]
    assert dc.raw_lookup_from_all(('W',)) == [('d', d2)]
    assert dc.raw_lookup_from_all(('T',)) == [('b', d1)]
    assert dc.reverse_lookup('c') == {('S',)}

    dc.remove_filter(f)
    dc.remove_filter(g)
    assert dc.lookup(('S',)) == 'c'
    assert dc.lookup(('W',)) == 'd'
    assert dc.lookup(('T',)) == 'b'
    assert dc.lookup_from_all(('S',)) == [('c', d2), ('a', d1)]
    assert dc.lookup_from_all(('W',)) == [('d', d2)]
    assert dc.lookup_from_all(('T',)) == [('b', d1)]

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
    assert d.casereverse_lookup('something') == {'something'}
    del d[('S-G',)]
    assert d.casereverse_lookup('something') == {'something'}
    del d[('SPH-G',)]
    assert d.casereverse_lookup('something') == set()


def test_casereverse_lookup():
    dc = StenoDictionaryCollection()

    d1 = StenoDictionary()
    d1[('PWAOUFL',)] = 'beautiful'
    d1[('WAOUFL',)] = 'beAuTIFul'

    d2 = StenoDictionary()
    d2[('PW-FL',)] = 'BEAUTIFUL'

    d3 = StenoDictionary()
    d3[('WAOUFL',)] = 'not beautiful'

    dc.set_dicts([d1, d2, d3])

    assert dc.casereverse_lookup('beautiful') == {'beautiful', 'BEAUTIFUL', 'beAuTIFul'}


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
    assert dc.casereverse_lookup('testing') == {'Testing'}
    assert dc.reverse_lookup('Testing') == {('TEFT', '-G'), ('TEFGT',)}
    d2.enabled = False
    assert dc.lookup(('TEFT',)) == 'test1'
    assert dc.raw_lookup(('TEFT',)) == 'test1'
    assert dc.casereverse_lookup('testing') == {'Testing'}
    assert dc.reverse_lookup('Testing') == {('TEFGT',)}
    d1.enabled = False
    assert dc.lookup(('TEST',)) is None
    assert dc.raw_lookup(('TEFT',)) is None
    assert dc.casereverse_lookup('testing') == set()
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


TEST_DICTIONARY_UPDATE_DICT = {
    ('S-G',): 'something',
    ('SPH-G',): 'something',
    ('SPH*G',): 'Something',
    ('SPH', 'THEUPBG'): 'something',
}
TEST_DICTIONARY_UPDATE_STENODICT = StenoDictionary()
TEST_DICTIONARY_UPDATE_STENODICT.update(TEST_DICTIONARY_UPDATE_DICT)

@pytest.mark.parametrize('update_from, start_empty', (
    (dict(TEST_DICTIONARY_UPDATE_DICT), True),
    (dict(TEST_DICTIONARY_UPDATE_DICT), False),
    (list(TEST_DICTIONARY_UPDATE_DICT.items()), True),
    (list(TEST_DICTIONARY_UPDATE_DICT.items()), False),
    (iter(TEST_DICTIONARY_UPDATE_DICT.items()), True),
    (iter(TEST_DICTIONARY_UPDATE_DICT.items()), False),
    (TEST_DICTIONARY_UPDATE_STENODICT, True),
    (TEST_DICTIONARY_UPDATE_STENODICT, False),
))
def test_dictionary_update(update_from, start_empty):
    d = StenoDictionary()
    if not start_empty:
        d.update({
            ('SPH*G',): 'not something',
            ('STHEUPBG',): 'something',
            ('EF', 'REU', 'TH*EUPBG'): 'everything',
        })
        assert d[('STHEUPBG',)] == 'something'
        assert d[('EF', 'REU', 'TH*EUPBG')] == 'everything'
        assert d.reverse_lookup('not something') == {('SPH*G',)}
        assert d.longest_key == 3
    d.update(update_from)
    assert d[('S-G',)] == 'something'
    assert d[('SPH-G',)] == 'something'
    assert d[('SPH*G',)] == 'Something'
    assert d[('SPH', 'THEUPBG')] == 'something'
    if not start_empty:
        assert d[('STHEUPBG',)] == 'something'
        assert d[('EF', 'REU', 'TH*EUPBG')] == 'everything'
        assert d.reverse_lookup('not something') == set()
        assert d.reverse_lookup('something') == {('STHEUPBG',), ('S-G',), ('SPH-G',), ('SPH', 'THEUPBG')}
        assert d.casereverse_lookup('something') == {'something', 'Something'}
        assert d.longest_key == 3
    else:
        assert d.reverse_lookup('something') == {('S-G',), ('SPH-G',), ('SPH', 'THEUPBG')}
        assert d.casereverse_lookup('something') == {'something', 'Something'}
        assert d.longest_key == 2
