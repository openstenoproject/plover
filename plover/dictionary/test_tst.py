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
        self.assertEquals(r.get(), "anterior")
        self.assertEquals(r.get(), "antidisassembly")
        r = tst.prefixMatch("bob");
        self.assertEquals(r.qsize(), 0)
        r = tst.prefixMatch("aunt");
        self.assertEquals(r.qsize(), 1)
        r = tst.prefixMatch("auntie")
        self.assertEquals(r.qsize(), 0)

    def test_delete(self):
        tst = TST()
        tst.put("a", "A")
        self.assertEquals(1, len(tst))
        self.assertEquals("A", tst.get("a"))
        tst.delete("b")
        self.assertEquals(1, len(tst))
        tst.delete("a")
        self.assertEquals(1, len(tst))
        self.assertIsNone(tst.get("a"))


