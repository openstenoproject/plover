import pytest

from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry


@pytest.fixture(scope='session', autouse=True)
def setup_plover():
    registry.update()
    system.setup(DEFAULT_SYSTEM_NAME)

pytest.register_assert_rewrite('plover_build_utils.testing')
