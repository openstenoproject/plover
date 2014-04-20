import unittest
import plover.dictionary.lookup_table
from plover.steno_dictionary import StenoDictionaryCollection

class TestCase(unittest.TestCase):

    def test_load(self):
        self.assertFalse(plover.dictionary.lookup_table.loaded)
        plover.dictionary.lookup_table.load(StenoDictionaryCollection())
        self.assertTrue(plover.dictionary.lookup_table.loaded)

    def test_lookup(self):
        self.assertEquals(None, plover.dictionary.lookup_table.lookup("this"))
        plover.dictionary.lookup_table.addToDictionary(["THEUS", "this"])
        self.assertEquals("THEUS", plover.dictionary.lookup_table.lookup("this"))

        plover.dictionary.lookup_table.addToDictionary(["TH", "this"])
        self.assertEquals("TH", plover.dictionary.lookup_table.lookup("this"))
        plover.dictionary.lookup_table.addToDictionary(["THEUS", "this"])
        self.assertEquals("TH", plover.dictionary.lookup_table.lookup("this"))

        plover.dictionary.lookup_table.addToDictionary(["THA", "that"])
        plover.dictionary.lookup_table.addToDictionary(["THEUS/WAEU", "this way"])
        plover.dictionary.lookup_table.addToDictionary(["THEUS/STK/THA", "this and that"])
        self.assertEquals(3, plover.dictionary.lookup_table.prefixMatch("this").qsize())
        self.assertEquals(4, plover.dictionary.lookup_table.prefixMatch("th").qsize())

        self.assertEquals(plover.dictionary.lookup_table.shortestOf(["BCD","EF","G"], None), ["BCD","EF","G"])
        self.assertEquals(plover.dictionary.lookup_table.shortestOf(None, "AAAL"), "AAAL")
        self.assertEquals(plover.dictionary.lookup_table.shortestOf("", ["ABC","DEFGHIJ"]), ["ABC","DEFGHIJ"])
        self.assertEquals(plover.dictionary.lookup_table.shortestOf(["BCD","EF","G"],""), ["BCD","EF","G"])
        self.assertEquals(plover.dictionary.lookup_table.shortestOf(["BCD","EF","G"], None), ["BCD","EF","G"])
        self.assertEquals(plover.dictionary.lookup_table.shortestOf(["ABC","DEFGHIJ"], ["BCD","EF","G"]), ["ABC","DEFGHIJ"])
        self.assertEquals(plover.dictionary.lookup_table.shortestOf(["BCD","EF","G"], ["ABC","DEFGHIJ"]), ["ABC","DEFGHIJ"])
        self.assertEquals(plover.dictionary.lookup_table.shortestOf(["BCD","EF"], ["ABC","DEFGHIJ"]), ["BCD","EF"])






