import os

import pytest

from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry


# Set pytest-qt's API to QtPy's.
try:
    from qtpy import API as QT_API
    from qtpy import QtCore
except ImportError:
    pass
else:
    os.environ['PYTEST_QT_API'] = QT_API


@pytest.fixture(scope='session', autouse=True)
def setup_plover():
    registry.update()
    system.setup(DEFAULT_SYSTEM_NAME)

pytest.register_assert_rewrite('plover_build_utils.testing')

def pytest_ignore_collect(path, config):
    # Ignore `gui_qt` test during collection
    # if pytest-qt is not available.
    if 'gui_qt' not in str(path).split(os.path.sep):
        return False
    if config.pluginmanager.has_plugin('pytest-qt'):
        return False
    return True

def pytest_collection_modifyitems(items):
    for item in items:
        # Mark `gui_qt` tests.
        if 'gui_qt' in item.location[0].split(os.path.sep):
            item.add_marker(pytest.mark.gui_qt)
