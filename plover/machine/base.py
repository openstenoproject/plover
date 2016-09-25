# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: add tests for all machines
# TODO: add tests for new status callbacks

"""Base classes for machine types. Do not use directly."""

import serial
import threading

from plover import log
from plover.machine.keymap import Keymap
from plover import system


STATE_STOPPED = 'stopped'
STATE_INITIALIZING = 'initializing'
STATE_RUNNING = 'connected'
STATE_ERROR = 'disconnected'


class StenotypeBase(object):
    """The base class for all Stenotype classes."""

    # Layout of physical keys.
    KEYS_LAYOUT = ''
    # And possible actions to map to.
    ACTIONS = system.KEYS + ('no-op',)

    def __init__(self):
        self.keymap = Keymap(self.KEYS_LAYOUT.split(), self.ACTIONS)
        self.stroke_subscribers = []
        self.state_subscribers = []
        self.state = STATE_STOPPED

    def set_mappings(self, mappings):
        """Setup machine keymap: mappings of action to keys."""
        self.keymap.set_mappings(mappings)

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

    def set_suppression(self, enabled):
        '''Enable keyboard suppression.

        This is only of use for the keyboard machine,
        to suppress the keyboard when then engine is running.
        '''
        pass

    def suppress_last_stroke(self, send_backspaces):
        '''Suppress the last stroke key events after the fact.

        This is only of use for the keyboard machine,
        and the engine is resumed with a command stroke.

        Argument:

        send_backspaces -- The function to use to send backspaces.
        '''
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

    @classmethod
    def get_option_info(cls):
        """Get the default options for this machine."""
        return {}


class ThreadedStenotypeBase(StenotypeBase, threading.Thread):
    """Base class for thread based machines.
    
    Subclasses should override run.
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.name += '-machine'
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

    def _close_port(self):
        if self.serial_port is None:
            return
        self.serial_port.close()
        self.serial_port = None

    def start_capture(self):
        self._close_port()

        try:
            self.serial_port = serial.Serial(**self.serial_params)
        except (serial.SerialException, OSError):
            log.warning('Can\'t open serial port', exc_info=True)
            self._error()
            return

        if not self.serial_port.isOpen():
            log.warning('Serial port is not open: %s', self.serial_params.get('port'))
            self._error()
            return

        return ThreadedStenotypeBase.start_capture(self)

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        ThreadedStenotypeBase.stop_capture(self)
        self._close_port()

    @classmethod
    def get_option_info(cls):
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
