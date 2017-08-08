
import sys


if sys.platform.startswith('win32'):

    from ctypes import windll

    GetForegroundWindow = windll.user32.GetForegroundWindow
    SetForegroundWindow = windll.user32.SetForegroundWindow


elif sys.platform.startswith('darwin'):

    from Foundation import NSAppleScript

    def GetForegroundWindow():
        return NSAppleScript.alloc().initWithSource_("""
tell application "System Events"
    return unix id of first process whose frontmost = true
end tell""").executeAndReturnError_(None)[0].int32Value()

    def SetForegroundWindow(pid):
        NSAppleScript.alloc().initWithSource_("""
tell application "System Events"
    set the frontmost of first process whose unix id is %d to true
end tell""" % pid).executeAndReturnError_(None)


elif sys.platform.startswith('linux'):

    from plover.oslayer.xwmctrl import WmCtrl

    wmctrl = WmCtrl()

    GetForegroundWindow = wmctrl.get_foreground_window
    SetForegroundWindow = wmctrl.set_foreground_window
