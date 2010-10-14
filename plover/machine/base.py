# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Base classes for machine types. Do not use directly."""

# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Thread-based monitoring of a Gemini PR stenotype machine."""

import serial
import threading

class SerialStenotypeBase(threading.Thread):
    """For use with stenotype machines that connect via serial port.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """
    
    def __init__(self, port='/dev/ttyUSB0'):
        """Monitor the stenotype over a serial port.

        Argument:

        port -- Serial port to which the machine is
        connected. Defaults to '/dev/ttyUSB0'.

        """
        threading.Thread.__init__(self)
        self.finished = threading.Event()
        self.subscribers = []
        # The timeout argument to Serial is in seconds. This is needed
        # so that the thread can terminate properly by being allowed
        # to periodically check the finished flag. This might cause
        # strokes to be only partially read.
        self.serial_port = serial.Serial(port=port, timeout=2)
        
    def run(self):
        """This method should be overridden by a subclass."""
        pass

    def start_capture(self):
        """Begin listening for output from the stenotype machine."""
        self.finished.clear()
        self.start()

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        self.finished.set()
        self.serial_port.close()

    def add_callback(self, callback):
        """Subscribe to output from the stenotype machine.

        Argument:

        callback -- The function to call whenever there is output from
        the stenotype machine and output is being captured.

        """
        self.subscribers.append(callback)

    def _notify(self, steno_keys):
        """Invoke the callback of each subscriber with the given argument."""
        for callback in self.subscribers:
            callback(steno_keys)
