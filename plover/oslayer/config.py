# Copyright (c) 2012 Hesky Fisher
# See LICENSE.txt for details.

"""Platform dependent configuration."""

import appdirs
import os.path
import sys

# If plover is run from a pyinstaller binary.
if hasattr(sys, 'frozen'):
    ASSETS_DIR = sys._MEIPASS
# If plover is run from an app bundle on Mac.
elif sys.platform.startswith('darwin') and '.app' in os.path.realpath(__file__):
    ASSETS_DIR = os.getcwd()
else:
    ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'assets')

CONFIG_DIR = appdirs.user_data_dir('plover', 'plover')
