# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""The main graphical user interface.

Plover's graphical user interface is a simple task bar icon that
pauses and resumes stenotype translation and allows for application
configuration.

"""

import os
import wx
import ConfigParser
import plover.app as app
import plover.config as conf
import plover.gui.config as gui
import plover.exception as exception
from plover import __name__ as __software_name__
from plover import __version__
from plover import __copyright__
from plover import __long_description__
from plover import __url__
from plover import __credits__
from plover import __license__

class PloverGUI(wx.App):
    """The main entry point for the Plover application."""

    def OnInit(self):
        """Called just before the application starts."""
        frame = Frame(conf.CONFIG_FILE)
        frame.Show()
        self.SetTopWindow(frame)
        return True

class Frame(wx.Frame):
    """The top-level GUI element of the Plover application."""

    # Class constants.
    TITLE = "Plover"
    ALERT_DIALOG_TITLE = TITLE
    ON_IMAGE_FILE = "plover_on.png"
    OFF_IMAGE_FILE = "plover_off.png"
    BORDER = 5
    RUNNING_MESSAGE = "running"
    STOPPED_MESSAGE = "stopped"
    ERROR_MESSAGE = "error"
    CONFIGURE_BUTTON_LABEL = "Configure..."
    ABOUT_BUTTON_LABEL = "About..."
    COMMAND_SUSPEND = 'SUSPEND'
    COMMAND_RESUME = 'RESUME'
    COMMAND_TOGGLE = 'TOGGLE'
    COMMAND_CONFIGURE = 'CONFIGURE'
    COMMAND_FOCUS = 'FOCUS'
    COMMAND_QUIT = 'QUIT'

    def __init__(self, config_file):
        wx.Frame.__init__(self, None,
                          title=Frame.TITLE,
                          pos=wx.DefaultPosition,
                          size=wx.DefaultSize,
                          style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER|
                                                           wx.RESIZE_BOX|
                                                           wx.MAXIMIZE_BOX))
        config_file = config_file
        config = ConfigParser.RawConfigParser()
        config.read(config_file)
        try:
            self.steno_engine = app.StenoEngine()
            self.steno_engine.formatter.engine_command_callback = \
              self.consume_command
        except exception.SerialPortException, spe:
            self.steno_engine = None
            alert_dialog = wx.MessageDialog(self._show_config_dialog(),
                                            unicode(spe),
                                            self.ALERT_DIALOG_TITLE,
                                            wx.OK | wx.ICON_INFORMATION)
            alert_dialog.ShowModal()
            alert_dialog.Destroy()

        # Status button.
        on_icon_file = os.path.join(conf.ASSETS_DIR, self.ON_IMAGE_FILE)
        off_icon_file = os.path.join(conf.ASSETS_DIR, self.OFF_IMAGE_FILE)
        self.on_bitmap = wx.Bitmap(on_icon_file, wx.BITMAP_TYPE_PNG)
        self.off_bitmap = wx.Bitmap(off_icon_file, wx.BITMAP_TYPE_PNG)
        self.status_button = wx.BitmapButton(self, bitmap=self.on_bitmap)
        self.status_button.Bind(wx.EVT_BUTTON, self._toggle_steno_engine)

        # Configure button.
        self.configure_button = wx.Button(self, label=self.CONFIGURE_BUTTON_LABEL)
        self.configure_button.Bind(wx.EVT_BUTTON, self._show_config_dialog)

        # About button.
        self.about_button = wx.Button(self, label=self.ABOUT_BUTTON_LABEL)
        self.about_button.Bind(wx.EVT_BUTTON, self._show_about_dialog)

        # Layout.
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.status_button,
                  flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                  border=self.BORDER)
        sizer.Add(self.configure_button,
                  flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL,
                  border=self.BORDER)
        sizer.Add(self.about_button,
                  flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL,
                  border=self.BORDER)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Bind(wx.EVT_CLOSE, self._quit)
        if self.steno_engine:
            self.steno_engine.add_callback(self._update_status)
        self._update_status()

    def consume_command(self, command):
        # Wrap all actions in a CallAfter since the initiator of the
        # action is likely a thread other than the wx thread.
        if command == self.COMMAND_SUSPEND and self.steno_engine:
            wx.CallAfter(self.steno_engine.set_is_running, False)
        elif command == self.COMMAND_RESUME and self.steno_engine:
            wx.CallAfter(self.steno_engine.set_is_running, True)
        elif command == self.COMMAND_TOGGLE and self.steno_engine:
            wx.CallAfter(self.steno_engine.set_is_running, not self.steno_engine.is_running)
        elif command == self.COMMAND_CONFIGURE:
            wx.CallAfter(self._show_config_dialog)
        elif command == self.COMMAND_FOCUS:
            wx.CallAfter(self.Raise)
            wx.CallAfter(self.Iconize, False)
        elif command == self.COMMAND_QUIT:
            wx.CallAfter(self._quit)

    def _update_status(self):
        if self.steno_engine:
            self.status_button.Enable()
            if self.steno_engine.is_running:
                self.status_button.SetBitmapLabel(self.on_bitmap)
                self.SetTitle("%s: %s" % (self.TITLE, self.RUNNING_MESSAGE))
            else:
                self.status_button.SetBitmapLabel(self.off_bitmap)
                self.SetTitle("%s: %s" % (self.TITLE, self.STOPPED_MESSAGE))
        else:
            self.status_button.Disable()
            self.status_button.SetBitmapLabel(self.off_bitmap)
            self.SetTitle("%s: %s" % (self.TITLE, self.ERROR_MESSAGE))

    def _quit(self, event=None):
        if self.steno_engine:
            self.steno_engine.destroy()
        self.Destroy()

    def _toggle_steno_engine(self, event=None):
        """Called when the status button is clicked."""
        self.steno_engine.set_is_running(not self.steno_engine.is_running)

    def _show_config_dialog(self, event=None):
        dialog = gui.ConfigurationDialog(conf.CONFIG_FILE)
        dialog.Show()
        return dialog

    def _show_about_dialog(self, event=None):
        """Called when the About... button is clicked."""
        info = wx.AboutDialogInfo()
        info.Name = __software_name__
        info.Version = __version__
        info.Copyright = __copyright__
        info.Description = __long_description__
        info.WebSite = __url__
        info.Developers = __credits__
        info.License = __license__
        wx.AboutBox(info)

