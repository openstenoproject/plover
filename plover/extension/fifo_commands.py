import select
import errno
import os
from threading import Lock, Thread


from plover import log


FIFO_PATH = '/tmp/PLOVER_CMD'

class FIFOCommands(Thread):

    def __init__(self, engine, name='FIFOCommand'):
        super(FIFOCommands, self).__init__()
        self.name += '-' + name
        self._engine = engine
        self._pipe = os.pipe()

    def run(self):

        # Ensure that the FIFO exists
        try:
            os.mkfifo(FIFO_PATH)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise

        fifo = os.fdopen(os.open(FIFO_PATH, os.O_RDWR | os.O_NONBLOCK))

        while True:
            try:
                rlist, wlist, xlist = select.select((self._pipe[0], fifo), (), ())


            # In some versions of python, if the thread receives 
            # a signal, select will raise a harmless EINTR
            # exception. In our case, we can just ignore it, and
            # restart our loop
            except select.error as err:
                if isinstance(err, OSError):
                    code = err.errno
                else:
                    code = err[0]

                if code != errno.EINTR:
                    raise

                continue


            assert not wlist
            assert not xlist

            if self._pipe[0] in rlist:
                break

            elif fifo in rlist:
                cmd = fifo.readline().strip()
                self._engine.run_engine_command(cmd)

    def stop(self):
        # Wakes up the thread
        os.write(self._pipe[1], b'quit\n')

        # ... and waits for it to terminate
        self.join()

        # Closes the pipes
        for fd in self._pipe:
            os.close(fd)

        # Removes the FIFO
        os.remove(FIFO_PATH)


