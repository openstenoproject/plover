# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: add tests for all machines
# TODO: add tests for new status callbacks

"""Base classes for machine types. Do not use directly."""

import serial
import threading
import collections
from plover import log

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
        self.suppress = None

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
        # If the stroke matches a command while the keyboard is not suppressed 
        # then the stroke needs to be suppressed after the fact. One of the 
        # handlers will set the suppress function. This function is passed in to 
        # prevent threading issues with the gui.
        self.suppress = None
        for callback in self.stroke_subscribers:
            callback(steno_keys)
        if self.suppress:
            self._post_suppress(self.suppress, steno_keys)
            
    def _post_suppress(self, suppress, steno_keys):
        """This is a complicated way for the application to tell the machine to 
        suppress this stroke after the fact. This only currently has meaning for 
        the keyboard machine so it can backspace over the last stroke when used 
        to issue a command when plover is 'off'.
        """
        pass

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
        except (serial.SerialException, OSError) as e:
            log.error('Opening serial port: %s', str(e))
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
        sb = lambda s: int(float(s)) if float(s).is_integer() else float(s)
        return {
            'port': (None, str), # TODO: make first port default
            'baudrate': (9600, int),
            'bytesize': (8, int),
            'parity': ('N', str),
            'stopbits': (1, sb),
            'timeout': (2.0, float),
            'xonxoff': (False, bool_converter),
            'rtscts': (False, bool_converter)
        }
