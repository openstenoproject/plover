# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"Manager for stenotype machines types."

from plover.machine.geminipr import Stenotype as geminipr
from plover.machine.txbolt import Stenotype as txbolt
from plover.machine.sidewinder import Stenotype as sidewinder
from plover.machine.stentura import Stenotype as stentura
try:
    from plover.machine.treal import Stenotype as treal
except:
    treal = None

class NoSuchMachineException(Exception):
    def __init__(self, id):
        self._id = id

    def __str__(self):
        return 'Unrecognized machine type: {}'.format(self._id)

class Registry(object):
    def __init__(self):
        self._machines = {}
        self._aliases = {}

    def register(self, name, machine):
        self._machines[name] = machine

    def add_alias(self, name, machine):
        self._aliases[name] = machine

    def get(self, name):
        try:
            return self._machines[name]
        except KeyError:
            pass
        try:
            return self._aliases[name]
        except KeyError:
            raise NoSuchMachineException(name)

    def get_all_names(self):
        return self._machines.keys()

machine_registry = Registry()
machine_registry.register('NKRO Keyboard', sidewinder)
machine_registry.register('Gemini PR', geminipr)
machine_registry.register('TX Bolt', txbolt)
machine_registry.register('Stentura', stentura)
if treal:
    machine_registry.register('Treal', treal)

machine_registry.add_alias('Microsoft Sidewinder X4', sidewinder)
