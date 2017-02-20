# -*- coding: utf-8 -*-
# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

# TODO: add tests

"Thread-based monitoring of a stenotype machine using the Treal machine."

from time import sleep

import hid

from plover import log
from plover.machine.base import ThreadedStenotypeBase


STENO_KEY_CHART = (('K-', 'W-', 'R-', '*2', '-R', '-B', '-G', '-S'),
                   ('*1', '-F', '-P', '-L', '-T', '-D', 'X2-', 'S2-'),
                   ('#9', '#A', '#B', 'X1-', 'S1-', 'T-', 'P-', 'H-'),
                   ('#1', '#2', '#3', '#4', '#5', '#6', '#7', '#8'),
                   ('', '', '-Z', 'A-', 'O-', 'X3', '-E', '-U'))

def packet_to_stroke(p):
    keys = []
    for i, b in enumerate(p):
        map = STENO_KEY_CHART[i]
        for i in range(8):
            if (b >> i) & 1:
                key = map[-i + 7]
                if key:
                    keys.append(key)
    return keys

VENDOR_ID = 3526
PRODUCT_IDS = range(1, 11)

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


class Treal(ThreadedStenotypeBase):

    KEYS_LAYOUT = '''
        #1  #2  #3 #4 #5 #6 #7 #8 #9 #A #B
        X1- S1- T- P- H- *1 -F -P -L -T -D
        X2- S2- K- W- R- *2 -R -B -G -S -Z
                   A- O- X3 -E -U
    '''

    def __init__(self, params):
        super(Treal, self).__init__()
        self._machine = None

    def _on_stroke(self, keys):
        steno_keys = self.keymap.keys_to_actions(keys)
        if steno_keys:
            self._notify(steno_keys)

    def _connect(self):
        connected = False
        for product_id in PRODUCT_IDS:
            try:
                if hasattr(hid.device, 'open'):
                    self._machine = hid.device()
                    self._machine.open(VENDOR_ID, product_id)
                else:
                    self._machine = hid.device(VENDOR_ID, product_id)
            except IOError:
                self._machine = None
            else:
                self._machine.set_nonblocking(0)
                self._ready()
                connected = True
                break

        return connected

    def start_capture(self):
        """Begin listening for output from the stenotype machine."""
        if not self._connect():
            log.warning('Treal is not connected')
            self._error()
            return
        super(Treal, self).start_capture()

    def _reconnect(self):
        self._machine = None
        self._initializing()

        connected = self._connect()
        # Reconnect loop
        while not self.finished.isSet() and not connected:
            sleep(0.5)
            connected = self._connect()
        return connected

    def run(self):
        handler = DataHandler(self._on_stroke)
        self._ready()
        while not self.finished.isSet():
            try:
                packet = self._machine.read(5, 100)
            except IOError:
                self._machine.close()
                log.warning(u'Treal disconnected, reconnecting…')
                if self._reconnect():
                    log.warning('Treal reconnected.')
            else:
                if len(packet) is 5:
                    handler.update(packet)

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        super(Treal, self).stop_capture()
        if self._machine:
            self._machine.close()
        self._stopped()
