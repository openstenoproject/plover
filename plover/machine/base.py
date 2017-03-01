# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: add tests for all machines
# TODO: add tests for new status callbacks

"""Base classes for machine types. Do not use directly."""

import threading

from time import sleep

import serial

from plover import log
from plover.machine.keymap import Keymap


STATE_STOPPED = 'stopped'
STATE_INITIALIZING = 'initializing'
STATE_RUNNING = 'connected'
STATE_ERROR = 'disconnected'


class StenotypeBase(object):
    """The base class for all Stenotype classes."""

    # Layout of physical keys.
    KEYS_LAYOUT = ''
    # And special actions to map to.
    ACTIONS = ()
    # Fallback to use as machine type for finding a compatible keymap
    # if one is not already available for this machine type.
    KEYMAP_MACHINE_TYPE = None

    def __init__(self):
        # Setup default keymap with no translation of keys.
        keys = self.get_keys()
        self.keymap = Keymap(keys, keys)
        self.keymap.set_mappings(zip(keys, keys))
        self.stroke_subscribers = []
        self.state_subscribers = []
        self.state = STATE_STOPPED

    def set_keymap(self, keymap):
        """Setup machine keymap."""
        self.keymap = keymap

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
    def get_actions(cls):
        """List of supported actions to map to."""
        return cls.ACTIONS

    @classmethod
    def get_keys(cls):
        return tuple(set(cls.KEYS_LAYOUT.split()))

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
        self._reconnecting = False

    def _connect(self):
        """This method should be overridden by a subclass."""
        pass

    def _disconnect(self):
        """This method should be overridden by a subclass."""
        pass

    def _reconnect(self):
        try:
            self._reconnecting = True
            self._disconnect()
            i = 0
            # Reconnect loop
            while i < 30 and not self.finished.isSet():
                if self._connect():
                    return True
                i += 1
                sleep(1)
            return False
        finally:
            self._reconnecting = False

    def run(self):
        self._ready()
        while not self.finished.isSet():
            try:
                self._loop_body()
            except Exception:
                log.warning(self.__class__.__name__ + ' disconnected, reconnecting...')
                self._initializing()
                if self._reconnect():
                    self._ready()
                    log.info(self.__class__.__name__ + ' reconnected.')
                else:
                    self._error()
                    log.warning(self.__class__.__name__ + ' could not be reconnected.')

    def _loop_body(self):
        """This method should be overridden by a subclass."""
        pass

    def start_capture(self):
        """Begin listening for output from """ + self.__class__.__name__
        self.finished.clear()
        self._initializing()
        if not self._connect():
            log.warning(self.__class__.__name__ + ' is not connected')
            self._error()
            return
        self.start()

    def stop_capture(self):
        """Stop listening for output from """ + self.__class__.__name__
        self.finished.set()
        try:
            self.join()
        except RuntimeError:
            pass
        self._stopped()
        self._disconnect()

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

    def _connect(self):
        try:
            self.serial_port = serial.Serial(**self.serial_params)
        except (serial.SerialException, OSError):
            if not self._reconnecting:
                log.warning('Can\'t open serial port', exc_info=True)
            return False

        if not self.serial_port.isOpen():
            if not self._reconnecting:
                log.warning('Serial port is not open: %s', self.serial_params.get('port'))
            return False

        return True

    def _disconnect(self):
        if self.serial_port is None:
            return
        self.serial_port.close()
        self.serial_port = None

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
