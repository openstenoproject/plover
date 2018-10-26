""" Unit tests for base dictionary package (dictionary/base.py) """

from plover.dictionary.base import SimilarSearchDict


def test_searchdict():
    """ Basic unit tests for init, getitem, setitem, delitem, len, and contains on SimilarSearchDict. """
    d = SimilarSearchDict(None, {1: "a", 2: "b", 3: "c"})
    assert 1 in d
    assert 2 in d
    assert 5 not in d
    assert len(d) == 3
    del d[1]
    assert 1 not in d
    assert len(d) == 2
    d[1] = "x"
    assert d[1] == "x"
    assert len(d) == 3
    d[1] = "y"
    assert len(d) == 3
    del d["key not here"]
    assert len(d) == 3


def test_searchdict_similar():
    """
    For these tests, the similarity function will remove everything but a's in the string.
    This means strings with equal numbers of a's will compare as "similar".
    In the key lists, they are sorted by this measure, then standard string sort order applies second
    """
    def just_a(key):
        return "".join(c for c in key if c is "a")

    # Keys are restricted to whatever type the similarity function takes, so just use strings for now
    # The values don't matter right now; just have them be the number of a's for reference.
    data = {"a": 1, "Canada": 3, "a man!?": 2, "^hates^": 1, "lots\nof\nlines": 0,
            "": 0,  "A's don't count, just a's": 1, "AaaAaa, Ʊnićodə!": 4}
    d = SimilarSearchDict(simfn=just_a, **data)

    # "Similar keys", should be all keys with the same number of a's as the input
    assert d.get_similar_keys("a") == ["A's don't count, just a's", "^hates^", "a"]
    assert d.get_similar_keys("none in here") == ["", "lots\nof\nlines"]
    assert d.get_similar_keys("Havana") == ["Canada"]
    assert d.get_similar_keys("lalalalala") == []

    # Restrict the number of returned values
    assert d.get_similar_keys("add", 2) == ["A's don't count, just a's", "^hates^"]
    assert d.get_similar_keys("still none of the first English letter", 1) == [""]

    # Using a filter function, return anything with three or more a's
    assert d.filter_keys("aaa", None, str.startswith) == ["Canada", "AaaAaa, Ʊnićodə!"]

    # Without a filter function, return everything in order including/after the given key until count.
    assert d.filter_keys("AAAAaAAAA", 2) == ["A's don't count, just a's", "^hates^"]
    assert d.filter_keys("#%*&!?", 4) == ["", "lots\nof\nlines", "A's don't count, just a's", "^hates^"]
    assert d.filter_keys("a", 5) == ["A's don't count, just a's", "^hates^", "a", "a man!?", "Canada"]
    assert d.filter_keys("aaaaaaaaaa", 100) == []

    # Add/delete/mutate individual items and make sure order is maintained for search.
    del d["^hates^"]
    assert d.get_similar_keys("a") == ["A's don't count, just a's", "a"]
    d["----I shall be first!---"] = 1
    assert d.get_similar_keys("a") == ["----I shall be first!---", "A's don't count, just a's", "a"]
    d["^hates^"] = 1
    assert d.get_similar_keys("a") == ["----I shall be first!---", "A's don't count, just a's", "^hates^", "a"]


def test_searchdict_iter():
    # The iterators should treat this as an ordinary dictionary, independent of the search capabilities.
    d = SimilarSearchDict(None, {1: "a", 2: "b", 3: "c"})
    for (k, v, item) in zip(d.keys(), d.values(), d.items()):
        assert any(k_iter == k for k_iter in d)
        assert (k, v) == item


def test_searchdict_update():
    # Make a blank dict, add new stuff from (k, v) tuples and keywords, and test it
    d = SimilarSearchDict()
    d.update([("a list", "yes"), ("of tuples", "okay")], but="add", some="keywords")
    assert d
    assert len(d) == 4
    assert d["a list"] == "yes"
    assert d["some"] == "keywords"
    # Add more items (some overwriting others) and see if it behaves correctly, then clear it.
    d.update([("a list", "still yes"), ("of sets", "nope")])
    assert len(d) == 5
    assert d["a list"] == "still yes"
    d.clear()
    assert not d
    assert len(d) == 0


def test_searchdict_values():
    # Strange values shouldn't break anything.
    d = SimilarSearchDict(None, {"x" * i: i for i in range(10)})
    d["func"] = len
    assert d["func"](d) == 11
    d["tuple"] = (("UNWRAP ME!",),)
    assert d["tuple"][0][0] == "UNWRAP ME!"
    d["recurse me!"] = d
    assert d["recurse me!"]["recurse me!"]["recurse me!"] is d
