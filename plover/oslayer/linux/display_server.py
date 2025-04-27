import os

"""
This value should be one of:
    - x11
    - wayland
    - tty
"""
DISPLAY_SERVER = os.environ.get("XDG_SESSION_TYPE", None)
