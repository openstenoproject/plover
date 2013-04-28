# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

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
            pressed = EMPTY
        else:
            self._pressed = [x[0] | x[1] for x in zip(self._pressed, p)]
        

if sys.platform.startswith('win32'):
    from plover.machine.base import StenotypeBase
    from pywinusb import hid
    
    class Stenotype(StenotypeBase):
        def __init__(self):
            super(type(self), self).__init__()

        def start_capture(self):
            """Begin listening for output from the stenotype machine."""
            devices = hid.HidDeviceFilter(vendor_id = VENDOR_ID).get_devices()
            if len(devices) == 0:
                raise Exception("No Treal is plugged in.")
            self._machine = devices[0]
            self._machine.open()
            handler = DataHandler(self._notify)
            
            def callback(p):
                if len(p) != 6: return
                handler.update(p[1:])
            
            self._machine.set_raw_data_handler(callback)

        def stop_capture(self):
            """Stop listening for output from the stenotype machine."""
            self._machine.close()

else:
    from plover.machine.base import ThreadedStenotypeBase
    import hid

    class Stenotype(ThreadedStenotypeBase):
        
        def __init__(self):
            super(type(self), self).__init__()

        def start_capture(self):
            """Begin listening for output from the stenotype machine."""
            try:
                self._machine = hid.device(3526, 1)
                self._machine.set_nonblocking(1)
            except IOError as e:
                # TODO(hesky): Figure out what to do here. Maybe start_capture should return a bool or error or raise an exception.
                raise e
            super(type(self), self).start_capture()

        def stop_capture(self):
            """Stop listening for output from the stenotype machine."""
            super(type(self), self).stop_capture()
            self._machine.close()

        def run(self):
            handler = DataHandler(self._notify)
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
