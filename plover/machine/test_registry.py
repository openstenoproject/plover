# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for registry.py."""

import unittest
from plover.machine.registry import Registry, machine_registry, NoSuchMachineException

class OneMachine(object):
    pass

class AnotherMachine(object):
    pass

class RegistryClassTestCase(unittest.TestCase):
    def test_lookup(self):
        registry = Registry()
        registry.register('a', OneMachine)
        self.assertEqual(OneMachine, registry.get('a'))
    
    def test_unknown_entry(self):
        registry = Registry()
        with self.assertRaises(NoSuchMachineException):
            registry.get('b')
            
    def test_alias(self):
        registry = Registry()
        registry.register('a', OneMachine)
        registry.add_alias('b', 'a')
        self.assertEqual(registry.resolve_alias('b'), 'a')
        self.assertEqual(OneMachine, registry.get('b'))
            
    def test_all_names(self):
        registry = Registry()
        registry.register('a', OneMachine)
        registry.register('b', AnotherMachine)
        registry.add_alias('c', 'b')
        self.assertEqual(['a', 'b'], sorted(registry.get_all_names()))

    def test_unknown_machine(self):
        with self.assertRaises(NoSuchMachineException):
            machine_registry.get('No such machine')

if __name__ == '__main__':
    unittest.main()
