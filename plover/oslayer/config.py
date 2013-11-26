# Copyright (c) 2012 Hesky Fisher
# See LICENSE.txt for details.

"""Platform dependent configuration."""

import appdirs
import os
from os.path import realpath, join, dirname, abspath, isfile, pardir
import sys


# If plover is run from a pyinstaller binary.
if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
    ASSETS_DIR = sys._MEIPASS
    PROGRAM_DIR = dirname(sys.executable)
# If plover is run from an app bundle on Mac.
elif (sys.platform.startswith('darwin') and '.app' in realpath(__file__)):
    ASSETS_DIR = os.getcwd()
    PROGRAM_DIR = abspath(join(dirname(sys.executable), *[pardir] * 3))
else:
    ASSETS_DIR = join(dirname(dirname(realpath(__file__))), 'assets')
    PROGRAM_DIR = os.getcwd()

# If the program's directory has a plover.cfg file then run in "portable mode",
# i.e. store all data in the same directory. This allows keeping all Plover
# files in a portable drive.
if isfile(join(PROGRAM_DIR, 'plover.cfg')):
    CONFIG_DIR = PROGRAM_DIR
else:
    CONFIG_DIR = appdirs.user_data_dir('plover', 'plover')
