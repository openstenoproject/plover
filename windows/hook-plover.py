
import os
import sys
import pkg_resources

from PyInstaller.utils.hooks import copy_metadata, collect_submodules
from plover import __version__ as plover_version

python_version = 'py%u%u' % (sys.version_info.major, sys.version_info.minor)

egg_info = 'Plover-%s-%s.egg-info' % (plover_version, python_version)

datas = [('Plover.egg-info', egg_info)]

for pkg in (
    'appdirs',
    'pyserial',
    'pywinauto',
    'pywinusb',
    'setuptools',
):
    datas.extend(copy_metadata(pkg))

for pkg in (
    'pyHook',
    'pywin32',
):
    dist = pkg_resources.get_distribution(pkg)
    egg_info = dist.egg_name() + '.egg-info'
    datas.append((os.path.join(dist.location, egg_info), egg_info))

datas.append(('plover/assets', 'plover/assets'))

hiddenimports = []
hiddenimports.append('plover.system.english_stenotype')
hiddenimports.extend(collect_submodules('pkg_resources._vendor'))

