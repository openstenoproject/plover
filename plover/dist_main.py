
import os
import sys
import subprocess

from plover.oslayer.config import CONFIG_DIR, PLUGINS_PLATFORM


def main():
    args = sys.argv[:]
    args[0:1] = [sys.executable, '-m', 'plover.main', '--gui', 'qt']
    if '--no-user-plugins' in args[3:]:
        args.remove('--no-user-plugins')
        args.insert(1, '-s')
    os.environ['PYTHONUSERBASE'] = os.path.join(CONFIG_DIR, 'plugins', PLUGINS_PLATFORM)
    if sys.platform.startswith('win32'):
        # Workaround https://bugs.python.org/issue19066
        subprocess.Popen(args, cwd=os.getcwd())
        sys.exit(0)
    os.execv(args[0], args)


if __name__ == '__main__':
    main()
