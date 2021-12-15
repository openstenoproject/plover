from contextlib import contextmanager
from tempfile import NamedTemporaryFile
import os
import shutil

import pkg_resources


ASSET_SCHEME = 'asset:'


def _asset_filename(resource_name):
    components = resource_name[len(ASSET_SCHEME):].split(':', 1)
    if len(components) != 2:
        raise ValueError('invalid asset: %s' % resource_name)
    if os.path.isabs(components[1]):
        raise ValueError(f'invalid asset: {resource_name}')
    return pkg_resources.resource_filename(*components)

def resource_exists(resource_name):
    if resource_name.startswith(ASSET_SCHEME):
        resource_name = _asset_filename(resource_name)
    return os.path.exists(resource_name)

def resource_filename(resource_name):
    if resource_name.startswith(ASSET_SCHEME):
        resource_name = _asset_filename(resource_name)
    return resource_name

def resource_timestamp(resource_name):
    filename = resource_filename(resource_name)
    return os.path.getmtime(filename)

@contextmanager
def resource_update(resource_name):
    if resource_name.startswith(ASSET_SCHEME):
        raise ValueError(f'updating an asset is unsupported: {resource_name}')
    filename = resource_filename(resource_name)
    directory = os.path.dirname(filename)
    extension = os.path.splitext(filename)[1]
    tempfile = NamedTemporaryFile(delete=False, dir=directory,
                                  suffix=extension or None)
    try:
        tempfile.close()
        yield tempfile.name
        shutil.move(tempfile.name, filename)
    finally:
        if os.path.exists(tempfile.name):
            os.unlink(tempfile.name)
