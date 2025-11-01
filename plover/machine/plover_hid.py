"""
Thread-based monitoring of a Plover HID stenotype machine.

This implementation is based on the plover-machine-hid plugin created by dnaq (MIT license):
https://github.com/dnaq/plover-machine-hid

Plover HID is a simple HID-based protocol that sends the current state
of the steno machine every time that state changes.
"""

from plover.machine.base import ThreadedStenotypeBase
from plover.misc import boolean

import hid
import time
import platform
import ctypes
from plover import log


def _darwin_disable_exclusive_open():
    lib = getattr(hid, "hidapi", None)
    if lib is not None:
        func = getattr(lib, "hid_darwin_set_open_exclusive")
        func.argtypes = (ctypes.c_int,)
        func.restype = None
        func(0)
    else:
        log.warning(
            "could not call hid_darwin_set_open_exclusive; HID may open exclusively"
        )


# Invoke once at import time (before any devices are opened)
if platform.system() == "Darwin":
    _darwin_disable_exclusive_open()

USAGE_PAGE: int = 0xFF50
USAGE: int = 0x4C56

N_LEVERS: int = 64

# A simple report contains the report id 1 and one bit
# for each of the 64 buttons in the report.
SIMPLE_REPORT_TYPE: int = 0x01
SIMPLE_REPORT_LEN: int = N_LEVERS // 8


class InvalidReport(Exception):
    pass


# fmt: off
STENO_KEY_CHART = (
    "S1-", "T-", "K-", "P-", "W-", "H-", "R-", "A-",
    "O-", "*1", "-E", "-U", "-F", "-R", "-P", "-B",
    "-L", "-G", "-T", "-S", "-D", "-Z", "#1", "S2-",
    "*2", "*3", "*4", "#2", "#3", "#4", "#5", "#6",
    "#7", "#8", "#9", "#A", "#B", "#C", "X1", "X2",
    "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10",
    "X11", "X12", "X13", "X14", "X15", "X16", "X17", "X18",
    "X19", "X20", "X21", "X22", "X23", "X24", "X25", "X26",
)
# fmt: on


class PloverHid(ThreadedStenotypeBase):
    # fmt: off
    KEYS_LAYOUT: str = '''
        #1 #2  #3 #4 #5 #6 #7 #8 #9 #A #B #C
           S1- T- P- H- *1 *3 -F -P -L -T -D
           S2- K- W- R- *2 *4 -R -B -G -S -Z
                  A- O-       -E -U
        X1  X2  X3  X4  X5  X6  X7  X8  X9  X10
        X11 X12 X13 X14 X15 X16 X17 X18 X19 X20
        X21 X22 X23 X24 X25 X26 
    '''
    # fmt: on

    def __init__(self, params):
        super().__init__()
        self._params = params
        self._hids = []

    def _parse(self, report):
        # The first byte is the report id, and due to idiosyncrasies
        # in how HID-apis work on different operating system we can't
        # map the report id to the contents in a good way, so we force
        # compliant devices to always use a report id of 0x50 ('P').
        if len(report) > SIMPLE_REPORT_LEN and report[0] == 0x50:
            return int.from_bytes(report[1 : SIMPLE_REPORT_LEN + 1], "big")
        else:
            raise InvalidReport()

    def send(self, key_state):
        steno_actions = self.keymap.keys_to_actions(
            [key for i, key in enumerate(STENO_KEY_CHART) if key_state >> (63 - i) & 1]
        )
        if steno_actions:
            self._notify(steno_actions)

    def run(self):
        self._ready()

        if not self._hids:
            log.error("no HID available")
            self._error()
            return

        key_state = 0
        current = 0
        last_sent = 0
        press_started = time.time()
        sent_first_up = False
        while not self.finished.wait(0):
            interval_ms = self._params["repeat_interval_ms"]

            report = None
            # Poll all devices: block on the first, then non-blocking on the rest
            for idx, dev in enumerate(list(self._hids)):
                try:
                    r = dev.read(65536, interval_ms if idx == 0 else 0)
                except Exception as e:
                    log.debug(f"exception during run: {e}")
                    try:
                        dev.close()
                    except Exception:
                        pass
                    self._hids.remove(dev)
                    continue
                if r:
                    report = r
                    break

            if not report:
                # The set of keys pressed down hasn't changed. Figure out if we need to be sending repeats:
                if (
                    self._params["double_tap_repeat"]
                    and 0 != current == last_sent
                    and time.time() - press_started
                    > self._params["repeat_delay_ms"] / 1e3
                ):
                    self.send(current)
                    # Avoid sending an extra chord when the repeated chord is released.
                    sent_first_up = True
                # If all devices are gone, stop.
                if not self._hids:
                    self._error()
                    return
                continue

            try:
                current = self._parse(report)
            except InvalidReport:
                log.error("invalid report")
                continue

            press_started = time.time()
            if self._params["first_up_chord_send"]:
                if key_state & ~current and not sent_first_up:
                    # A finger went up: send a first-up chord and remember it.
                    self.send(key_state)
                    last_sent = key_state
                    sent_first_up = True
                if current & ~key_state:
                    # A finger went down: get ready to send a new first-up chord.
                    sent_first_up = False
                key_state = current
            else:
                key_state |= current
                if current == 0:
                    # All fingers are up: send the "total" chord and reset it.
                    self.send(key_state)
                    last_sent = key_state
                    key_state = 0

    def start_capture(self):
        self.finished.clear()
        self._initializing()
        # Enumerate all hid devices on the machine and if we find one with our
        # usage page and usage we try to connect to it.
        try:
            devices = [
                device["path"]
                for device in hid.enumerate()
                if device["usage_page"] == USAGE_PAGE and device["usage"] == USAGE
            ]

            if not devices:
                self._error()
                log.info("no device found")
                return

            self._hids = [hid.Device(path=path) for path in devices]
        except Exception as e:
            self._error()
            log.error(f"error during start of capture: {e}")
            return
        self.start()

    def stop_capture(self):
        super().stop_capture()
        for dev in self._hids:
            try:
                dev.close()
            except Exception as e:
                log.debug(f"error while closing device: {e}")
                pass
        self._hids = []

    @classmethod
    def get_option_info(cls):
        return {
            "first_up_chord_send": (False, boolean),
            "double_tap_repeat": (False, boolean),
            "repeat_delay_ms": (200, int),
            "repeat_interval_ms": (30, int),
        }
