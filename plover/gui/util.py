# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import sys
import wx


if sys.platform.startswith('win32'):

    from ctypes import windll

    GetForegroundWindow = windll.user32.GetForegroundWindow
    SetForegroundWindow = windll.user32.SetForegroundWindow

    def SetTopApp(w):
        # Nothing else is necessary for windows.
        pass

elif sys.platform.startswith('darwin'):
    from Foundation import NSAppleScript
    from AppKit import NSApp, NSApplication

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

    def SetTopApp(w):
        NSApplication.sharedApplication()
        NSApp().activateIgnoringOtherApps_(True)

elif sys.platform.startswith('linux'):
    from subprocess import call, check_output, CalledProcessError

    def GetForegroundWindow():
        try:
            output = check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'])
            return output.split()[-1]
        except CalledProcessError:
            return None

    def SetForegroundWindow(w):
        """Returns focus to previous application."""
        try:
            call(['wmctrl', '-i', '-a', w])
        except CalledProcessError:
            pass

    def SetTopApp(w):
        """Forces the new dialog to the front."""

        w.Update()  # make sure the dialog has drawn before using wmctrl
        try:
            call(['wmctrl', '-a', w.Title])
        except CalledProcessError:
            pass

else:
    # These functions are optional so provide a non-functional default
    # implementation.
    def GetForegroundWindow():
        return None

    def SetForegroundWindow(w):
        pass

    def SetTopApp(w):
        pass


def find_fixed_width_font(point_size=None,
                          family=wx.FONTFAMILY_DEFAULT,
                          style=wx.FONTSTYLE_NORMAL,
                          weight=wx.FONTWEIGHT_NORMAL):
    '''Look for a suitable fixed width font.'''
    if point_size is None:
        point_size = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT).GetPointSize()
    for face in (
        'monospace',
        'Courier',
        'Courier New',
    ):
        fixed_font = wx.Font(point_size, family, style, weight, face=face)
        if fixed_font.IsFixedWidth():
            break
    # If no suitable font was found, the closest
    # match to Courier New is returned.
    return fixed_font

def shorten_unicode(s):
    '''Detect and shorten Unicode to prevent crashes on Mac OS X.'''
    if not sys.platform.startswith('darwin'):
        return s
    # Turn into 4 byte chars.
    encoded = s.encode('utf-32-be')
    sanitized = ""
    for n in range(0, len(encoded), 4):
        character = encoded[n:n+4].decode('utf-32-be')
        # Get 1 Unicode char at a time.
        character = character.encode('utf-8')
        # Within range?
        if len(character) <= 2:
            sanitized += character
        else:
            # Replace with Unicode replacement character.
            sanitized += unichr(0xfffd)
    return sanitized

