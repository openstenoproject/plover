#!/usr/bin/env python2
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

import os
import re
import shutil
import subprocess
import sys

from distutils import log
import pkg_resources
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

from utils.metadata import copy_metadata


package_name = __software_name__.capitalize()


def get_version():
    if not os.path.exists('.git'):
        return None
    version = subprocess.check_output('git describe --tags --match=v[0-9]*'.split()).strip()
    m = re.match(r'^v(\d[\d.]*)(-\d+-g[a-f0-9]*)?$', version)
    assert m is not None, version
    version = m.group(1)
    if m.group(2) is not None:
        version += '+' + m.group(2)[1:].replace('-', '.')
    return version


def pyinstaller(*args):
    py_args = [
        '--log-level=INFO',
        '--specpath=build',
        '--additional-hooks-dir=windows',
        '--paths=.',
        '--name=%s-%s' % (
            __software_name__.capitalize(),
            __version__,
        ),
        '--noconfirm',
        '--windowed',
        '--onefile'
    ]
    py_args.extend(args)
    py_args.append('plover/main.py')
    main = pkg_resources.load_entry_point('PyInstaller', 'console_scripts', 'pyinstaller')
    main(py_args)


class PyInstallerDist(setuptools.Command):

    user_options = []
    extra_args = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Make sure metadata are up-to-date first.
        self.run_command("egg_info")
        pyinstaller(*self.extra_args)


class BinaryDistWin(PyInstallerDist):
    description = 'create an executabe for MS Windows'
    extra_args = [
        '--icon=plover/assets/plover.ico',
    ]


class PatchVersion(setuptools.Command):

    description = 'patch package version from VCS'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        version = get_version()
        if version is None:
            sys.exit(1)
        log.info('patching version to %s', version)
        version_file = os.path.join('plover', '__init__.py')
        with open(version_file, 'r') as fp:
            contents = fp.read().split('\n')
        contents = [re.sub(r'^__version__ = .*$', "__version__ = '%s'" % version, line)
                    for line in contents]
        with open(version_file, 'w') as fp:
            fp.write('\n'.join(contents))


class TagWeekly(setuptools.Command):

    description = 'tag weekly version'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        version = get_version()
        if version is None:
            sys.exit(1)
        weekly_version = 'weekly-v%s' % version
        log.info('tagging as %s', weekly_version)
        subprocess.check_call('git tag -f'.split() + [weekly_version])


class BinaryDistApp(setuptools.Command):

    user_options = []
    extra_args = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Make sure metadata are up-to-date first.
        self.run_command('egg_info')
        self.run_command('py2app')
        app = 'dist/%s-%s.app' % (package_name, __version__)
        libdir = '%s/Contents/Resources/lib/python2.7' % app
        sitezip = '%s/site-packages.zip' % libdir
        # Add version to filename and strip other architectures.
        # (using py2app --arch is not enough).
        tmp_app = 'dist/%s.app' % package_name
        cmd = 'ditto --arch x86_64 %s %s' % (tmp_app, app)
        log.info('running %s', cmd)
        subprocess.check_call(cmd.split())
        shutil.rmtree(tmp_app)
        # We can't access package resources from the site zip,
        # so extract module and package data to the lib directory.
        cmd = 'unzip -d %s %s plover/*' % (libdir, sitezip)
        log.info('running %s', cmd)
        subprocess.check_call(cmd.split())
        cmd = 'zip -d %s plover/*' % sitezip
        log.info('running %s', cmd)
        subprocess.check_call(cmd.split())
        # Add packages metadata.
        copy_metadata('.', libdir)


cmdclass = {
    'patch_version': PatchVersion,
    'tag_weekly': TagWeekly,
}
setup_requires = []
options = {}
kwargs = {}

if sys.platform.startswith('darwin'):
    setup_requires.append('py2app')
    options['py2app'] = {
        'arch': 'x86_64',
        'argv_emulation': False,
        'iconfile': 'osx/plover.icns',
        'plist': {
            'CFBundleName': package_name,
            'CFBundleShortVersionString': __version__,
            'CFBundleVersion': __version__,
            'CFBundleIdentifier': 'org.openstenoproject.plover',
            'NSHumanReadableCopyright': __copyright__,
            'CFBundleDevelopmentRegion': 'English',
            }
        }
    # Py2app will not look at entry_points.
    kwargs['app'] = 'launch.py',
    cmdclass['bdist_app'] = BinaryDistApp

if sys.platform.startswith('win32'):
    setup_requires.append('PyInstaller==3.1.1')
    cmdclass['bdist_win'] = BinaryDistWin

setup_requires.extend(('pytest-runner', 'pytest'))
options['aliases'] = {
    'test': 'pytest --addopts -ra --addopts plover',
}

install_requires = [
    'setuptools',
    'pyserial>=2.7',
    'appdirs>=1.4.0',
    'hidapi',
]

extras_require = {
    ':"win32" in sys_platform': [
        'pyhook>=1.5.1',
        'pywin32>=219',
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

    if sys.argv[1] == 'write_requirements':
        write_requirements(extra_features=sys.argv[2:])
        sys.exit(0)

    setuptools.setup(
        name=package_name,
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
        cmdclass=cmdclass,
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
            'plover.system',
        ],
        package_data={
            'plover': ['assets/*'],
        },
        data_files=[
            ('share/applications', ['application/Plover.desktop']),
            ('share/pixmaps', ['plover/assets/plover.png']),
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

