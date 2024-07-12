# TODO: add some logging

# TODO: get a stop() function to run when KeyboardEmulation stops, calling `self._ui.close()`
# TODO: figure out a better way to do this:
import os  # To read the layout variable

# TODO: somehow get the requires udev rule installed
from evdev import UInput, ecodes as e, util, InputDevice, list_devices
import threading
from select import select

from .xkb_symbols import generate_symbols

from plover.output.keyboard import GenericKeyboardEmulation
from plover.machine.keyboard_capture import Capture
from plover.key_combo import parse_key_combo
from plover import log


modifiers = {
    "alt_l": e.KEY_LEFTALT,
    "alt_r": e.KEY_RIGHTALT,
    "alt": e.KEY_LEFTALT,
    "control_l": e.KEY_LEFTCTRL,
    "control_r": e.KEY_RIGHTCTRL,
    "control": e.KEY_LEFTCTRL,
    "shift_l": e.KEY_LEFTSHIFT,
    "shift_r": e.KEY_RIGHTSHIFT,
    "shift": e.KEY_LEFTSHIFT,
    "super_l": e.KEY_LEFTMETA,
    "super_r": e.KEY_RIGHTMETA,
    "super": e.KEY_LEFTMETA,
}


keys = {
    # Lowercase
    "a": e.KEY_A,
    "b": e.KEY_B,
    "c": e.KEY_C,
    "d": e.KEY_D,
    "e": e.KEY_E,
    "f": e.KEY_F,
    "g": e.KEY_G,
    "h": e.KEY_H,
    "i": e.KEY_I,
    "j": e.KEY_J,
    "k": e.KEY_K,
    "l": e.KEY_L,
    "m": e.KEY_M,
    "n": e.KEY_N,
    "o": e.KEY_O,
    "p": e.KEY_P,
    "q": e.KEY_Q,
    "r": e.KEY_R,
    "s": e.KEY_S,
    "t": e.KEY_T,
    "u": e.KEY_U,
    "v": e.KEY_V,
    "w": e.KEY_W,
    "x": e.KEY_X,
    "y": e.KEY_Y,
    "z": e.KEY_Z,
    # Numbers
    "1": e.KEY_1,
    "2": e.KEY_2,
    "3": e.KEY_3,
    "4": e.KEY_4,
    "5": e.KEY_5,
    "6": e.KEY_6,
    "7": e.KEY_7,
    "8": e.KEY_8,
    "9": e.KEY_9,
    "0": e.KEY_0,
    # Symbols
    "-": e.KEY_MINUS,
    "=": e.KEY_EQUAL,
    " ": e.KEY_SPACE,
    "[": e.KEY_LEFTBRACE,
    "]": e.KEY_RIGHTBRACE,
    ";": e.KEY_SEMICOLON,
    "'": e.KEY_APOSTROPHE,
    "`": e.KEY_GRAVE,
    "\\": e.KEY_BACKSLASH,
    ".": e.KEY_DOT,
    ",": e.KEY_COMMA,
    "/": e.KEY_SLASH,
    "\b": e.KEY_BACKSPACE,
    "\n": e.KEY_ENTER,
    # Other keys (for send_key_combination())
    # https://github.com/openstenoproject/plover/blob/9b5a357f1fb57cb0a9a8596ae12cd1e84fcff6c4/plover/oslayer/osx/keyboardcontrol.py#L75
    # https://gist.github.com/jfortin42/68a1fcbf7738a1819eb4b2eef298f4f8
    "return": e.KEY_ENTER,
    "tab": e.KEY_TAB,
    "backspace": e.KEY_BACKSPACE,
    "delete": e.KEY_DELETE,
    "escape": e.KEY_ESC,
    "clear": e.KEY_CLEAR,
    # Navigation
    "up": e.KEY_UP,
    "down": e.KEY_DOWN,
    "left": e.KEY_LEFT,
    "right": e.KEY_RIGHT,
    "page_up": e.KEY_PAGEUP,
    "page_down": e.KEY_PAGEDOWN,
    "home": e.KEY_HOME,
    "insert": e.KEY_INSERT,
    "end": e.KEY_END,
    "space": e.KEY_SPACE,
    "print": e.KEY_PRINT,
    # Function keys
    "fn": e.KEY_FN,
    "f1": e.KEY_F1,
    "f2": e.KEY_F2,
    "f3": e.KEY_F3,
    "f4": e.KEY_F4,
    "f5": e.KEY_F5,
    "f6": e.KEY_F6,
    "f7": e.KEY_F7,
    "f8": e.KEY_F8,
    "f9": e.KEY_F9,
    "f10": e.KEY_F10,
    "f11": e.KEY_F11,
    "f12": e.KEY_F12,
    "f13": e.KEY_F13,
    "f14": e.KEY_F14,
    "f15": e.KEY_F15,
    "f16": e.KEY_F16,
    "f17": e.KEY_F17,
    "f18": e.KEY_F18,
    "f19": e.KEY_F19,
    "f20": e.KEY_F20,
    "f21": e.KEY_F21,
    "f22": e.KEY_F22,
    "f23": e.KEY_F23,
    "f24": e.KEY_F24,
    # Numpad
    "kp_1": e.KEY_KP1,
    "kp_2": e.KEY_KP2,
    "kp_3": e.KEY_KP3,
    "kp_4": e.KEY_KP4,
    "kp_5": e.KEY_KP5,
    "kp_6": e.KEY_KP6,
    "kp_7": e.KEY_KP7,
    "kp_8": e.KEY_KP8,
    "kp_9": e.KEY_KP9,
    "kp_0": e.KEY_KP0,
    "kp_add": e.KEY_KPPLUS,
    "kp_decimal": e.KEY_KPDOT,
    "kp_delete": e.KEY_DELETE,  # There is no KPDELETE
    "kp_divide": e.KEY_KPSLASH,
    "kp_enter": e.KEY_KPENTER,
    "kp_equal": e.KEY_KPEQUAL,
    "kp_multiply": e.KEY_KPASTERISK,
    "kp_subtract": e.KEY_KPMINUS,
    # Media keys
    "audioraisevolume": e.KEY_VOLUMEUP,
    "audiolowervolume": e.KEY_VOLUMEDOWN,
    "monbrightnessup": e.KEY_BRIGHTNESSUP,
    "monbrightnessdown": e.KEY_BRIGHTNESSDOWN,
    "audiomute": e.KEY_MUTE,
    "num_lock": e.KEY_NUMLOCK,
    "eject": e.KEY_EJECTCD,
    "audiopause": e.KEY_PAUSE,
    "audioplay": e.KEY_PLAY,
    "audionext": e.KEY_NEXT,  # Maybe VIDEO_NEXT or NEXTSONG
    "audiorewind": e.KEY_REWIND,
    "kbdbrightnessup": e.KEY_KBDILLUMUP,
    "kbdbrightnessdown": e.KEY_KBDILLUMDOWN,
}
KEY_TO_KEYCODE = {**keys, **modifiers}
KEYCODE_TO_KEY = dict(zip(KEY_TO_KEYCODE.values(), KEY_TO_KEYCODE.keys()))

