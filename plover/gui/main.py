# coding: utf-8
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
from plover.config import ASSETS_DIR, SPINNER_FILE, copy_default_dictionaries
from plover.gui.config import ConfigurationDialog
import plover.gui.add_translation
import plover.gui.lookup
from plover.oslayer.keyboardcontrol import KeyboardEmulation
from plover.machine.base import STATE_ERROR, STATE_INITIALIZING, STATE_RUNNING
from plover.machine.registry import machine_registry
from plover.gui.paper_tape import StrokeDisplayDialog
from plover.gui.suggestions import SuggestionsDisplayDialog
from plover import log

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

        osx = sys.platform.startswith('darwin')
        if not osx:
            frame.Iconize(self.config.get_start_minimized())
        frame.Show()
        if osx:
            frame.Iconize(self.config.get_start_minimized())
        return True


class MainFrame(wx.Frame):
    """The top-level GUI element of the Plover application."""

    # Class constants.
    TITLE = __software_name__.capitalize()
    ALERT_DIALOG_TITLE = TITLE
    CONNECTED_IMAGE_FILE = os.path.join(ASSETS_DIR, 'connected.png')
    DISCONNECTED_IMAGE_FILE = os.path.join(ASSETS_DIR, 'disconnected.png')
    REFRESH_IMAGE_FILE = os.path.join(ASSETS_DIR, 'refresh.png')
    PLOVER_ICON_FILE = os.path.join(ASSETS_DIR, 'plover.ico')
    BORDER = 5
    STATUS_DISCONNECTED, STATUS_OUTPUT_DISABLED, STATUS_OUTPUT_ENABLED = range(-1, 2)
    ENABLE_OUTPUT_LABEL = "Enable"
    DISABLE_OUTPUT_LABEL = "Disable"
    HEADER_OUTPUT = "Output"
    HEADER_MACHINE = "Machine"
    HEADER_SETTINGS = "Settings"
    CONFIGURE_BUTTON_LABEL = u"Configure…"
    ABOUT_BUTTON_LABEL = u"About…"
    RECONNECT_BUTTON_LABEL = u"Reconnect…"
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
        root = wx.Panel(self, style=wx.DEFAULT_FRAME_STYLE)

        # Menu Bar
        MenuBar = wx.MenuBar()
        self.SetMenuBar(MenuBar)

        # Application icon
        icon = wx.Icon(self.PLOVER_ICON_FILE,
                       wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Configure button.
        self.configure_button = wx.Button(root,
                                          label=self.CONFIGURE_BUTTON_LABEL)
        self.configure_button.Bind(wx.EVT_BUTTON, self._show_config_dialog)

        # About button.
        self.about_button = wx.Button(root, label=self.ABOUT_BUTTON_LABEL)
        self.about_button.Bind(wx.EVT_BUTTON, self._show_about_dialog)

        # Status radio buttons.
        self.radio_output_enable = wx.RadioButton(root,
                                                  label=self.ENABLE_OUTPUT_LABEL)
        self.radio_output_enable.Bind(wx.EVT_RADIOBUTTON,
                                      lambda e: self.steno_engine.set_is_running(True))
        self.radio_output_disable = wx.RadioButton(root,
                                                   label=self.DISABLE_OUTPUT_LABEL)
        self.radio_output_disable.Bind(wx.EVT_RADIOBUTTON,
                                       lambda e: self.steno_engine.set_is_running(False))

        # Machine status.
        # TODO: Figure out why spinner has darker gray background.
        self.spinner = wx.animate.GIFAnimationCtrl(root, -1, SPINNER_FILE)
        self.spinner.GetPlayer().UseBackgroundColour(True)
        # Need to call this so the size of the control is not
        # messed up (100x100 instead of 16x16) on Linux...
        self.spinner.InvalidateBestSize()
        self.spinner.Hide()

        self.connected_bitmap = wx.Bitmap(self.CONNECTED_IMAGE_FILE,
                                          wx.BITMAP_TYPE_PNG)
        self.disconnected_bitmap = wx.Bitmap(self.DISCONNECTED_IMAGE_FILE, 
                                             wx.BITMAP_TYPE_PNG)
        self.connection_ctrl = wx.StaticBitmap(root,
                                               bitmap=self.disconnected_bitmap)

        border_flag = wx.SizerFlags(1).Border(wx.ALL, self.BORDER)

        # Create Settings Box
        settings_sizer = wx.BoxSizer(wx.HORIZONTAL)


        settings_sizer.AddF(self.configure_button, border_flag.Expand())
        settings_sizer.AddF(self.about_button, border_flag.Expand())

        # Create Output Status Box
        box = wx.StaticBox(root, label=self.HEADER_OUTPUT)
        status_sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)

        status_sizer.AddF(self.radio_output_enable, border_flag)
        status_sizer.AddF(self.radio_output_disable, border_flag)

        # Create Machine Status Box
        machine_sizer = wx.BoxSizer(wx.HORIZONTAL)
        center_flag =\
            wx.SizerFlags()\
              .Align(wx.ALIGN_CENTER_VERTICAL)\
              .Border(wx.LEFT | wx.RIGHT, self.BORDER)

        machine_sizer.AddF(self.spinner, center_flag)
        machine_sizer.AddF(self.connection_ctrl, center_flag)
        longest_machine = max(machine_registry.get_all_names(), key=len)
        longest_state = max((STATE_ERROR, STATE_INITIALIZING, STATE_RUNNING),
                            key=len)
        longest_machine_status = '%s: %s' % (longest_machine, longest_state)
        self.machine_status_text = wx.StaticText(root, label=longest_machine_status)
        machine_sizer.AddF(self.machine_status_text, center_flag)
        refresh_bitmap = wx.Bitmap(self.REFRESH_IMAGE_FILE, wx.BITMAP_TYPE_PNG)          
        self.reconnect_button = wx.BitmapButton(root, bitmap=refresh_bitmap)
        machine_sizer.AddF(self.reconnect_button, center_flag)

        # Assemble main UI
        global_sizer = wx.GridBagSizer(vgap=self.BORDER, hgap=self.BORDER)
        global_sizer.Add(settings_sizer,
                         flag=wx.EXPAND,
                         pos=(0, 0),
                         span=(1, 2))
        global_sizer.Add(status_sizer,
                         flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
                         border=self.BORDER,
                         pos=(1, 0),
                         span=(1, 2))
        global_sizer.Add(machine_sizer,
                         flag=wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND | wx.LEFT,
                         pos=(2, 0),
                         border=self.BORDER,
                         span=(1, 2))
        self.machine_sizer = machine_sizer
        # Add a border around the entire sizer.
        border = wx.BoxSizer()
        border.AddF(global_sizer,
                    wx.SizerFlags(1).Border(wx.ALL, self.BORDER).Expand())
        root.SetSizerAndFit(border)
        border.SetSizeHints(self)

        self.Bind(wx.EVT_CLOSE, self._quit)
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.reconnect_button.Bind(wx.EVT_BUTTON, lambda e: self._reconnect())

        try:
            with open(config.target_file, 'rb') as f:
                self.config.load(f)
        except Exception:
            log.error('loading configuration failed, reseting to default', exc_info=True)
            self.config.clear()
        copy_default_dictionaries(self.config)

        rect = wx.Rect(config.get_main_frame_x(), config.get_main_frame_y(), *self.GetSize())
        self.SetRect(AdjustRectToScreen(rect))

        self.steno_engine = app.StenoEngine()
        self.steno_engine.add_callback(
            lambda s: wx.CallAfter(self._update_status, s))
        self.steno_engine.set_output(
            Output(self.consume_command, self.steno_engine))

        self.steno_engine.add_stroke_listener(
            StrokeDisplayDialog.stroke_handler)
        if self.config.get_show_stroke_display():
            StrokeDisplayDialog.display(self, self.config)

        self.steno_engine.formatter.add_listener(
            SuggestionsDisplayDialog.stroke_handler)
        if self.config.get_show_suggestions_display():
            SuggestionsDisplayDialog.display(self, self.config, self.steno_engine)

        try:
            app.init_engine(self.steno_engine, self.config)
        except Exception:
            log.error('engine initialization failed', exc_info=True)
            self._show_config_dialog()

    def _reconnect(self):
        try:
            app.reset_machine(self.steno_engine, self.config)
        except Exception:
            log.error('machine reset failed', exc_info=True)

    def consume_command(self, command):
        # The first commands can be used whether plover has output enabled or not.
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

        # These commands can only be run when plover has output enabled.
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
            self.machine_sizer.Layout()
        if not self.steno_engine.machine or self.steno_engine.machine.state is not STATE_RUNNING:
            status = self.STATUS_DISCONNECTED
        elif self.steno_engine.is_running:
            status = self.STATUS_OUTPUT_ENABLED
        else:
            status = self.STATUS_OUTPUT_DISABLED
        self._show_status(status)

    def _show_status(self, status):
        if status is self.STATUS_DISCONNECTED:
            controls_enabled = False
            output_enabled = False
        elif status is self.STATUS_OUTPUT_DISABLED:
            controls_enabled = True
            output_enabled = False
        elif status is self.STATUS_OUTPUT_ENABLED:
            controls_enabled = True
            output_enabled = True
        else:
            raise ValueError('invalid status: %s' % str(status))
        # Enable / Disable controls
        self.radio_output_disable.Enable(controls_enabled)
        self.radio_output_enable.Enable(controls_enabled)
        # Set selected values
        self.radio_output_disable.SetValue(not output_enabled)
        self.radio_output_enable.SetValue(output_enabled)

    def _quit(self, event=None):
        if self.steno_engine:
            self.steno_engine.destroy()
        self.Destroy()

    def _show_config_dialog(self, event=None):
        dlg = ConfigurationDialog(self.steno_engine,
                                  self.config,
                                  parent=self)
        dlg.Show()

    def _show_about_dialog(self, event=None):
        """Called when the About... button is clicked."""
        info = wx.AboutDialogInfo()
        info.Name = __software_name__.capitalize()
        info.Version = __version__
        info.Copyright = __copyright__
        info.Description = __long_description__
        info.WebSite = __url__
        info.Developers = __credits__
        info.License = __license__
        wx.AboutBox(info)

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

    def _xcall(self, fn, *args, **kwargs):
        try:
            fn(*args, **kwargs)
        except Exception:
            log.error('output failed', exc_info=True)

    def send_backspaces(self, b):
        wx.CallAfter(self._xcall, self.keyboard_control.send_backspaces, b)

    def send_string(self, t):
        wx.CallAfter(self._xcall, self.keyboard_control.send_string, t)

    def send_key_combination(self, c):
        wx.CallAfter(self._xcall, self.keyboard_control.send_key_combination, c)

    # TODO: test all the commands now
    def send_engine_command(self, c):
        result = self.engine_command_callback(c)
        if result and not self.engine.is_running:
            self.engine.machine.suppress_last_stroke(self.send_backspaces)
