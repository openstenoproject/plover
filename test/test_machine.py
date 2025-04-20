from unittest.mock import Mock
from plover.machine.base import ThreadedStenotypeBase
import pytest

class MyMachine(ThreadedStenotypeBase):
    def run(self):
        raise RuntimeError("some unexpected error")

@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_update_machine_staten_on_unhandled_exception():
    machine = MyMachine()
    callback = Mock()
    machine.add_state_callback(callback)
    machine.start_capture()
    machine.join()
    callback.assert_called_with('disconnected')
