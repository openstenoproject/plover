# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Base classes for machine types. Do not use directly."""

import serial
import threading
from plover.exception import SerialPortException
import collections

class StenotypeBase(object):
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

    def remove_callback(self, callback):
        """Unsubscribe from output from the stenotype machine.

        Argument:

        callback -- A function that was previously subscribed.

        """
        self.subscribers.remove(callback)

    def _notify(self, steno_keys):
        """Invoke the callback of each subscriber with the given argument."""
        for callback in self.subscribers:
            callback(steno_keys)

    @staticmethod
    def get_option_info():
        """Get the default options for this machine."""
        return {}

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
        # todo: handle the possibility of failure on start
        # add notification mechanism for "ready"

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        self.finished.set()
        self.join()
        # todo: handle the possibility that the thread never started.

class SerialStenotypeBase(ThreadedStenotypeBase):
    """For use with stenotype machines that connect via serial port.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """

    def __init__(self, serial_params):
        """Monitor the stenotype over a serial port.

        Keyword arguments are the same as the keyword arguments for a
        serial.Serial object.

        """
        ThreadedStenotypeBase.__init__(self)
        try:
            self.serial_port = serial.Serial(**serial_params)
        except serial.SerialException:
            raise SerialPortException()
        if self.serial_port is None or not self.serial_port.isOpen():
            raise SerialPortException()

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        ThreadedStenotypeBase.stop_capture(self)
        self.serial_port.close()

    @staticmethod
    def get_option_info():
        """Get the default options for this machine."""
        bool_converter = lambda s: s == 'True'
        return {
            'port': (None, str), # TODO: make first port default
            'baudrate': (9600, int),
            'bytesize': (8, int),
            'parity': ('N', str),
            'stopbits': (1, float),
            'timeout': (2.0, float),
            'xonxoff': (False, bool_converter),
            'rtscts': (False, bool_converter)
        }
