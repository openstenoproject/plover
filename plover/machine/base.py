# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: add tests for all machines
# TODO: add tests for new status callbacks

"""Base classes for machine types. Do not use directly."""

import serial
import threading
from plover.exception import SerialPortException
import collections

STATE_STOPPED = 'closed'
STATE_INITIALIZING = 'initializing'
STATE_RUNNING = 'connected'
STATE_ERROR = 'disconnected'

class StenotypeBase(object):
    """The base class for all Stenotype classes."""

    def __init__(self):
        self.stroke_subscribers = []
        self.state_subscribers = []
        self.state = STATE_STOPPED

    def start_capture(self):
        """Begin listening for output from the stenotype machine."""
        pass

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        pass

    def add_stroke_callback(self, callback):
        """Subscribe to output from the stenotype machine.

        Argument:

        callback -- The function to call whenever there is output from
        the stenotype machine and output is being captured.

        """
        self.stroke_subscribers.append(callback)

    def remove_stroke_callback(self, callback):
        """Unsubscribe from output from the stenotype machine.

        Argument:

        callback -- A function that was previously subscribed.

        """
        self.stroke_subscribers.remove(callback)

    def add_state_callback(self, callback):
        self.state_subscribers.append(callback)
        
    def remove_state_callback(self, callback):
        self.state_subscribers.remove(callback)

    def _notify(self, steno_keys):
        """Invoke the callback of each subscriber with the given argument."""
        for callback in self.stroke_subscribers:
            callback(steno_keys)

    def _set_state(self, state):
        self.state = state
        for callback in self.state_subscribers:
            callback(state)

    def _stopped(self):
        self._set_state(STATE_STOPPED)

    def _initializing(self):
        self._set_state(STATE_INITIALIZING)

    def _ready(self):
        self._set_state(STATE_RUNNING)
            
    def _error(self):
        self._set_state(STATE_ERROR)

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
        self._initializing()
        self.start()

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        self.finished.set()
        try:
            self.join()
        except RuntimeError:
            pass
        self._stopped()

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
        self.serial_port = None
        self.serial_params = serial_params

    def start_capture(self):
        if self.serial_port:
            self.serial_port.close()

        try:
            self.serial_port = serial.Serial(**self.serial_params)
        except serial.SerialException:
            self._error()
            return
        if self.serial_port is None or not self.serial_port.isOpen():
            self._error()
            return
        return ThreadedStenotypeBase.start_capture(self)

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        ThreadedStenotypeBase.stop_capture(self)
        if self.serial_port:
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
