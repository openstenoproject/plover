# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

# TODO: add tests

"Thread-based monitoring of a stenotype machine using the Treal machine."

import sys

STENO_KEY_CHART = (('K-', 'W-', 'R-', '*', '-R', '-B', '-G', '-S'),
                   ('*', '-F', '-P', '-L', '-T', '-D', '', 'S-'),
                   ('#', '#', '#', '', 'S-', 'T-', 'P-', 'H-'),
                   ('#', '#', '#', '#', '#', '#', '#', '#'),
                   ('', '', '-Z', 'A-', 'O-', '', '-E', '-U'))

def packet_to_stroke(p):
   keys = []
   for i, b in enumerate(p):
       map = STENO_KEY_CHART[i]
       for i in xrange(8):
           if (b >> i) & 1:
               key = map[-i + 7]
               if key:
                   keys.append(key)
   return keys

VENDOR_ID = 3526

EMPTY = [0] * 5

class DataHandler(object):
    def __init__(self, callback):
        self._callback = callback
        self._pressed = EMPTY
        
    def update(self, p):
        if p == EMPTY and self._pressed != EMPTY:
            stroke = packet_to_stroke(self._pressed)
            if stroke:
                self._callback(stroke)
            self._pressed = EMPTY
        else:
            self._pressed = [x[0] | x[1] for x in zip(self._pressed, p)]
        

if sys.platform.startswith('win32'):
    from plover.machine.base import StenotypeBase
    from pywinusb import hid
    
    class Stenotype(StenotypeBase):
        def __init__(self, params):
            StenotypeBase.__init__(self)
            self._machine = None

        def start_capture(self):
            """Begin listening for output from the stenotype machine."""
            devices = hid.HidDeviceFilter(vendor_id = VENDOR_ID).get_devices()
            if len(devices) == 0:
                self._error()
                return
            self._machine = devices[0]
            self._machine.open()
            handler = DataHandler(self._notify)
            
            def callback(p):
                if len(p) != 6: return
                handler.update(p[1:])
            
            self._machine.set_raw_data_handler(callback)
            self._ready()

        def stop_capture(self):
            """Stop listening for output from the stenotype machine."""
            if self._machine:
                self._machine.close()
            self._stopped()

else:
    from plover.machine.base import ThreadedStenotypeBase
    import hid

    class Stenotype(ThreadedStenotypeBase):
        
        def __init__(self, params):
            ThreadedStenotypeBase.__init__(self)
            self._machine = None

        def start_capture(self):
            """Begin listening for output from the stenotype machine."""
            try:
                self._machine = hid.device(VENDOR_ID, 1)
                self._machine.set_nonblocking(1)
            except IOError as e:
                self._error()
                return
            return ThreadedStenotypeBase.start_capture(self)

        def stop_capture(self):
            """Stop listening for output from the stenotype machine."""
            ThreadedStenotypeBase.stop_capture(self)
            if self._machine:
                self._machine.close()
            self._stopped()

        def run(self):
            handler = DataHandler(self._notify)
            self._ready()
            while not self.finished.isSet():
                packet = self._machine.read(5)
                if len(packet) != 5: continue
                handler.update(packet)

if __name__ == '__main__':
    from plover.steno import Stroke
    import time
    def callback(s):
        print Stroke(s).rtfcre
    machine = Stenotype()
    machine.add_callback(callback)
    machine.start_capture()
    time.sleep(30)
    machine.stop_capture()
