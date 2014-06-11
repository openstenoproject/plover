import wx
import plover.gui.main

class TaskBarIcon(wx.TaskBarIcon):

    def __init__(self, on_icon_path, off_icon_path, callback):
        super(TaskBarIcon, self).__init__()
        self.on_icon_path = on_icon_path
        self.off_icon_path = off_icon_path
        self.double_click_callback = callback
        self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.on_double_click)

    def set_active(self, active):
        icon = self.on_icon_path if active else self.off_icon_path
        self.SetIcon(wx.IconFromBitmap(wx.Bitmap(icon)), plover.gui.main.MainFrame.TITLE)

    def on_double_click(self, event):
        if self.double_click_callback:
            self.double_click_callback()

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
