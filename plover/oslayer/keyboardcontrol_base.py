
class KeyboardCaptureBase:
    """Listen to keyboard press and release events."""

    # Callbacks for keyboard press/release events.
    key_down = lambda key: None
    key_up = lambda key: None

    def start(self):
        pass

    def cancel(self):
        pass

    def suppress_keys(self, suppressed_keys=()):
        raise NotImplementedError()


class KeyboardEmulationBase:
    """Emulate keyboard events."""

    @classmethod
    def get_option_info(cls):
        return {}

    def __init__(self, params):
        pass

    def start(self):
        pass

    def cancel(self):
        pass

    def send_backspaces(self, number_of_backspaces):
        '''Emulate the given number of backspaces.'''
        raise NotImplementedError()

    def send_string(self, s):
        '''Emulate the given string.'''
        raise NotImplementedError()

    def send_key_combination(self, combo_string):
        '''Emulate a sequence of key combinations.'''
        raise NotImplementedError()

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass
