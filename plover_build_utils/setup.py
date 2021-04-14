from distutils import log
import contextlib
import importlib
import os
import shutil
import subprocess
import sys

from setuptools.command.build_py import build_py
import pkg_resources
import setuptools


class Command(setuptools.Command):

    def build_in_place(self):
        self.run_command('build_py')
        self.reinitialize_command('build_ext', inplace=1)
        self.run_command('build_ext')

    @contextlib.contextmanager
    def project_on_sys_path(self, build=True):
        ei_cmd = self.get_finalized_command("egg_info")
        if build:
            self.build_in_place()
        else:
            ei_cmd.run()
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

    def bdist_wheel(self):
        '''Run bdist_wheel and return resulting wheel file path.'''
        whl_cmd = self.get_finalized_command('bdist_wheel')
        whl_cmd.run()
        for cmd, py_version, dist_path in whl_cmd.distribution.dist_files:
            if cmd == 'bdist_wheel':
                return dist_path
        raise Exception('could not find wheel path')

# `test` command. {{{

class Test(Command):

    description = 'run unit tests after in-place build'
    command_consumes_arguments = True
    user_options = []
    test_dir = 'test'
    build_before = True

    def initialize_options(self):
        self.args = []

    def finalize_options(self):
        pass

    def run(self):
        with self.project_on_sys_path(build=self.build_before):
            self.run_tests()

    def run_tests(self):
        # Remove __pycache__ directory so pytest does not freak out
        # when switching between the Linux/Windows versions.
        pycache = os.path.join(self.test_dir, '__pycache__')
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
            args.insert(0, self.test_dir)
        sys.argv[1:] = args
        main = pkg_resources.load_entry_point('pytest',
                                              'console_scripts',
                                              'py.test')
        sys.exit(main())

# }}}

# i18n support. {{{

def babel_options(package, resource_dir=None):
    if resource_dir is None:
        localedir = '%s/messages' % package
    else:
        localedir = '%s/%s' % (package, resource_dir)
    template = '%s/%s.pot' % (localedir, package)
    return {
        'compile_catalog': {
            'domain': package,
            'directory': localedir,
        },
        'extract_messages': {
            'add_comments': ['i18n:'],
            'output_file': template,
            'strip_comments': True,
        },
        'init_catalog': {
            'domain': package,
            'input_file': template,
            'output_dir': localedir,
        },
        'update_catalog': {
            'domain': package,
            'output_dir': localedir,
        }
    }

# }}}

# UI generation. {{{

class BuildUi(Command):

    description = 'build UI files'
    user_options = [
        ('force', 'f',
         'force re-generation of all UI files'),
    ]

    hooks = '''
    plover_build_utils.pyqt:fix_icons
    plover_build_utils.pyqt:no_autoconnection
    '''.split()

    def initialize_options(self):
        self.force = False

    def finalize_options(self):
        pass

    def _build_ui(self, src):
        dst = os.path.splitext(src)[0] + '_ui.py'
        if not self.force and os.path.exists(dst) and \
           os.path.getmtime(dst) >= os.path.getmtime(src):
            return
        cmd = (
            sys.executable, '-m', 'PyQt5.uic.pyuic',
            '--from-import', src,
        )
        if self.verbose:
            log.info('generating %s', dst)
        contents = subprocess.check_output(cmd).decode('utf-8')
        for hook in self.hooks:
            mod_name, attr_name = hook.split(':')
            mod = importlib.import_module(mod_name)
            hook_fn = getattr(mod, attr_name)
            contents = hook_fn(contents)
        with open(dst, 'w') as fp:
            fp.write(contents)

    def _build_resources(self, src):
        dst = os.path.join(
            os.path.dirname(os.path.dirname(src)),
            os.path.splitext(os.path.basename(src))[0]
        ) + '_rc.py'
        cmd = (
            sys.executable, '-m', 'PyQt5.pyrcc_main',
            src, '-o', dst,
        )
        if self.verbose:
            log.info('generating %s', dst)
        subprocess.check_call(cmd)

    def run(self):
        self.run_command('egg_info')
        std_hook_prefix = __package__ + '.pyqt:'
        hooks_info = [
            h[len(std_hook_prefix):] if h.startswith(std_hook_prefix) else h
            for h in self.hooks
        ]
        log.info('generating ui (hooks: %s)', ', '.join(hooks_info))
        ei_cmd = self.get_finalized_command('egg_info')
        for src in ei_cmd.filelist.files:
            if src.endswith('.qrc'):
                self._build_resources(src)
            if src.endswith('.ui'):
                self._build_ui(src)

# }}}

# Patched `build_py` command. {{{

class BuildPy(build_py):

    build_dependencies = []

    def run(self):
        for command in self.build_dependencies:
            self.run_command(command)
        build_py.run(self)

# }}}
