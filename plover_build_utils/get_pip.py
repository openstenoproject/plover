#!/usr/bin/env python3

import os
import shutil
import sys
import zipfile

from .download import download
from .install_wheels import WHEELS_CACHE, install_wheels


PIP_VERSION = '25.0.1'
PIP_WHEEL_URL = 'https://files.pythonhosted.org/packages/c9/bc/b7db44f5f39f9d0494071bddae6880eb645970366d0a200022a1a93d57f5/pip-25.0.1-py3-none-any.whl'
PIP_INSTALL = os.path.join('.cache', 'pip', PIP_VERSION)


def get_pip(args=None):
    # Download the wheel.
    pip_wheel = download(PIP_WHEEL_URL, downloads_dir=WHEELS_CACHE)
    # "Install" it (can't run directly from it because of the PEP 517 code).
    if not os.path.exists(PIP_INSTALL):
        os.makedirs(PIP_INSTALL)
        # Extract it.
        with zipfile.ZipFile(pip_wheel) as z:
            z.extractall(PIP_INSTALL)
        # Get rid of the info metadata.
        shutil.rmtree(os.path.join(PIP_INSTALL, 'pip-%s.dist-info' % PIP_VERSION))
    # If no arguments where passed, or only options arguments,
    # automatically install pip / setuptools / wheel,
    # otherwise, let the caller be in charge.
    if args is None or not next((a for a in args if not a.startswith('-')), None):
        args = (args or []) + [pip_wheel, 'setuptools', 'wheel']
    # Run pip from the wheel we just got.
    install_wheels(args, pip_install=os.path.join(PIP_INSTALL, 'pip'))


if __name__ == '__main__':
    get_pip(sys.argv[1:])
