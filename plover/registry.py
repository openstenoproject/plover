
import sys
import os

import pkg_resources

from plover.oslayer.config import CONFIG_DIR
from plover import log


PLUGINS_DIR = os.path.join(CONFIG_DIR, 'plugins')

if sys.platform.startswith('darwin'):
    PLUGINS_PLATFORM = 'mac'
elif sys.platform.startswith('linux'):
    PLUGINS_PLATFORM = 'linux'
elif sys.platform.startswith('win'):
    PLUGINS_PLATFORM = 'win'
else:
    PLUGINS_PLATFORM = None


class Plugin(object):

    def __init__(self, plugin_type, name, obj):
        self.plugin_type = plugin_type
        self.name = name
        self.obj = obj
        self.__doc__ = obj.__doc__ or ''

    def __str__(self):
        return '%s:%s' % (self.plugin_type, self.name)


class Registry(object):

    PLUGIN_TYPES = (
        'command',
        'dictionary',
        'extension',
        'gui',
        'gui.qt.tool',
        'machine',
        'system',
    )

    def __init__(self):
        self._plugins = {}
        for plugin_type in self.PLUGIN_TYPES:
            self._plugins[plugin_type] = {}

    def register_plugin(self, plugin_type, name, obj):
        plugin = Plugin(plugin_type, name, obj)
        self._plugins[plugin_type][name.lower()] = plugin

    def register_plugin_from_entrypoint(self, plugin_type, entrypoint):
        log.info('%s: %s (from %s)', plugin_type,
                 entrypoint.name, entrypoint.module_name)
        try:
            obj = entrypoint.resolve()
        except:
            log.error('error loading %s plugin: %s (from %s)', plugin_type,
                      entrypoint.name, entrypoint.module_name, exc_info=True)
        else:
            self.register_plugin(plugin_type, entrypoint.name, obj)

    def get_plugin(self, plugin_type, plugin_name):
        return self._plugins[plugin_type][plugin_name.lower()]

    def list_plugins(self, plugin_type):
        return sorted(self._plugins[plugin_type].values(),
                      key=lambda p: p.name)

    def load_plugins(self, plugins_dir=PLUGINS_DIR):
        log.info('loading plugins from %s', plugins_dir)
        working_set = pkg_resources.working_set
        environment = pkg_resources.Environment([plugins_dir])
        distributions, errors = working_set.find_plugins(environment)
        if errors:
            log.error("error(s) while loading plugins: %s", errors)
        list(map(working_set.add, distributions))

    def update(self):
        for plugin_type in self.PLUGIN_TYPES:
            entrypoint_type = 'plover.%s' % plugin_type
            for entrypoint in pkg_resources.iter_entry_points(entrypoint_type):
                self.register_plugin_from_entrypoint(plugin_type, entrypoint)
            if PLUGINS_PLATFORM is not None:
                entrypoint_type = 'plover.%s.%s' % (PLUGINS_PLATFORM, plugin_type)
                for entrypoint in pkg_resources.iter_entry_points(entrypoint_type):
                    self.register_plugin_from_entrypoint(plugin_type, entrypoint)


registry = Registry()

