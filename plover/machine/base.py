# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Base classes for machine types. Do not use directly."""

import serial
import threading
from plover.exception import SerialPortException


class StenotypeBase:
    """The base class for all Stenotype classes."""

    # Some subclasses of StenotypeBase might require configuration
    # parameters to be passed to the constructor. This variable
    # advertises the class that contains such parameters.
    CONFIG_CLASS = None

    def __init__(self):
        self.subscribers = []

    def start_capture(self):
        """Begin listening for output from the stenotype machine."""
        pass

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        pass

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

class ThreadedStenotypeBase(StenotypeBase, threading.Thread):
    """Base class for thread based machines.
    
    Subclasses should override run.
    """
    def __init__(self):
        threading.Thread.__init__(self)
        StenotypeBase.__init__(self)
        self.finished = threading.Event()

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
        self.join()

class SerialStenotypeBase(ThreadedStenotypeBase):
    """For use with stenotype machines that connect via serial port.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """

    CONFIG_CLASS = serial.Serial

    def __init__(self, **kwargs):
        """Monitor the stenotype over a serial port.

        Keyword arguments are the same as the keyword arguments for a
        serial.Serial object.

        """
        super(type(self), self).__init__()
        try:
            self.serial_port = self.CONFIG_CLASS(**kwargs)
        except serial.SerialException:
            raise SerialPortException()
        if self.serial_port is None or not self.serial_port.isOpen():
            raise SerialPortException()

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        super(type(self), self).stop_capture()
        self.serial_port.close()
