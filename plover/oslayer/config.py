# Copyright (c) 2012 Hesky Fisher
# See LICENSE.txt for details.

"""Platform dependent configuration."""

import os
import sys
import sysconfig

import appdirs


# If plover is run from a pyinstaller binary.
if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
    PROGRAM_DIR = os.path.dirname(sys.executable)
# If plover is run from an app bundle on Mac.
elif sys.platform.startswith('darwin') and '.app' in os.path.realpath(__file__):
    PROGRAM_DIR = os.path.abspath(os.path.join(os.path.dirname(sys.executable), *[os.path.pardir] * 3))
else:
    PROGRAM_DIR = os.getcwd()

# If the program's directory has a plover.cfg file then run in "portable mode",
# i.e. store all data in the same directory. This allows keeping all Plover
# files in a portable drive.
if os.path.isfile(os.path.join(PROGRAM_DIR, 'plover.cfg')):
    CONFIG_DIR = PROGRAM_DIR
else:
    CONFIG_DIR = appdirs.user_data_dir('plover', 'plover')

# Setup plugins directory.
if sys.platform.startswith('darwin'):
    PLUGINS_PLATFORM = 'mac'
elif sys.platform.startswith('linux'):
    PLUGINS_PLATFORM = 'linux'
elif sys.platform.startswith('win'):
    PLUGINS_PLATFORM = 'win'
else:
    PLUGINS_PLATFORM = None
if PLUGINS_PLATFORM is None:
    PLUGINS_BASE = None
    PLUGINS_DIR = None
else:
    PLUGINS_BASE = os.path.join(CONFIG_DIR, 'plugins', PLUGINS_PLATFORM)
    scheme = '%s_user' % os.name
    if PLUGINS_PLATFORM == 'mac' and sysconfig.get_config_var('PYTHONFRAMEWORK'):
        scheme = 'osx_framework_user'
    PLUGINS_DIR = sysconfig.get_path('purelib', scheme, dict(userbase=PLUGINS_BASE))
    sys.path.insert(0, PLUGINS_DIR)

# This need to be imported after patching sys.path.
import pkg_resources

plover_dist = pkg_resources.get_distribution('plover')

ASSETS_DIR = plover_dist.get_resource_filename(__name__, 'plover/assets')

# Is support for the QT GUI available?
HAS_GUI_QT = True
for req in plover_dist.requires(('gui_qt',)):
    if pkg_resources.working_set.find(req) is None:
        HAS_GUI_QT = False
        break
