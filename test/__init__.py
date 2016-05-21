
import unittest


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

