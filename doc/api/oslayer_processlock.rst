``plover.oslayer.processlock`` -- Process locking
=================================================

This module provides a global process lock to ensure that there is only
one instance of Plover running.

.. py:module:: plover.oslayer.processlock

.. exception:: LockNotAcquiredException

    Raised when the process lock is already being held, i.e. Plover is
    already running.

.. class:: PloverLock

    Creates a system-wide mutex lock. On Windows, this creates a mutex with
    Plover's GUID; on macOS and Linux, this creates a file in the user's home
    directory and acquires a lock on that.

    An instance of this class can also be used as a context manager:

    ::

        with PloverLock():
          # Now this is the only Plover instance running
          pass

    .. method:: acquire()

        Acquire the lock. Raise :exc:`LockNotAcquiredException` if it is
        already being held. This method is called when Plover starts.

    .. method:: release()

        Release the lock. This method is called when Plover exits.