class KeyboardEmulation(GenericKeyboardEmulation):
    def __init__(self):
        super().__init__()
        self._res = util.find_ecodes_by_regex(r"KEY_.*")
        self._ui = UInput(self._res)
        # Set the keyboard layout from an environment variable
        kb_env = "PLOVER_UINPUT_LAYOUT"
        kb_layout = os.environ[kb_env] if kb_env in os.environ else "us"
        self._set_layout(kb_layout)

    def _set_layout(self, layout):
        log.info("Using keyboard layout " + layout + " for keyboard emulation.")
        symbols = generate_symbols(layout)
        # Remove unwanted symbols from the table
        # Includes symbols such as numpad-star - use unicode instead
        # There has to be a cleaner way to do this
        syms_to_remove = []
        for sym in symbols:
            (base, _) = symbols[sym]
            if base not in KEY_TO_KEYCODE:
                syms_to_remove.append(sym)
        for sym in syms_to_remove:
            symbols.pop(sym)
        self._symbols = symbols

    def _press_key(self, key, state):
        self._ui.write(e.EV_KEY, key, 1 if state else 0)
        self._ui.syn()

    def _send_key(self, key):
        self._press_key(key, True)
        self._press_key(key, False)
        self._ui.syn()

    """
    Send a unicode character.
    This depends on an IME such as iBus or fcitx5. iBus is used by GNOME, and fcitx5 by KDE.
    It assumes the default keybinding ctrl-shift-u, enter hex, enter is used, which is the default in both.
    """
    # TODO: avoid hard-coded keys and delays here, maybe call the send key combination function?
    # TODO: at least for the "u" key, as it can vary with different keyboard layouts - maybe use the already existing generated symbols table?
    def _send_unicode(self, hex):
        self._press_key(KEY_TO_KEYCODE["control_l"], True)
        self._press_key(KEY_TO_KEYCODE["shift_r"], True)
        self.delay()
        self._send_key(KEY_TO_KEYCODE["u"])
        self.delay()
        self._press_key(KEY_TO_KEYCODE["control_l"], False)
        self._press_key(KEY_TO_KEYCODE["shift_r"], False)
        self.delay()
        self.send_string(hex)
        self._send_key(KEY_TO_KEYCODE["\n"])

    def _send_char(self, char):
        # Key can be sent with a key combination
        if char in self._symbols:
            (base, mods) = self._symbols[char]
            for mod in mods:
                self._press_key(KEY_TO_KEYCODE[mod], True)
            self.delay()
            self._send_key(KEY_TO_KEYCODE[base])
            for mod in mods:
                self._press_key(KEY_TO_KEYCODE[mod], False)

        # Key press can not be emulated - send unicode symbol instead
        else:
            # Convert to hex and remove leading "0x"
            unicode_hex = hex(ord(char))[2:]
            self._send_unicode(unicode_hex)

    def send_string(self, string):
        for key in self.with_delay(list(string)):
            self._send_char(key)

    def send_backspaces(self, count):
        for _ in range(count):
            self._send_key(KEY_TO_KEYCODE["\b"])

    def send_key_combination(self, combo):
        key_events = parse_key_combo(combo)

        for key, pressed in self.with_delay(key_events):
            k = KEY_TO_KEYCODE[key.lower()]
            self._press_key(k, pressed)


