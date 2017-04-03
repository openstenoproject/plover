from contextlib import contextmanager
import os
import tempfile


@contextmanager
def make_dict(contents):
    tf = tempfile.NamedTemporaryFile(delete=False)
    try:
        tf.write(contents)
        tf.close()
        yield tf.name
    finally:
        os.unlink(tf.name)

