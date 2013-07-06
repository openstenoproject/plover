# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for registry.py."""

import unittest
from registry import Registry, machine_registry, NoSuchMachineException

class RegistryClassTestCase(unittest.TestCase):
    def test_lookup(self):
        registry = Registry()
        registry.register('a', 1)
        self.assertEqual(1, registry.get('a'))
    
    def test_unknown_entry(self):
        registry = Registry()
        with self.assertRaises(NoSuchMachineException):
            registry.get('b')
            
    def test_alias(self):
        registry = Registry()
        registry.register('a', 1)
        registry.add_alias('b', 'a')
        self.assertEqual(registry.resolve_alias('b'), 'a')
        self.assertEqual(1, registry.get('b'))
            
    def test_all_names(self):
        registry = Registry()
        registry.register('a', 1)
        registry.register('b', 5)
        registry.add_alias('c', 'b')
        self.assertEqual(['a', 'b'], sorted(registry.get_all_names()))

class MachineRegistryTestCase(object):
    def test_sidewinder(self):
        self.assertEqual(machine_registery.get("NKRO Keyboard"), 
                         machine_registry.get('Microsoft Sidewinder X4'))

    def test_unknown_machine(self):
        with self.assertRaises(NoSuchMachineException):
            machine_registry.get('No such machine')

if __name__ == '__main__':
    unittest.main()
