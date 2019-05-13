# Copyright (c) 2012 Hesky Fisher
# See LICENSE.txt for details.

"""Platform dependent configuration."""

import os
import sys

import appdirs
import pkg_resources


# If the program's working directory has a plover.cfg file then run in
# "portable mode", i.e. store all data in the same directory. This allows
# keeping all Plover files in a portable drive.
#
# Note: the special case when run from an app bundle on macOS.
if sys.platform.startswith('darwin') and '.app/' in os.path.realpath(__file__):
    PROGRAM_DIR = os.path.abspath(os.path.join(os.path.dirname(sys.executable),
                                               *[os.path.pardir] * 3))
else:
    PROGRAM_DIR = os.getcwd()

# Setup configuration directory.
CONFIG_BASENAME = 'plover.cfg'
if os.path.isfile(os.path.join(PROGRAM_DIR, CONFIG_BASENAME)):
    CONFIG_DIR = PROGRAM_DIR
else:
    config_directories = [
        getattr(appdirs, directory_type)('plover')
        for directory_type in ('user_config_dir', 'user_data_dir')
    ]
    for CONFIG_DIR in config_directories:
        if os.path.isfile(os.path.join(CONFIG_DIR, CONFIG_BASENAME)):
            break
    else:
        CONFIG_DIR = config_directories[0]
CONFIG_FILE = os.path.join(CONFIG_DIR, CONFIG_BASENAME)

# Setup plugins directory.
if sys.platform.startswith('darwin'):
    PLUGINS_PLATFORM = 'mac'
elif sys.platform.startswith('linux'):
    PLUGINS_PLATFORM = 'linux'
elif sys.platform.startswith('win'):
    PLUGINS_PLATFORM = 'win'
else:
    PLUGINS_PLATFORM = None

plover_dist = pkg_resources.working_set.by_key['plover']

ASSETS_DIR = plover_dist.get_resource_filename(__name__, 'plover/assets')

# Is support for the QT GUI available?
HAS_GUI_QT = True
for req in plover_dist.requires(('gui_qt',)):
    if pkg_resources.working_set.find(req) is None:
        HAS_GUI_QT = False
        break
