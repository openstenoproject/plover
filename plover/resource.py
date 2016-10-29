
import io
import os

import pkg_resources


ASSET_SCHEME = 'asset:'

def _asset_split(resource_name):
    return resource_name[len(ASSET_SCHEME):].split(':', 2)

def resource_exists(resource_name):
    if resource_name.startswith(ASSET_SCHEME):
        return pkg_resources.resource_exists(*_asset_split(resource_name))
    return os.path.exists(resource_name)

def resource_filename(resource_name):
    if resource_name.startswith(ASSET_SCHEME):
        return pkg_resources.resource_filename(*_asset_split(resource_name))
    return resource_name

def resource_stream(resource_name, encoding=None):
    filename = resource_filename(resource_name)
    mode = 'rb' if encoding is None else 'r'
    return io.open(filename, mode, encoding=encoding)

def resource_string(resource_name, encoding=None):
    if resource_name.startswith(ASSET_SCHEME):
        s = pkg_resources.resource_string(*_asset_split(resource_name))
        return s if encoding is None else unicode(s, encoding)
    mode = 'rb' if encoding is None else 'r'
    with io.open(resource_name, mode, encoding=encoding) as fp:
        return fp.read()
