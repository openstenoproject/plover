import unittest
from tst import TST

class TestCase(unittest.TestCase):

    def test_put_get(self):
        tst = TST()
        self.assertEquals(0, len(tst))
        self.assertIsNone(tst.get("a"))
        tst.put("a", "a")
        self.assertEquals(1, len(tst))
        self.assertEquals("a", tst.get("a"))
        tst.put("b", "b")
        self.assertEquals(2, len(tst))
        self.assertEquals("a", tst.get("a"))
        self.assertEquals("b", tst.get("b"))
        tst.put("a", "new_a")
        self.assertEquals(2, len(tst))
        self.assertEquals("new_a", tst.get("a"))
        self.assertTrue(tst.contains("b"))
        self.assertFalse(tst.contains("ab"))


    def test_longest_prefix(self):
        tst = TST()
        tst.put("a", "A")
        tst.put("anterior", "ANTERIOR")
        tst.put("ant", "ANT")
        tst.put("aunt", "AUNT")
        self.assertEquals(tst.longestPrefixOf("auntie"), "aunt")
        self.assertEquals(tst.longestPrefixOf("ant"), "ant")
        self.assertEquals(tst.longestPrefixOf(""), "")
        self.assertEquals(tst.longestPrefixOf("b"), "")

    def test_prefix_match(self):
        tst = TST()
        tst.put("a", "A")
        tst.put("anterior", "ANTERIOR")
        tst.put("antidisassembly", "ANTIDISASSEMBLY")
        tst.put("ant", "ANT")
        tst.put("aunt", "AUNT")
        r = tst.prefixMatch("ant");
        self.assertEquals(r.qsize(), 3)
        self.assertEquals(r.get(), "ant")

        self.assertFalse(True)

