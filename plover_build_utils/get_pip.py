#!/usr/bin/env python3

import os
import subprocess
import sys

from .download import download
from .install_wheels import WHEELS_CACHE, install_wheels


def get_pip(args=None):
    # Download `get-pip.py`.
    script = download('https://github.com/pypa/get-pip/raw/c394417beced07131645c83cd0a01d1adc8c149b/get-pip.py',
                      '19365b3d19b145dd9f94f8b55200aa2a0a3ec1cd')
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
