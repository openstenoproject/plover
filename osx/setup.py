#!/usr/bin/env python2.6
# Copyright (c) 2012 Hesky Fisher.
# See LICENSE.txt for details.

"""Build an Mac app for Plover.

Run with: python setup.py py2app
"""

import os
import shutil
import sys

from setuptools import setup

if sys.platform != 'darwin':
    raise Exception('This file is only meant to be used on OSX.')

# It's better to run inside the osx dir and keep all the output in here.
os.chdir(os.path.dirname(os.path.realpath(__file__)))

assets_dir = os.path.realpath('../plover/assets')
resources = ','.join('/'.join([assets_dir, x]) for x in os.listdir(assets_dir))

# py2app doesn't understand that a python script doesn't have to end in .py so
# we need to make a launch script for it.
launch_file = os.path.realpath('../launch.py')
shutil.copyfile(os.path.realpath('../application/plover'), launch_file)

setup(name='Plover',
      setup_requires=['py2app'],
      app=[launch_file],
      options = dict(py2app=dict(argv_emulation=True,
      iconfile='plover.icns',
      resources=resources))
      )