# Copyright (c) 2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Custom exceptions used by Plover.

The exceptions in this module are typically caught in the main GUI
loop and displayed to the user as an alert dialog.

"""

SERIAL_PORT_EXCEPTION_MESSAGE =  ("The requested serial port either "
                                  "doesn't exist or is "
                                  "misconfigured. Please reconfigure"
                                  "the serial port and restart Plover.")

class SerialPortException(Exception):
    """Raised when a serial port is misconfigured."""

    def __init__(self, *args):
        """Override the constructor to include a default message."""
        Exception.__init__(self, SERIAL_PORT_EXCEPTION_MESSAGE, *args)
