
from plover import log

from plover.plugins_manager import global_registry, local_registry


class PackageState:

    def __init__(self, name, installed=None, available=None):
        self.name = name
        self.installed = installed or []
        self.available = available or []
        self.status = 'installed' if installed else ''

    @property
    def current(self):
        return self.installed[-1] if self.installed else None

    @current.setter
    def current(self, metadata):
        self.installed.append(metadata)
        self.status = 'removed' if metadata is None else 'updated'

    @property
    def latest(self):
        return self.available[-1] if self.available else None

    @property
    def metadata(self):
        return self.current or self.latest

    def __getattr__(self, name):
        return getattr(self.metadata, name)

    def __str__(self):
        s = self.name
        if self.latest:
            s += ' ' + self.latest.version
        if self.current:
            s += ' [' + self.status + ' ' + self.current.version + ']'
        return s

    def __lt__(self, other):
        return self.name < other.name

    def __repr__(self):
        return str(self)


class Registry:

    def __init__(self):
        self._packages = {
            name: PackageState(name, installed=metadata)
            for name, metadata in local_registry.list_plugins().items()
        }

    def __len__(self):
        return len(self._packages)

    def __contains__(self, name):
        return name in self._packages

    def __getitem__(self, name):
        return self._packages[name]

    def __iter__(self):
        return iter(self._packages.values())

    def keys(self):
        return self._packages.keys()

    def items(self):
        return self._packages.items()

    def update(self):
        try:
            available_plugins = global_registry.list_plugins()
        except:
            log.error("failed to fetch list of available plugins from PyPI",
                      exc_info=True)
            return
        for name, metadata in available_plugins.items():
            pkg = self._packages.get(name)
            if pkg is None:
                pkg = PackageState(name, available=metadata)
                self._packages[name] = pkg
            else:
                pkg.available = metadata
                if pkg.current and pkg.current.parsed_version < pkg.latest.parsed_version:
                    pkg.status = 'outdated'
