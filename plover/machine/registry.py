# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"Manager for stenotype machines types."

from plover import log


class NoSuchMachineException(Exception):
    def __init__(self, id):
        self._id = id

    def __str__(self):
        return 'Unrecognized machine type: {}'.format(self._id)

class Registry(object):
    def __init__(self):
        self._machines = {}
        self._aliases = {}

    def register(self, name, import_spec_or_class):
        self._machines[name] = import_spec_or_class

    def add_alias(self, alias, name):
        self._aliases[alias] = name

    def get(self, name):
        try:
            import_spec_or_class = self._machines[self.resolve_alias(name)]
        except KeyError:
            raise NoSuchMachineException(name)
        if isinstance(import_spec_or_class, basestring):
            mod_name, class_name = import_spec_or_class.rsplit('.', 1)
            mod = __import__(mod_name, globals(), locals(), (class_name,))
            return getattr(mod, class_name)
        else:
            return import_spec_or_class

    def get_all_names(self):
        return self._machines.keys()
        
    def resolve_alias(self, name):
        try:
            return self._aliases[name]
        except KeyError:
            return name

machine_registry = Registry()
for name, import_spec in (
    ('NKRO Keyboard', 'sidewinder.Stenotype'),
    ('Gemini PR'    , 'geminipr.Stenotype'  ),
    ('TX Bolt'      , 'txbolt.Stenotype'    ),
    ('Stentura'     , 'stentura.Stenotype'  ),
    ('Passport'     , 'passport.Stenotype'  ),
    ('Treal'        , 'treal.Stenotype'     ),
):
    machine_registry.register(name, 'plover.machine.%s' % import_spec)

machine_registry.add_alias('Microsoft Sidewinder X4', 'NKRO Keyboard')

