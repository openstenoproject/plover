#!/usr/bin/env python2
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

from plover import (
    __name__ as __software_name__,
    __version__,
    __description__,
    __long_description__,
    __url__,
    __download_url__,
    __license__,
    __copyright__,
)

import os
import sys
import setuptools

setup_requires = []
options = {}
kwargs = {}

if sys.platform.startswith('darwin'):
    setup_requires.append('py2app')
    options['py2app'] = {
        'argv_emulation': False,
        'iconfile': 'osx/plover.icns',
        'resources': 'plover/assets/',
        'plist': {
            'CFBundleName': __software_name__.capitalize(),
            'CFBundleShortVersionString': __version__,
            'CFBundleVersion': __version__,
            'CFBundleIdentifier': 'org.openstenoproject.plover',
            'NSHumanReadableCopyright': __copyright__,
            'CFBundleDevelopmentRegion': 'English',
            }
        }
    # Py2app will not look at entry_points.
    kwargs['app'] = 'launch.py',

setuptools.setup(
    name=__software_name__.capitalize(),
    version=os.environ.get('PLOVER_VERSION', __version__),
    description=__description__,
    long_description=__long_description__,
    url=__url__,
    download_url=__download_url__,
    license=__license__,
    author='Joshua Harlan Lifton',
    author_email='joshua.harlan.lifton@gmail.com',
    maintainer='Ted Morin',
    maintainer_email='morinted@gmail.com',
    zip_safe=True,
    options=options,
    setup_requires=setup_requires,
    install_requires=[
        'setuptools',
        'pyserial>=2.7',
        'appdirs>=1.4.0',
    ],
    extras_require={
        ':"win32" in sys_platform': [
            'pyhook>=1.5.1',
            'pywin32>=219',
            'pywinusb>=0.4.0',
            # Can't reliably require wxPython
        ],
        ':"linux" in sys_platform': [
            'python-xlib>=0.14',
            'wxPython>=3.0',
        ],
        ':"darwin" in sys_platform': [
            'pyobjc-core>=3.0.3',
            'pyobjc-framework-Cocoa>=3.0.3',
            'pyobjc-framework-Quartz>=3.0.3',
            'wxPython>=3.0',
        ],
    },
    entry_points={
        'console_scripts': ['plover=plover.main:main'],
        'setuptools.installation': ['eggsecutable=plover.main:main'],
    },
    packages=[
        'plover', 'plover.machine', 'plover.gui',
        'plover.oslayer', 'plover.dictionary',
    ],
    package_data={
        'plover': ['assets/*'],
    },
    data_files=[
        ('share/applications', ['application/Plover.desktop']),
        ('share/pixmaps', ['plover/assets/plover_on.png']),
    ],
    platforms=[
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
    ],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Topic :: Adaptive Technologies',
        'Topic :: Desktop Environment',
    ],
    **kwargs
)
