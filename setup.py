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
)

import setuptools

setuptools.setup(
    name=__software_name__.capitalize(),
    version=__version__,
    description=__description__,
    long_description=__long_description__,
    url=__url__,
    download_url=__download_url__,
    license=__license__,
    author='Joshua Harlan Lifton',
    author_email='joshua.harlan.lifton@gmail.com',
    maintainer='Joshua Harlan Lifton',
    maintainer_email='joshua.harlan.lifton@gmail.com',
    zip_safe=True,
    install_requires=[
        'setuptools',
        'pyserial>=2.7',
        'appdirs>=1.4.0',
        # Don't add wxPython because it cannot be installed through PIP,
        # and may not appears as present when it is installed (Windows...).
        # 'wxPython>=2.8',
    ],
    extras_require={
        ':"win32" in sys_platform': [
            'pyhook>=1.5.1',
            'pywin32>=219',
            'pywinauto>=0.5.3',
            'pywinusb>=0.4.0',
        ],
        ':"linux" in sys_platform': [
            'python-xlib>=0.14',
            'wxPython>=2.8',
        ],
    },
    entry_points={
        'console_scripts' : ['plover=plover.main:main'],
        'setuptools.installation' : ['eggsecutable=plover.main:main'],
    },
    packages=[
        'plover', 'plover.machine', 'plover.gui',
        'plover.oslayer', 'plover.dictionary',
    ],
    package_data={
        'plover' : ['assets/*'],
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
)
