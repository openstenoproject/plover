import os

import pytest

# Ensure i18n support does not mess us up.
os.environ['LANGUAGE'] = 'C'

from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry


@pytest.fixture(scope='session', autouse=True)
def setup_plover():
    registry.update()
    system.setup(DEFAULT_SYSTEM_NAME)

pytest.register_assert_rewrite('plover_build_utils.testing')

def pytest_collection_modifyitems(items):
    for item in items:
        # Mark `gui_qt` tests.
        if 'gui_qt' in item.location[0].split(os.path.sep):
            item.add_marker(pytest.mark.gui_qt)
