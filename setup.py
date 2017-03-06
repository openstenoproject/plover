#!/usr/bin/env python2
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

import contextlib
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


# Don't use six to avoid dependency with 'write_requirements' command.
PY3 = sys.version_info[0] >= 3

PACKAGE = '%s-%s-%s' % (
    __software_name__,
    __version__,
    'py3' if PY3 else 'py2',
)


def get_version():
    if not os.path.exists('.git'):
        return None
    version = subprocess.check_output('git describe --tags --match=v[0-9]*'.split()).strip().decode()
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
        '--name=%s' % PACKAGE,
        '--noconfirm',
        '--windowed',
        '--onefile',
    ]
    py_args.extend(args)
    py_args.append('windows/main.py')
    main = pkg_resources.load_entry_point('PyInstaller', 'console_scripts', 'pyinstaller')
    return main(py_args) or 0


class Command(setuptools.Command):

    def build_in_place(self):
        self.run_command('build_py')
        self.reinitialize_command('build_ext', inplace=1)
        self.run_command('build_ext')

    @contextlib.contextmanager
    def project_on_sys_path(self):
        self.build_in_place()
        ei_cmd = self.get_finalized_command("egg_info")
        old_path = sys.path[:]
        old_modules = sys.modules.copy()
        try:
            sys.path.insert(0, pkg_resources.normalize_path(ei_cmd.egg_base))
            pkg_resources.working_set.__init__()
            pkg_resources.add_activation_listener(lambda dist: dist.activate())
            pkg_resources.require('%s==%s' % (ei_cmd.egg_name, ei_cmd.egg_version))
            yield
        finally:
            sys.path[:] = old_path
            sys.modules.clear()
            sys.modules.update(old_modules)
            pkg_resources.working_set.__init__()


class PyInstallerDist(Command):

    user_options = []
    extra_args = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.build_in_place()
        code = pyinstaller(*self.extra_args)
        if code != 0:
            sys.exit(code)


class BinaryDistWin(PyInstallerDist):
    description = 'create an executable for MS Windows'
    extra_args = [
        '--icon=plover/assets/plover.ico',
    ]


class Launch(Command):

    description = 'run %s from source' % __software_name__.capitalize()
    command_consumes_arguments = True
    user_options = []

    def initialize_options(self):
        self.args = None

    def finalize_options(self):
        pass

    def run(self):
        with self.project_on_sys_path():
            from plover.main import main
            sys.argv = [' '.join(sys.argv[0:2]) + ' --'] + self.args
            sys.exit(main())


class PatchVersion(Command):

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


class TagWeekly(Command):

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


class Test(Command):

    description = 'run unit tests after in-place build'
    command_consumes_arguments = True
    user_options = []

    def initialize_options(self):
        self.args = []

    def finalize_options(self):
        pass

    def run(self):
        with self.project_on_sys_path():
            self.run_tests()

    def run_tests(self):
        test_dir = os.path.join(os.path.dirname(__file__), 'test')
        # Remove __pycache__ directory so pytest does not freak out
        # when switching between the Linux/Windows versions.
        pycache = os.path.join(test_dir, '__pycache__')
        if os.path.exists(pycache):
            shutil.rmtree(pycache)
        custom_testsuite = None
        args = []
        for a in self.args:
            if '-' == a[0]:
                args.append(a)
            elif os.path.exists(a):
                custom_testsuite = a
                args.append(a)
            else:
                args.extend(('-k', a))
        if custom_testsuite is None:
            args.insert(0, test_dir)
        sys.argv[1:] = args
        main = pkg_resources.load_entry_point('pytest',
                                              'console_scripts',
                                              'py.test')
        sys.exit(main())


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
        app = 'dist/%s.app' % PACKAGE
        libdir = '%s/Contents/Resources/lib/python2.7' % app
        sitezip = '%s/site-packages.zip' % libdir
        # Add version to filename and strip other architectures.
        # (using py2app --arch is not enough).
        tmp_app = 'dist/%s.app' % __software_name__
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


