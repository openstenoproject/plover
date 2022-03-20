class Capture:

    """Keyboard capture interface."""

    # Callbacks for keyboard press/release events.
    key_down = lambda key: None
    key_up = lambda key: None

    def start(self):
        """Start capturing key events."""
        raise NotImplementedError()

    def cancel(self):
        """Stop capturing key events."""
        raise NotImplementedError()

    def suppress(self, suppressed_keys=()):
        """Setup suppression."""
        raise NotImplementedError()
