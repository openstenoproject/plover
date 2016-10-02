
from glob import glob
import os

import pkg_resources

from utils.metadata import collect_metadata

from PyInstaller import log as logging


log = logging.getLogger(__name__)
log.info('hook-plover.py')

datas = []
hiddenimports = []

distribution = list(pkg_resources.find_distributions('.', only=True))[0]
assert distribution.project_name == 'plover'

metadata_list = collect_metadata(distribution)
log.info('adding metadata: %s', metadata_list)
datas.extend(metadata_list)

datas.append(('plover/assets', 'plover/assets'))
for group in distribution.get_entry_map().values():
    for entrypoint in group.values():
        hiddenimports.append(entrypoint.module_name)

try:
    import PyQt5
except ImportError:
    pass
else:
    # Qt GUI localization.
    from PyQt5.QtCore import QLibraryInfo

    for catalog in glob('plover/gui_qt/messages/*/*/*.mo'):
        datas.append((catalog, os.path.dirname(catalog)))
    translations_dir = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    for filename in glob(os.path.join(translations_dir, 'qtbase_*.qm')):
        datas.append((filename, 'PyQt5/Qt/translations'))
