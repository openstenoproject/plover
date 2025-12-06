class Capture:
    """Keyboard capture interface."""

    # Callbacks for keyboard press/release events.
    def key_down(key):
        return None

    def key_up(key):
        return None

    def start(self):
        """Start capturing key events."""
        raise NotImplementedError()

    def cancel(self):
        """Stop capturing key events."""
        raise NotImplementedError()

    def suppress(self, suppressed_keys=()):
        """Setup suppression."""
        raise NotImplementedError()
