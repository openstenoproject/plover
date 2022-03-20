from .wmctrl_x11 import WmCtrl


_wmctrl = WmCtrl()

GetForegroundWindow = _wmctrl.get_foreground_window
SetForegroundWindow = _wmctrl.set_foreground_window
