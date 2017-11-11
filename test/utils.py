from contextlib import contextmanager
import os
import tempfile

from plover.misc import normalize_path


@contextmanager
def make_dict(contents, extension=None, name=None):
    kwargs = { 'delete': False }
    if name is not None:
        kwargs['prefix'] = name + '_'
    if extension is not None:
        kwargs['suffix'] = '.' + extension
    tf = tempfile.NamedTemporaryFile(**kwargs)
    try:
        tf.write(contents)
        tf.close()
        yield normalize_path(tf.name)
    finally:
        os.unlink(tf.name)

