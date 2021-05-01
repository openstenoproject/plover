from plover.oslayer.config import PLATFORM


if PLATFORM == 'win':

    from ctypes import windll, wintypes

    GetForegroundWindow = windll.user32.GetForegroundWindow
    GetForegroundWindow.argtypes = []
    GetForegroundWindow.restype = wintypes.HWND

    SetForegroundWindow = windll.user32.SetForegroundWindow
    SetForegroundWindow.argtypes = [
        wintypes.HWND, # hWnd
    ]
    SetForegroundWindow.restype = wintypes.BOOL


elif PLATFORM == 'mac':

    from Cocoa import NSWorkspace, NSRunningApplication, NSApplicationActivateIgnoringOtherApps

    def GetForegroundWindow():
        return NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier()

    def SetForegroundWindow(pid):
        target_window = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
        target_window.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

elif PLATFORM in {'linux', 'bsd'}:

    from plover.oslayer.xwmctrl import WmCtrl

    wmctrl = WmCtrl()

    GetForegroundWindow = wmctrl.get_foreground_window
    SetForegroundWindow = wmctrl.set_foreground_window
