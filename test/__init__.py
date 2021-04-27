from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry


# Setup registry.
registry.update()
# Setup default system.
system.setup(DEFAULT_SYSTEM_NAME)
