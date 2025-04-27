from .display_server import DISPLAY_SERVER

if DISPLAY_SERVER == "x11":
    from .keyboardcontrol_x11 import KeyboardCapture, KeyboardEmulation # pylint: disable=unused-import
else:
    from .keyboardcontrol_uinput import KeyboardCapture, KeyboardEmulation #pylint: disable=unused-import
