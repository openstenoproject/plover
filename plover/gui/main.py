# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""The main graphical user interface.

Plover's graphical user interface is a simple task bar icon that pauses and
resumes stenotype translation and allows for application configuration.

"""

import sys
import os
import wx
import wx.animate
from wx.lib.utils import AdjustRectToScreen
import plover.app as app
from plover.config import ASSETS_DIR, SPINNER_FILE
from plover.gui.config import ConfigurationDialog
import plover.gui.add_translation
import plover.gui.lookup
from plover.oslayer.keyboardcontrol import KeyboardEmulation
from plover.machine.base import STATE_ERROR, STATE_INITIALIZING, STATE_RUNNING
from plover.machine.registry import machine_registry
from plover.exception import InvalidConfigurationError
from plover.gui.paper_tape import StrokeDisplayDialog
from plover.gui.suggestions import SuggestionsDisplayDialog

from plover import __name__ as __software_name__
from plover import __version__
from plover import __copyright__
from plover import __long_description__
from plover import __url__
from plover import __credits__
from plover import __license__


class PloverGUI(wx.App):
    """The main entry point for the Plover application."""

    def __init__(self, config):
        self.config = config
        # Override sys.argv[0] so X11 windows class is correctly set.
        argv = sys.argv
        try:
            sys.argv = [__software_name__] + argv[:1]
            wx.App.__init__(self, redirect=False)
        finally:
            sys.argv = argv

    def OnInit(self):
        """Called just before the application starts."""
        # Enable GUI logging.
        from plover.gui import log as gui_log
        frame = MainFrame(self.config)
        self.SetTopWindow(frame)
        frame.Show()
        return True


def gui_thread_hook(fn, *args):
    wx.CallAfter(fn, *args)

class MainFrame(wx.Frame):
    """The top-level GUI element of the Plover application."""

    # Class constants.
    TITLE = __software_name__.capitalize()
    ALERT_DIALOG_TITLE = TITLE
    ON_IMAGE_FILE = os.path.join(ASSETS_DIR, 'plover_on.png')
    OFF_IMAGE_FILE = os.path.join(ASSETS_DIR, 'plover_off.png')
    CONNECTED_IMAGE_FILE = os.path.join(ASSETS_DIR, 'connected.png')
    DISCONNECTED_IMAGE_FILE = os.path.join(ASSETS_DIR, 'disconnected.png')
    REFRESH_IMAGE_FILE = os.path.join(ASSETS_DIR, 'refresh.png')
    BORDER = 5
    RUNNING_MESSAGE = "running"
    STOPPED_MESSAGE = "stopped"
    ERROR_MESSAGE = "error"
    CONFIGURE_BUTTON_LABEL = "Configure..."
    ABOUT_BUTTON_LABEL = "About..."
    RECONNECT_BUTTON_LABEL = "Reconnect..."
    COMMAND_SUSPEND = 'SUSPEND'
    COMMAND_ADD_TRANSLATION = 'ADD_TRANSLATION'
    COMMAND_LOOKUP = 'LOOKUP'
    COMMAND_RESUME = 'RESUME'
    COMMAND_TOGGLE = 'TOGGLE'
    COMMAND_CONFIGURE = 'CONFIGURE'
    COMMAND_FOCUS = 'FOCUS'
    COMMAND_QUIT = 'QUIT'

    def __init__(self, config):
        self.config = config

        # Note: don't set position from config, since it's not yet loaded.
        wx.Frame.__init__(self, None, title=self.TITLE,
                          style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER |
                                                           wx.RESIZE_BOX |
                                                           wx.MAXIMIZE_BOX))

        # Status button.
        self.on_bitmap = wx.Bitmap(self.ON_IMAGE_FILE, wx.BITMAP_TYPE_PNG)
        self.off_bitmap = wx.Bitmap(self.OFF_IMAGE_FILE, wx.BITMAP_TYPE_PNG)
        self.status_button = wx.BitmapButton(self, bitmap=self.on_bitmap)
        self.status_button.Bind(wx.EVT_BUTTON, self._toggle_steno_engine)

        # Configure button.
        self.configure_button = wx.Button(self,
                                          label=self.CONFIGURE_BUTTON_LABEL)
        self.configure_button.Bind(wx.EVT_BUTTON, self._show_config_dialog)

        # Menu Bar
        MenuBar = wx.MenuBar()
        self.SetMenuBar(MenuBar)

        # About button.
        self.about_button = wx.Button(self, label=self.ABOUT_BUTTON_LABEL)
        self.about_button.Bind(wx.EVT_BUTTON, self._show_about_dialog)

        # Machine status.
        # TODO: Figure out why spinner has darker gray background.
        self.spinner = wx.animate.GIFAnimationCtrl(self, -1, SPINNER_FILE)
        self.spinner.GetPlayer().UseBackgroundColour(True)
        self.spinner.Hide()

        self.connected_bitmap = wx.Bitmap(self.CONNECTED_IMAGE_FILE, 
                                          wx.BITMAP_TYPE_PNG)
        self.disconnected_bitmap = wx.Bitmap(self.DISCONNECTED_IMAGE_FILE, 
                                             wx.BITMAP_TYPE_PNG)
        self.connection_ctrl = wx.StaticBitmap(self, 
                                               bitmap=self.disconnected_bitmap)

        # Layout.
        global_sizer = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.status_button,
                  flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                  border=self.BORDER)
        sizer.Add(self.configure_button,
                  flag=wx.TOP | wx.BOTTOM | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
                  border=self.BORDER)
        sizer.Add(self.about_button,
                  flag=wx.TOP | wx.BOTTOM | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
                  border=self.BORDER)
        global_sizer.Add(sizer)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.spinner,
                  flag=(wx.LEFT | wx.BOTTOM | wx.RIGHT | 
                        wx.ALIGN_CENTER_VERTICAL), 
                  border=self.BORDER)
        sizer.Add(self.connection_ctrl, 
                  flag=(wx.LEFT | wx.BOTTOM | wx.RIGHT | 
                        wx.ALIGN_CENTER_VERTICAL), 
                  border=self.BORDER)
        longest_machine = max(machine_registry.get_all_names(), key=len)
        longest_state = max((STATE_ERROR, STATE_INITIALIZING, STATE_RUNNING), 
                            key=len)
        longest_status = '%s: %s' % (longest_machine, longest_state)
        self.machine_status_text = wx.StaticText(self, label=longest_status)
        sizer.Add(self.machine_status_text, 
                  flag=wx.BOTTOM | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
                  border=self.BORDER)
        refresh_bitmap = wx.Bitmap(self.REFRESH_IMAGE_FILE, wx.BITMAP_TYPE_PNG)          
        self.reconnect_button = wx.BitmapButton(self, bitmap=refresh_bitmap)
        sizer.Add(self.reconnect_button, 
                  flag=wx.BOTTOM | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 
                  border=self.BORDER)
        self.machine_status_sizer = sizer
        global_sizer.Add(sizer)
        self.SetSizer(global_sizer)
        global_sizer.Fit(self)

        self.Bind(wx.EVT_CLOSE, self._quit)
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.reconnect_button.Bind(wx.EVT_BUTTON,
            lambda e: app.reset_machine(self.steno_engine, self.config))

        try:
            with open(config.target_file, 'rb') as f:
                self.config.load(f)
        except InvalidConfigurationError as e:
            self._show_alert(unicode(e))
            self.config.clear()

        rect = wx.Rect(config.get_main_frame_x(), config.get_main_frame_y(), *self.GetSize())
        self.SetRect(AdjustRectToScreen(rect))

        self.steno_engine = app.StenoEngine()
        self.steno_engine.add_callback(
            lambda s: wx.CallAfter(self._update_status, s))
        self.steno_engine.set_output(
            Output(self.consume_command, self.steno_engine))

        while True:
            try:
                app.init_engine(self.steno_engine, self.config)
                break
            except InvalidConfigurationError as e:
                self._show_alert(unicode(e))
                dlg = ConfigurationDialog(self.steno_engine,
                                          self.config,
                                          parent=self)
                ret = dlg.ShowModal()
                if ret == wx.ID_CANCEL:
                    self._quit()
                    return
                    
        self.steno_engine.add_stroke_listener(
            StrokeDisplayDialog.stroke_handler)
        if self.config.get_show_stroke_display():
            StrokeDisplayDialog.display(self, self.config)

        self.steno_engine.formatter.add_listener(
            SuggestionsDisplayDialog.stroke_handler)
        if self.config.get_show_suggestions_display():
            SuggestionsDisplayDialog.display(self, self.config, self.steno_engine)

    def consume_command(self, command):
        # The first commands can be used whether plover is active or not.
        if command == self.COMMAND_RESUME:
            wx.CallAfter(self.steno_engine.set_is_running, True)
            return True
        elif command == self.COMMAND_TOGGLE:
            wx.CallAfter(self.steno_engine.set_is_running,
                         not self.steno_engine.is_running)
            return True
        elif command == self.COMMAND_QUIT:
            wx.CallAfter(self._quit)
            return True

        if not self.steno_engine.is_running:
            return False

        # These commands can only be run when plover is active.
        if command == self.COMMAND_SUSPEND:
            wx.CallAfter(self.steno_engine.set_is_running, False)
            return True
        elif command == self.COMMAND_CONFIGURE:
            wx.CallAfter(self._show_config_dialog)
            return True
        elif command == self.COMMAND_FOCUS:
            def f():
                self.Raise()
                self.Iconize(False)
            wx.CallAfter(f)
            return True
        elif command == self.COMMAND_ADD_TRANSLATION:
            wx.CallAfter(plover.gui.add_translation.Show, 
                         self, self.steno_engine, self.config)
            return True
        elif command == self.COMMAND_LOOKUP:
            wx.CallAfter(plover.gui.lookup.Show, 
                         self, self.steno_engine, self.config)
            return True
            
        return False

    def _update_status(self, state):
        if state:
            machine_name = machine_registry.resolve_alias(
                self.config.get_machine_type())
            self.machine_status_text.SetLabel('%s: %s' % (machine_name, state))
            self.reconnect_button.Show(state == STATE_ERROR)
            self.spinner.Show(state == STATE_INITIALIZING)
            self.connection_ctrl.Show(state != STATE_INITIALIZING)
            if state == STATE_INITIALIZING:
                self.spinner.Play()
            else:
                self.spinner.Stop()
            if state == STATE_RUNNING:
                self.connection_ctrl.SetBitmap(self.connected_bitmap)
            elif state == STATE_ERROR:
                self.connection_ctrl.SetBitmap(self.disconnected_bitmap)
            self.machine_status_sizer.Layout()
        if self.steno_engine.machine:
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
        dlg = ConfigurationDialog(self.steno_engine,
                                  self.config,
                                  parent=self)
        dlg.Show()

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

    def _show_alert(self, message):
        alert_dialog = wx.MessageDialog(self,
                                        message,
                                        self.ALERT_DIALOG_TITLE,
                                        wx.OK | wx.ICON_INFORMATION)
        alert_dialog.ShowModal()
        alert_dialog.Destroy()

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_main_frame_x(pos[0])
        self.config.set_main_frame_y(pos[1])
        event.Skip()


class Output(object):
    def __init__(self, engine_command_callback, engine):
        self.engine_command_callback = engine_command_callback
        self.keyboard_control = KeyboardEmulation()
        self.engine = engine

    def send_backspaces(self, b):
        wx.CallAfter(self.keyboard_control.send_backspaces, b)

    def send_string(self, t):
        wx.CallAfter(self.keyboard_control.send_string, t)

    def send_key_combination(self, c):
        wx.CallAfter(self.keyboard_control.send_key_combination, c)

    # TODO: test all the commands now
    def send_engine_command(self, c):
        result = self.engine_command_callback(c)
        if result and not self.engine.is_running:
            self.engine.machine.suppress = self.send_backspaces
