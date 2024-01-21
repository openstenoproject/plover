class Output:

    """Output interface."""

    def send_backspaces(self, count):
        """Output the given number of backspaces."""
        raise NotImplementedError()

    def send_string(self, string):
        """Output the given string."""
        raise NotImplementedError()

    def send_key_combination(self, combo):
        """Output a sequence of key combinations.

        See `plover.key_combo` for the format of the `combo` string.
        """
        raise NotImplementedError()
    
    def set_key_press_delay(self, delay_ms):
        """Sets the delay between outputting key press events."""
        raise NotImplementedError()
