import re
import sys
from importlib.metadata import entry_points

if __name__ == '__main__':
    if sys.platform.startswith('win32'):
        # Allow interrupting with Ctrl+C.
        __import__('ctypes').windll.kernel32.SetConsoleCtrlHandler(0, 0)

    # Normalize the script name in `sys.argv[0]`
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])

    # Find and load the `pip` entry point
    entry_point = next(
        ep for ep in entry_points(group='console_scripts') if ep.name == 'pip'
    )
    sys.exit(entry_point.load()())
