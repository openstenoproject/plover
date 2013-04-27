# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"Thread-based monitoring of a stenotype machine using the Treal machine."

from plover.machine.base import ThreadedStenotypeBase
import hid

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

# temp code
def _bin(x, width):
   return ''.join(str((x>>i)&1) for i in xrange(width-1,-1,-1))

_conv_table = [_bin(x,8) for x in range(256)]

def bin(x):
   return _conv_table[x]
# end temp code

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
        pressed = [0] * 5
        empty = [0] * 5
        while not self.finished.isSet():
            packet = self._machine.read(5)
            if len(packet) != 5: continue
            if packet == empty and pressed != empty:
                stroke = packet_to_stroke(pressed)
                if stroke:
                    self._notify(stroke)
                pressed = empty
            else:
                pressed = [x[0] | x[1] for x in zip(pressed, packet)]

if __name__ == '__main__':
    from plover.steno import Stroke
    import time
    def callback(s):
        print Stroke(s).rtfcre
    machine = Stenotype()
    machine.add_callback(callback)
    machine.start_capture()
    time.sleep(5)
    machine.stop_capture()
