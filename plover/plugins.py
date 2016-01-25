
import pkg_resources
import glob
import sys
import os

from plover.oslayer.config import CONFIG_DIR


def load_plugins():
    plugins_dir = os.path.join(CONFIG_DIR, 'plugins')
    print 'loading plugins from', plugins_dir
    if os.path.exists(plugins_dir):
        for egg in glob.iglob(os.path.join(plugins_dir, '*.egg')):
            print 'loading plugin', os.path.basename(egg)
            sys.path.insert(0, egg)
            pkg_resources.working_set.add_entry(egg)

def get_systems():
    return {
        entrypoint.name: entrypoint
        for entrypoint in
        pkg_resources.iter_entry_points('plover.plugins.system')
    }

def get_dictionaries():
    return {
        entrypoint.name: entrypoint
        for entrypoint in
        pkg_resources.iter_entry_points('plover.plugins.dictionary')
    }

