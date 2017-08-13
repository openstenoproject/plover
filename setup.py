#!/usr/bin/env python3
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

__requires__ = '''
Babel
PyQt5>=5.8.2
setuptools>=30.3.0
'''

from distutils import log
import glob
import os
import re
import shutil
import subprocess
import sys
import textwrap
import zipfile

from setuptools import setup

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

from plover_build_utils.setup import BuildPy, BuildUi, Command, Test


BuildPy.build_dependencies.append('build_ui')
cmdclass = {
    'build_py': BuildPy,
    'build_ui': BuildUi,
    'test': Test,
}
options = {}

# Platform specific requirements.
# Note: `extras_require` cannot be moved to setup.cfg, because `:` is not
# allowed in key names and environment markers are not properly supported
# (for the same reason `install_requires` cannot be used).
extras_require = {
    ':"win32" in sys_platform': [
        'plyer==1.2.4', # For notifications.
    ],
    ':"linux" in sys_platform': [
        'python-xlib>=0.16',
    ],
    ':"darwin" in sys_platform': [
        'appnope>=0.1.0',
        'pyobjc-core==3.1.1+plover2',
        'pyobjc-framework-Cocoa==3.1.1+plover2',
        'pyobjc-framework-Quartz==3.1.1',
    ],
}

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
    ]
    boolean_options = ['installer', 'trim', 'zipdir']
    extra_args = []

    def initialize_options(self):
        self.installer = False
        self.trim = False
        self.zipdir = False

    def finalize_options(self):
        pass

    def run(self):
        from plover_build_utils.install_wheels import WHEELS_CACHE
        # Download helper.
        from plover_build_utils.download import download
        # Run command helper.
        def run(*args):
            if self.verbose:
                log.info('running %s', ' '.join(a for a in args))
            subprocess.check_call(args)
        # First things first: create Plover wheel.
        wheel_cmd = self.get_finalized_command('bdist_wheel')
        wheel_cmd.run()
        plover_wheel = glob.glob(os.path.join(wheel_cmd.dist_dir,
                                              wheel_cmd.wheel_dist_name)
                                 + '*.whl')[0]
        # Setup embedded Python distribution.
        # Note: python35.zip is decompressed to prevent errors when 2to3
        # is used (including indirectly by setuptools `build_py` command).
        py_embedded = download('https://www.python.org/ftp/python/3.5.2/python-3.5.2-embed-win32.zip',
                               'a62675cd88736688bb87999e8b86d13ef2656312')
        dist_dir = os.path.join(wheel_cmd.dist_dir, PACKAGE + '-win32')
        data_dir = os.path.join(dist_dir, 'data')
        stdlib = os.path.join(data_dir, 'python35.zip')
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)
        os.makedirs(data_dir)
        for path in (py_embedded, stdlib):
            with zipfile.ZipFile(path) as zip:
                zip.extractall(data_dir)
        os.unlink(stdlib)
        dist_py = os.path.join(data_dir, 'python.exe')
        # Install pip/wheel.
        run(dist_py, '-m', 'plover_build_utils.get_pip')
        # Install Plover + standard plugins and dependencies.
        # Note: do not use the embedded Python executable with `setup.py
        # install` to prevent setuptools from installing extra development
        # dependencies...
        run(dist_py, '-m', 'plover_build_utils.install_wheels',
            '-r', 'requirements_distribution.txt')
        run(dist_py, '-m', 'plover_build_utils.install_wheels',
            '--ignore-installed', '--no-deps', plover_wheel)
        run(dist_py, '-m', 'plover_build_utils.install_wheels',
            '-r', 'requirements_plugins.txt')
        os.unlink(os.path.join(WHEELS_CACHE, os.path.basename(plover_wheel)))
        # Trim the fat...
        if self.trim:
            from plover_build_utils.trim import trim
            trim(data_dir, 'windows/dist_blacklist.txt', verbose=self.verbose)
        # Add miscellaneous files: icon, license, ...
        for src, target_dir in (
            ('LICENSE.txt'             , '.'   ),
            ('plover/assets/plover.ico', 'data')
        ):
            dst = os.path.join(dist_dir, target_dir, os.path.basename(src))
            shutil.copyfile(src, dst)
        # Create launchers.
        for entrypoint, gui in (
            ('plover         = plover.main:main', True ),
            ('plover_console = plover.main:main', False),
        ):
            run(dist_py, '-c', textwrap.dedent(
                '''
                from pip._vendor.distlib.scripts import ScriptMaker
                sm = ScriptMaker(source_dir='{dist_dir}', target_dir='{dist_dir}')
                sm.executable = 'data\\python.exe'
                sm.variants = set(('',))
                sm.make('{entrypoint}', options={{'gui': {gui}}})
                '''.rstrip()).format(dist_dir=dist_dir,
                                     entrypoint=entrypoint,
                                     gui=gui))
        # Make distribution source-less.
        run(dist_py, '-m', 'plover_build_utils.source_less',
            # Don't touch pip._vendor.distlib sources,
            # or `pip install` will not be usable...
            data_dir, '*/pip/_vendor/distlib/*',
        )
        # Check requirements.
        run(dist_py, '-m', 'plover_build_utils.check_requirements')
        # Zip results.
        if self.zipdir:
            from plover_build_utils.zipdir import zipdir
            if self.verbose:
                log.info('zipping %s', dist_dir)
            zipdir(dist_dir)
        # Create an installer.
        if self.installer:
            installer_exe = '%s.setup.exe' % dist_dir
            # Compute install size for "Add/Remove Programs" entry.
            install_size = sum(os.path.getsize(os.path.join(dirpath, f))
                               for dirpath, dirnames, filenames
                               in os.walk(dist_dir) for f in filenames)
            run('makensis.exe', '-NOCD',
                '-Dsrcdir=' + dist_dir,
                '-Dversion=' + __version__,
                '-Dinstall_size=' + str(install_size // 1024),
                'windows/installer.nsi',
                '-XOutFile ' + installer_exe)

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
        self.run_command('egg_info')
        python_path = os.environ.get('PYTHONPATH', '').split(os.pathsep)
        python_path.insert(0, os.getcwd())
        os.environ['PYTHONPATH'] = os.pathsep.join(python_path)
        os.execv(sys.executable, [sys.executable, '-m', 'plover.main'] + self.args)

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
        subprocess.check_call('git tag -f'.split() + [weekly_version])

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
        whl_cmd = self.get_finalized_command('bdist_wheel')
        whl_cmd.run()
        wheel_path = whl_cmd.get_archive_basename()
        cmd = 'bash osx/make_app.sh %s %s' % (wheel_path, PACKAGE)
        log.info('running %s', cmd)
        subprocess.check_call(cmd.split())

class BinaryDistDmg(Command):

    user_options = []
    extra_args = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('bdist_app')
        # Get dmgbuild
        from plover_build_utils.download import download
        dmgbuild = download(
          'https://github.com/morinted/dmgbuild/releases/download/v1.2.1%2Bplover/dmgbuild-1.2.1.pex',
          '548a5c3336fd30b966060b84d86faa9a697b7f94'
        )
        dmg = 'dist/%s.dmg' % PACKAGE
        # Use Apple's built-in python2 to run dmgbuild
        cmd = '/usr/bin/python %s -s osx/dmg_resources/settings.py Plover %s' % (dmgbuild, dmg)
        log.info('running %s', cmd)
        subprocess.check_call(cmd.split())

if sys.platform.startswith('darwin'):
    cmdclass['bdist_app'] = BinaryDistApp
    cmdclass['bdist_dmg'] = BinaryDistDmg

# }}}

# Translations support. {{{

from babel.messages import frontend as babel

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
BuildPy.build_dependencies.append('compile_catalog')

# }}}

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
    extras_require=extras_require,
)

# vim: foldmethod=marker
