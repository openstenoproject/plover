import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    if sys.platform.startswith('win32'):
        # Allow interrupting with Ctrl+C.
        __import__('ctypes').windll.kernel32.SetConsoleCtrlHandler(0, 0)
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('pip', 'console_scripts', 'pip')()
    )
