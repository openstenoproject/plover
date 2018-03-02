# Copyright (c) 2012 Hesky Fisher
# See LICENSE.txt for details.
#
# processlock.py - Cross platform global lock to ensure plover only runs once.

"""Global lock to ensure plover only runs once."""

import sys


class LockNotAcquiredException(Exception):
    pass


if sys.platform.startswith('win32'):

    from ctypes import windll


    class PloverLock:

        # A GUID from http://createguid.com/
        guid = 'plover_{F8C06652-2C51-410B-8D15-C94DF96FC1F9}'

        def __init__(self):
            pass

        def acquire(self):
            self.mutex = windll.kernel32.CreateMutexA(None, False, self.guid)
            if windll.kernel32.GetLastError() == 0xB7: # ERROR_ALREADY_EXISTS
                raise LockNotAcquiredException()

        def release(self):
            if hasattr(self, 'mutex'):
                windll.kernel32.CloseHandle(self.mutex)
                del self.mutex

        def __del__(self):
            self.release()

        def __enter__(self):
            self.acquire()

        def __exit__(self, type, value, traceback):
            self.release()

else:

    import fcntl
    import os


    class PloverLock:

        def __init__(self):
            # Check the environment for items to make the lockfile unique
            # fallback if not found

            if 'DISPLAY' in os.environ:
                display = os.environ['DISPLAY'][-1:]
            else:
                display = "0"

            if hasattr(os, "uname"):
                hostname = os.uname()[1]
            else:
                import socket
                hostname = socket.gethostname()

            lock_file_name = os.path.expanduser(
                '~/.plover-lock-%s-%s' % (hostname, display))
            self.fd = open(lock_file_name, 'w')

        def acquire(self):
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError as e:
                raise LockNotAcquiredException(str(e))

        def release(self):
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
            except:
                pass

        def __del__(self):
            self.release()
            try:
                self.fd.close()
            except:
                pass

        def __enter__(self):
            self.acquire()

        def __exit__(self, exc_type, exc_value, traceback):
            self.release()
