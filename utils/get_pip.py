#!/usr/bin/env python3

import os
import subprocess
import sys

from utils.download import download
from utils.install_wheels import WHEELS_CACHE, install_wheels


def get_pip(args=None):
    # Download `get-pip.py`.
    script = download('https://bootstrap.pypa.io/get-pip.py?test=arg',
                      '3d45cef22b043b2b333baa63abaa99544e9c031d')
    # Make sure wheels cache directory exists to avoid warning.
    if not os.path.exists(WHEELS_CACHE):
        os.makedirs(WHEELS_CACHE)
    # Install pip/wheel...
    get_pip_cmd = [sys.executable, script, '-f', WHEELS_CACHE]
    if args is not None:
        get_pip_cmd.extend(args)
    subprocess.check_call(get_pip_cmd)
    # ...and cache them for the next iteration.
    install_wheels(['--no-install', 'pip', 'wheel'])


if __name__ == '__main__':
    get_pip(sys.argv[1:])