class BinaryDistDmg(Command):

    user_options = []
    extra_args = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('bdist_app')
        app = 'dist/%s.app' % PACKAGE
        dmg = 'dist/%s.dmg' % PACKAGE
        cmd = 'bash -x osx/app2dmg.sh %s %s' % (app, dmg)
        log.info('running %s', cmd)
        subprocess.check_call(cmd.split())


cmdclass = {
    'launch': Launch,
    'patch_version': PatchVersion,
    'tag_weekly': TagWeekly,
    'test': Test,
}
setup_requires = ['setuptools-scm']
options = {}
kwargs = {}

if sys.platform.startswith('darwin'):
    setup_requires.append('py2app')
    options['py2app'] = {
        'arch': 'x86_64',
        'argv_emulation': False,
        'iconfile': 'osx/plover.icns',
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
    kwargs['app'] = 'plover/main.py',
    cmdclass['bdist_app'] = BinaryDistApp
    cmdclass['bdist_dmg'] = BinaryDistDmg

if sys.platform.startswith('win32'):
    setup_requires.append('PyInstaller==3.1.1')
    cmdclass['bdist_win'] = BinaryDistWin

setup_requires.append('pytest')

dependency_links = [
   'https://github.com/benoit-pierre/pyobjc/releases/download/pyobjc-3.1.1+plover2/pyobjc-core-3.1.1-plover2.tar.gz#egg=pyobjc-core',
   'https://github.com/benoit-pierre/pyobjc/releases/download/pyobjc-3.1.1+plover2/pyobjc-framework-Cocoa-3.1.1-plover2.tar.gz#egg=pyobjc-framework-Cocoa',
]

install_requires = [
    'six',
    'setuptools',
    'pyserial>=2.7',
    'appdirs>=1.3.0',
    'hidapi',
]

extras_require = {
    ':"win32" in sys_platform': [
    ],
    ':"linux" in sys_platform': [
        'python-xlib>=0.16',
    ],
    ':"darwin" in sys_platform': [
        'pyobjc-core==3.1.1+plover2',
        'pyobjc-framework-Cocoa==3.1.1+plover2',
        'pyobjc-framework-Quartz==3.1.1',
        'appnope>=0.1.0',
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
    requirements = sorted(set(requirements))
    with open('requirements.txt', 'w') as fp:
        fp.write('\n'.join(requirements))
        fp.write('\n')
    with open('requirements_constraints.txt', 'w') as fp:
        fp.write('\n'.join(dependency_links))
        fp.write('\n')


if __name__ == '__main__':

    if len(sys.argv) > 1 and sys.argv[1] == 'write_requirements':
        write_requirements(extra_features=sys.argv[2:])
        sys.exit(0)

    setuptools.setup(
        name=__software_name__,
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
        include_package_data=True,
        zip_safe=True,
        options=options,
        cmdclass=cmdclass,
        setup_requires=setup_requires,
        install_requires=install_requires,
        extras_require=extras_require,
        tests_require=tests_require,
        dependency_links=dependency_links,
        entry_points={
            'console_scripts': ['plover=plover.main:main'],
            'setuptools.installation': ['eggsecutable=plover.main:main'],
        },
        packages=[
            'plover', 'plover.machine', 'plover.gui',
            'plover.oslayer', 'plover.dictionary',
            'plover.system',
        ],
        data_files=[
            ('share/applications', ['application/Plover.desktop']),
            ('share/pixmaps', ['plover/assets/plover.png']),
        ],
        classifiers=[
            'Programming Language :: Python :: 2.7',
            'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
            'Development Status :: 5 - Production/Stable',
            'Environment :: X11 Applications',
            'Environment :: MacOS X',
            'Environment :: Win32 (MS Windows)',
            'Intended Audience :: End Users/Desktop',
            'Natural Language :: English',
            'Operating System :: POSIX :: Linux',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Topic :: Adaptive Technologies',
            'Topic :: Desktop Environment',
        ],
        **kwargs
    )

