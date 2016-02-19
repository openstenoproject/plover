#!/usr/bin/env python2
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

import os
import re
import subprocess
import sys

import setuptools

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


class PatchVersion(setuptools.Command):

    description = 'patch package version from VCS'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pkgdir = os.path.dirname(__file__)
        if not os.path.exists(os.path.join(pkgdir, '.git')):
            return
        version = subprocess.check_output('git describe --tags --match=v[0-9]*'.split()).strip()
        m = re.match(r'^v(\d[\d.]*)(-\d+-g[a-f0-9]*)?$', version)
        assert m is not None, version
        version = m.group(1)
        if m.group(2) is not None:
            version += '+' + m.group(2)[1:].replace('-', '.')
        version_file = os.path.join(pkgdir, 'plover', '__init__.py')
        with open(version_file, 'r') as fp:
            contents = fp.read().split('\n')
        contents = [re.sub(r'^__version__ = .*$', "__version__ = '%s'" % version, line)
                    for line in contents]
        with open(version_file, 'w') as fp:
            fp.write('\n'.join(contents))


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

if sys.platform.startswith('win32'):
    setup_requires.append('PyInstaller==3.1.1')

setup_requires.extend(('pytest-runner', 'pytest'))
options['aliases'] = {
    'test': 'pytest --addopts -ra --addopts plover',
}

install_requires = [
    'setuptools',
    'pyserial>=2.7',
    'appdirs>=1.4.0',
]

extras_require = {
    ':"win32" in sys_platform': [
        'pyhook>=1.5.1',
        'pywin32>=219',
        'pywinusb>=0.4.0',
        # Can't reliably require wxPython
    ],
    ':"linux" in sys_platform': [
        'python-xlib>=0.14',
        'wxPython>=3.0',
        'hidapi',
    ],
    ':"darwin" in sys_platform': [
        'pyobjc-core>=3.0.3',
        'pyobjc-framework-Cocoa>=3.0.3',
        'pyobjc-framework-Quartz>=3.0.3',
        'wxPython>=3.0',
        'hidapi',
    ],
}

tests_require = [
    'mock',
]


def write_requirements(extra_features=()):
    requirements = setup_requires + install_requires + tests_require
    for feature, dependencies in extras_require.items():
        if feature.startswith(':'):
            condition = feature[1:]
            for require in dependencies:
                requirements.append('%s; %s' % (require, condition))
        elif feature in extra_features:
            requirements.extend(dependencies)
    with open('requirements.txt', 'w') as fp:
        fp.write('\n'.join(requirements))
        fp.write('\n')


if __name__ == '__main__':

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
        maintainer='Ted Morin',
        maintainer_email='morinted@gmail.com',
        zip_safe=True,
        options=options,
        cmdclass={
            'patch_version': PatchVersion,
        },
        setup_requires=setup_requires,
        install_requires=install_requires,
        extras_require=extras_require,
        tests_require=tests_require,
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

