# Copyright (c) 2012 Hesky Fisher
# See LICENSE.txt for details.

"""Platform dependent configuration."""

import appdirs
import os.path
import sys

# If plover is run from a pyinstaller binary that is frozen then the working directory is in the environment variable _MEIPASS2.
if hasattr(sys, 'frozen'):
    if '_MEIPASS2' in os.environ:
        ASSETS_DIR = os.environ['_MEIPASS2']
    else:
        ASSETS_DIR = os.path.dirname(sys.executable)
else:
    ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'assets')

CONFIG_DIR = appdirs.user_data_dir('plover', 'plover')
