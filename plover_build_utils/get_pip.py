#!/usr/bin/env python3

import os
import subprocess
import sys

from .download import download
from .install_wheels import WHEELS_CACHE, install_wheels


def get_pip(args=None):
    # Download `get-pip.py`.
    script = download('https://github.com/pypa/get-pip/raw/69941dc3ee6a2562d873f8616a4df31ba401b2a9/get-pip.py',
                      '29295f4181a2a3df9539dcf1cebc2079da569320')
    # Make sure wheels cache directory exists to avoid warning.
    if not os.path.exists(WHEELS_CACHE):
        os.makedirs(WHEELS_CACHE)
    # Install pip/wheel...
    get_pip_cmd = [sys.executable, script, '-f', WHEELS_CACHE]
    if args is not None:
        get_pip_cmd.extend(args)
    subprocess.check_call(get_pip_cmd)
    # ...and cache them for the next iteration (if possible).
    try:
        import wheel
    except ImportError:
        pass
    else:
        install_wheels(['--no-install', 'pip', 'wheel'])


if __name__ == '__main__':
    get_pip(sys.argv[1:])
