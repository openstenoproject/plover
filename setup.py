#!/usr/bin/env python3
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

from distutils import log
from distutils.errors import DistutilsModuleError
import os
import re
import subprocess
import sys

from setuptools import setup

sys.path.insert(0, os.path.dirname(__file__))

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

from plover_build_utils.setup import (
    BuildPy, BuildUi, Command, Test,
)


BuildPy.build_dependencies.append('build_ui')
Test.build_before = False
cmdclass = {
    'build_py': BuildPy,
    'build_ui': BuildUi,
    'test': Test,
}
options = {}

PACKAGE = '%s-%s' % (
    __software_name__,
    __version__,
)

# Helpers. {{{

def get_version():
    if not os.path.exists('.git'):
        return None
    version = subprocess.check_output('git describe --tags --match=v[0-9]*'.split()).strip().decode()
    m = re.match(r'^v(\d[\d.]*(?:\.dev\d+)?)(-\d+-g[a-f0-9]*)?$', version)
    assert m is not None, version
    version = m.group(1)
    if m.group(2) is not None:
        version += '+' + m.group(2)[1:].replace('-', '.')
    return version

# }}}

# `bdist_win` command. {{{

class BinaryDistWin(Command):

    description = 'create distribution(s) for MS Windows'
    user_options = [
        ('trim', 't',
         'trim the resulting distribution to reduce size'),
        ('zipdir', 'z',
         'create a zip of the resulting directory'),
        ('installer', 'i',
         'create an executable installer for the resulting distribution'),
        ('bash=', None,
         'bash executable to use for running the build script'),
    ]
    boolean_options = ['installer', 'trim', 'zipdir']
    extra_args = []

    def initialize_options(self):
        self.bash = None
        self.installer = False
        self.trim = False
        self.zipdir = False

    def finalize_options(self):
        pass

    def run(self):
        cmd = [self.bash or 'bash', 'windows/dist_build.sh']
        if self.installer:
            cmd.append('--installer')
        if self.trim:
            cmd.append('--trim')
        if self.zipdir:
            cmd.append('--zipdir')
        cmd.extend((__software_name__, __version__, self.bdist_wheel()))
        log.info('running %s', ' '.join(cmd))
        subprocess.check_call(cmd)

if sys.platform.startswith('win32'):
    cmdclass['bdist_win'] = BinaryDistWin

# }}}

# `launch` command. {{{

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
            python_path = os.environ.get('PYTHONPATH', '').split(os.pathsep)
            python_path.insert(0, sys.path[0])
            os.environ['PYTHONPATH'] = os.pathsep.join(python_path)
            cmd = [sys.executable, '-m', 'plover.main'] + self.args
            if sys.platform.startswith('win32'):
                # Workaround https://bugs.python.org/issue19066
                subprocess.Popen(cmd, cwd=os.getcwd())
                sys.exit(0)
            os.execv(cmd[0], cmd)

cmdclass['launch'] = Launch

# }}}

# `patch_version` command. {{{

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

cmdclass['patch_version'] = PatchVersion

# }}}

# `tag_weekly` command. {{{

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
        subprocess.check_call('git tag -f -m'.split()
                              + [weekly_version, weekly_version])

cmdclass['tag_weekly'] = TagWeekly

# }}}

# `bdist_app` and `bdist_dmg` commands. {{{

class BinaryDistApp(Command):
    description = 'create an application bundle for Mac'
    user_options = []
    extra_args = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        cmd = ['bash', 'osx/make_app.sh', self.bdist_wheel()]
        log.info('running %s', ' '.join(cmd))
        subprocess.check_call(cmd)

class BinaryDistDmg(Command):

    user_options = []
    extra_args = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('bdist_app')
        # Encode targeted macOS plaftorm in the filename.
        from wheel.bdist_wheel import get_platform
        platform = get_platform('dist/Plover.app')
        args = '{out!r}, {name!r}, {settings!r}, lookForHiDPI=True'.format(
            out='dist/%s-%s.dmg' % (PACKAGE, platform),
            name=__software_name__.capitalize(),
            settings='osx/dmg_resources/settings.py',
        )
        log.info('running dmgbuild(%s)', args)
        script = "__import__('dmgbuild').build_dmg(" + args + ')'
        subprocess.check_call((sys.executable, '-u', '-c', script))



if sys.platform.startswith('darwin'):
    cmdclass['bdist_app'] = BinaryDistApp
    cmdclass['bdist_dmg'] = BinaryDistDmg

# }}}

# `bdist_appimage` command. {{{

class BinaryDistAppImage(Command):

    description = 'create AppImage distribution for Linux'
    command_consumes_arguments = True
    user_options = []

    def initialize_options(self):
        self.args = None

    def finalize_options(self):
        pass

    def run(self):
        cmd = ['./linux/appimage/build.sh',
               '--python', sys.executable,
               '--wheel', self.bdist_wheel()
              ] + self.args
        log.info('running %s', ' '.join(cmd))
        subprocess.check_call(cmd)

if sys.platform.startswith('linux'):
    cmdclass['bdist_appimage'] = BinaryDistAppImage

# }}}

# Translations support. {{{

try:
    from babel.messages import frontend as babel
except:
    babel_available = False
else:
    babel_available = True

if babel_available:

    cmdclass.update({
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog
    })
    locale_dir = 'plover/gui_qt/messages'
    template = '%s/%s.pot' % (locale_dir, __software_name__)
    options['compile_catalog'] = {
        'domain': __software_name__,
        'directory': locale_dir,
    }
    options['extract_messages'] = {
        'output_file': template,
    }
    options['init_catalog'] = {
        'domain': __software_name__,
        'input_file': template,
        'output_dir': locale_dir,
    }
    options['update_catalog'] = {
        'domain': __software_name__,
        'output_dir': locale_dir,
    }

else:

    class CompileCatalogs(Command):

        description = 'compile message catalogs'
        command_consumes_arguments = True
        user_options = []

        def initialize_options(self):
            self.args = None

        def finalize_options(self):
            pass

        def run(self):
            raise DistutilsModuleError('babel is not available')

    cmdclass.update({'compile_catalog': CompileCatalogs}),

BuildPy.build_dependencies.append('compile_catalog')

# }}}

def reqs(name):
    with open(os.path.join('reqs', name + '.txt')) as fp:
        return fp.read()

setup(
    name=__software_name__,
    version=__version__,
    description=__description__,
    long_description=__long_description__,
    url=__url__,
    download_url=__download_url__,
    license=__license__,
    options=options,
    cmdclass=cmdclass,
    install_requires=reqs('dist'),
    extras_require={
        'gui_qt': reqs('dist_extra_gui_qt'),
        'log': reqs('dist_extra_log'),
    },
    tests_require=reqs('test'),
)

# vim: foldmethod=marker
