
import unittest

from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry


# So our custom assertHelpers are not part of the test failure tracebacks.
__unittest = True


class TestCase(unittest.TestCase):

    def assertRaisesWithMessage(self, exception, msg):
        outer_self = self
        class ContextManager(object):
            def __enter__(self):
                pass
            def __exit__(self, exc_type, exc_value, traceback):
                if exc_type is exception:
                    return True
                if exc_type is None:
                    outer_self.fail(msg=msg)
                return False
        return ContextManager()


# Setup registry.
registry.update()
# Setup default system.
system.setup(DEFAULT_SYSTEM_NAME)
