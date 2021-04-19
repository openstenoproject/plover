
class KeyboardCaptureBase:
    """Listen to keyboard press and release events."""

    # Callbacks for keyboard press/release events.
    key_down = lambda key: None
    key_up = lambda key: None

    def start(self):
        pass

    def cancel(self):
        pass

    def suppress_keyboard(self, suppressed_keys=()):
        raise NotImplementedError()


class KeyboardEmulationBase:
    """Emulate keyboard events."""

    def send_backspaces(self, number_of_backspaces):
        raise NotImplementedError()

    def send_string(self, s):
        raise NotImplementedError()

    def send_key_combination(self, combo_string):
        raise NotImplementedError()
