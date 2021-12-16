from collections import namedtuple

import importlib_metadata

from plover.oslayer.config import PLUGINS_PLATFORM
from plover import log


class Plugin(namedtuple('Plugin', 'plugin_type name obj')):

    @property
    def __doc__(self):
        return self.obj.__doc__ or ''


PluginDistribution = namedtuple('PluginDistribution', 'name version plugins')


class Registry:

    PLUGIN_TYPES = (
        'command',
        'dictionary',
        'extension',
        'gui',
        'gui.qt.machine_option',
        'gui.qt.tool',
        'machine',
        'macro',
        'meta',
        'system',
    )

    def __init__(self, suppress_errors=True):
        self._plugins = {}
        self._distributions = {}
        self._suppress_errors = suppress_errors
        for plugin_type in self.PLUGIN_TYPES:
            self._plugins[plugin_type] = {}

    def register_plugin(self, plugin_type, name, obj):
        plugin = Plugin(plugin_type, name, obj)
        self._plugins[plugin_type][name.lower()] = plugin
        return plugin

    def register_plugin_from_entrypoint(self, plugin_type, entrypoint):
        log.info('%s: %s (from %s-%s in %s)', plugin_type, entrypoint.name,
                 entrypoint.dist.name, entrypoint.dist.version,
                 entrypoint.dist.locate_file('.'))
        try:
            obj = entrypoint.load()
        except:
            log.error('error loading %s plugin: %s (from %s)', plugin_type,
                      entrypoint.name, entrypoint.module, exc_info=True)
            if not self._suppress_errors:
                raise
        else:
            plugin = self.register_plugin(plugin_type, entrypoint.name, obj)
            # Keep track of distributions providing plugins.
            dist_id = f'{entrypoint.dist.name} {entrypoint.dist.version}'
            dist = self._distributions.get(dist_id)
            if dist is None:
                dist = PluginDistribution(entrypoint.dist.name,
                                          entrypoint.dist.version,
                                          set())
                self._distributions[dist_id] = dist
            dist.plugins.add(plugin)

    def get_plugin(self, plugin_type, plugin_name):
        return self._plugins[plugin_type][plugin_name.lower()]

    def list_plugins(self, plugin_type):
        return sorted(self._plugins[plugin_type].values(),
                      key=lambda p: p.name)

    def list_distributions(self):
        return [dist for dist_id, dist in sorted(self._distributions.items())]

    def update(self):
        all_entrypoints = importlib_metadata.entry_points()
        # Is support for the QT GUI available?
        try:
            all_entrypoints.select(group='plover.gui', name='qt')['qt'].load()
        except ImportError:
            has_gui_qt = False
        else:
            has_gui_qt = True
        # Register available plugins.
        for plugin_type in self.PLUGIN_TYPES:
            if plugin_type.startswith('gui.qt.') and not has_gui_qt:
                continue
            entrypoint_type = f'plover.{plugin_type}'
            for entrypoint in all_entrypoints.select(group=entrypoint_type):
                if 'gui_qt' in entrypoint.extras and not has_gui_qt:
                    # Ignore GUI specific entry points if it's no available.
                    continue
                self.register_plugin_from_entrypoint(plugin_type, entrypoint)
            if PLUGINS_PLATFORM is None:
                continue
            entrypoint_type = f'plover.{PLUGINS_PLATFORM}.{plugin_type}'
            for entrypoint in all_entrypoints.select(group=entrypoint_type):
                self.register_plugin_from_entrypoint(plugin_type, entrypoint)


registry = Registry()
