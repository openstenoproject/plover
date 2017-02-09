
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

    def register_plugin(self, plugin_type, entrypoint):
        log.info('%s: %s (from %s)', plugin_type,
                 entrypoint.name, entrypoint.module_name)
        self._plugins[plugin_type][entrypoint.name.lower()] = entrypoint

    def get_plugin(self, plugin_type, plugin_name):
        return self._plugins[plugin_type][plugin_name.lower()]

    def list_plugins(self, plugin_type):
        return [
            entrypoint.name
            for entrypoint in self._plugins[plugin_type].values()
        ]

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
                self.register_plugin(plugin_type, entrypoint)
            if PLUGINS_PLATFORM is not None:
                entrypoint_type = 'plover.%s.%s' % (PLUGINS_PLATFORM, plugin_type)
                for entrypoint in pkg_resources.iter_entry_points(entrypoint_type):
                    self.register_plugin(plugin_type, entrypoint)


registry = Registry()

