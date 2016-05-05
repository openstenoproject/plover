
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

