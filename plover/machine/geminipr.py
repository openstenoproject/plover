# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Thread-based monitoring of a Gemini PR stenotype machine."""

import serial
import threading

STENO_KEY_CHART = ("Fn","#","#","#","#","#","#",
                   "S-","S-","T-","K-","P-","W-","H-",
                   "R-","A-","O-","*","*","res","res",
                   "pwr","*","*","-E","-U","-F","-R",
                   "-P","-B","-L","-G","-T","-S","-D",
                   "#","#","#","#","#","#","-Z")

BYTES_PER_STROKE = 6

class Stenotype(threading.Thread):
    """Standard stenotype interface for a Gemini PR machine.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """
    
    def __init__(self, port='/dev/ttyUSB0'):
        """Monitor a Gemini PR machine over a serial port.

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
        """Overrides base class run method. Do not call directly."""
        while not self.finished.isSet() :

            # Grab data from the serial port.
            raw = self.serial_port.read(BYTES_PER_STROKE)
            if not raw :
                continue
            
            # XXX : work around for python 3.1 and python 2.6 differences
            if isinstance(raw, str) :
                raw = [ord(x) for x in raw]

            # Make sure this is a valid steno stroke.
            if not ((len(raw) == BYTES_PER_STROKE) and
                    (raw[0] & 0x80) and
                    (len([b for b in raw if b & 0x80]) == 1)):
                serial_port.flushInput()
                continue
    
            # Convert the raw to a list of steno keys.
            steno_keys= []
            for i in range(len(raw)):
                b = raw[i]
                for j in range(8):
                    if i == 0 and j == 0:
                        continue # Ignore the first bit 
                    if (b & (0x80 >> j)):
                        steno_keys.append(STENO_KEY_CHART[i*7 + j-1]) 
                
            # Notify all subscribers.
            for callback in self.subscribers:
                callback(steno_keys)

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