class KeyboardCapture(Capture):
    def __init__(self):
        super().__init__()
        # This is based on the example from the python-evdev documentation, using the first of the three alternative methods: https://python-evdev.readthedocs.io/en/latest/tutorial.html#reading-events-from-multiple-devices-using-select
        self._devices = self._get_devices()
        self._running = False
        self._thread = None
        self._res = util.find_ecodes_by_regex(r"KEY_.*")
        self._ui = UInput(self._res)
        self._suppressed_keys = []

    def _get_devices(self):
        input_devices = [InputDevice(path) for path in list_devices()]
        keyboard_devices = [dev for dev in input_devices if self._filter_devices(dev)]
        return {dev.fd: dev for dev in keyboard_devices}

    def _filter_devices(self, device):
        is_uinput = device.name == "py-evdev-uinput" or device.phys == "py-evdev-uinput"
        capabilities = device.capabilities()
        is_mouse =  e.EV_REL in capabilities or e.EV_ABS in capabilities
        return not is_uinput and not is_mouse

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def cancel(self):
        self._running = False
        [dev.ungrab() for dev in self._devices.values()]
        if self._thread is not None:
            self._thread.join()
        self._ui.close()

    def suppress(self, suppressed_keys=()):
        """
        UInput is not capable of suppressing only specific keys. To get around this, non-suppressed keys
        are passed through to a UInput device and emulated, while keys in this list get sent to plover.
        It does add a little bit of delay, but that is not noticeable.
        """
        self._suppressed_keys = suppressed_keys

    def _run(self):
        [dev.grab() for dev in self._devices.values()]
        while self._running:
            """
            The select() call blocks the loop until it gets an input, which meant that the keyboard
            had to be pressed once after executing `cancel()`. Now, there is a 1 second delay instead
            FIXME: maybe use one of the other options to avoid the timeout
            https://python-evdev.readthedocs.io/en/latest/tutorial.html#reading-events-from-multiple-devices-using-select
            """
            r, _, _ = select(self._devices, [], [], 1)
            for fd in r:
                for event in self._devices[fd].read():
                    if event.type == e.EV_KEY:
                        try:
                            """
                            It could be possible to support different layouts through the xkb_symbols script
                            , however, i think having it like this is actually better, because the keys
                            are supposed to be in these locations, and reduces the amount of work done
                            configuring it afterwards.
                            """
                            if event.code in KEYCODE_TO_KEY:
                                key_name = KEYCODE_TO_KEY[event.code]
                                if key_name in self._suppressed_keys:
                                    pressed = event.value == 1
                                    if pressed:
                                        log.info(f"Key {key_name} pressed")
                                    else:
                                        log.info(f"Key {key_name} released")
                                    (self.key_down if pressed else self.key_up)(key_name)
                                    continue # Go to the next iteration, skipping the below code:
                            self._ui.write(e.EV_KEY, event.code, event.value)
                            self._ui.syn()
                        except KeyError:
                            pass
