# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"Manager for stenotype machines types."

from plover.machine.geminipr import GeminiPr
from plover.machine.txbolt import TxBolt
from plover.machine.keyboard import Keyboard
from plover.machine.stentura import Stentura
from plover.machine.passport import Passport
from plover.machine.procat import ProCAT
from plover.machine.treal import Treal

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

    def add_alias(self, alias, name):
        self._aliases[alias] = name

    def get(self, name):
        try:
            return self._machines[self.resolve_alias(name)]
        except KeyError:
            raise NoSuchMachineException(name)

    def get_all_names(self):
        return self._machines.keys()
        
    def resolve_alias(self, name):
        try:
            return self._aliases[name]
        except KeyError:
            return name

machine_registry = Registry()
machine_registry.register('Keyboard', Keyboard)
machine_registry.register('Gemini PR', GeminiPr)
machine_registry.register('TX Bolt', TxBolt)
machine_registry.register('Stentura', Stentura)
machine_registry.register('Passport', Passport)
machine_registry.register('ProCAT', ProCAT)
machine_registry.register('Treal', Treal)

# Legacy configuration
machine_registry.add_alias('Microsoft Sidewinder X4', 'Keyboard')
machine_registry.add_alias('NKRO Keyboard', 'Keyboard')

