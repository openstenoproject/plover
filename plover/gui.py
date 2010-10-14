# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""The Plover graphical user interface.

Plover's graphical user interface is a simple task bar icon that
pauses and resumes stenotype translation. If a regular keyboard is
being used as a stenotype machine, this allows the user to switch
between using the keyboard as a regular keyboard and a stenotype.

"""

import os
import wx
import app
import ConfigParser
import plover.machine as machine
import plover.dictionary as dictionary
import plover.app as app
from plover import __name__ as __software_name__
from plover import __version__
from plover import __copyright__
from plover import __long_description__
from plover import __url__
from plover import __credits__
from plover import __license__

MACHINE_CONFIG_TAB_NAME = "Machine"
DICTIONARY_CONFIG_TAB_NAME = "Dictionary"
LOGGING_CONFIG_TAB_NAME = "Logging"
SAVE_CONFIG_BUTTON_NAME = "Save"
CONFIG_PANEL_SIZE = (300, 300)


class PloverGUI(wx.App):
    """The main entry point for the Plover application."""

    def OnInit(self):
        """Called just before the application starts."""
        steno_engine = app.StenoEngine()
        task_bar_icon = PloverTaskBarIcon(app.ASSETS_DIR, steno_engine)
        return True
        

class PloverTaskBarIcon(wx.TaskBarIcon):
    """A task bar icon for controlling a Plover's steno engine.

    When the task bar is left-clicked, Plover is toggled from paused
    to resumed or resumed to paused. When the task bar is
    right-clicked, a menu is displayed with About Plover, Toggle
    Resume/Pause, and Quit options. Selecting the About Plover option
    displays an informational dialog that can be closed by the user.
    
    """
    # Class constants.
    ON_MESSAGE = "Plover is ON"
    OFF_MESSAGE = "Plover is OFF"
    ON_IMAGE_FILE = "plover_on.png"
    OFF_IMAGE_FILE = "plover_off.png"
    ABOUT_MENU_ITEM = "About..."
    CONFIG_MENU_ITEM = "Configure..."
    PAUSE_MENU_ITEM = "Pause"
    RESUME_MENU_ITEM = "Resume"
    QUIT_MENU_ITEM = "Quit"

    TBMENU_CONFIG = wx.NewId()
    TBMENU_ABOUT = wx.NewId()
    TBMENU_PAUSE = wx.NewId()
    TBMENU_RESUME = wx.NewId()
    TBMENU_QUIT = wx.NewId()

    def __init__(self, assets_dir, steno_engine):
        """
        
        Arguments:

        assets_dir -- The base directory containing image and other
        assets to be used by the GUI.

        steno_engine -- A StenoEngine instance to control.

        """
        wx.TaskBarIcon.__init__(self)
        self.steno_engine = steno_engine

        # Create icons.
        on_icon_file = os.path.join(assets_dir, self.ON_IMAGE_FILE)
        off_icon_file = os.path.join(assets_dir, self.OFF_IMAGE_FILE)
        self.on_icon = wx.Icon(on_icon_file, wx.BITMAP_TYPE_PNG)
        self.off_icon = wx.Icon(off_icon_file, wx.BITMAP_TYPE_PNG)
        self._update_icon()
        
        # Bind events.
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarActivate)
        self.Bind(wx.EVT_MENU, self.OnTaskBarAbout, id=self.TBMENU_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnTaskBarConfig, id=self.TBMENU_CONFIG)
        self.Bind(wx.EVT_MENU, self.OnTaskBarPause, id=self.TBMENU_PAUSE)
        self.Bind(wx.EVT_MENU, self.OnTaskBarResume, id=self.TBMENU_RESUME)
        self.Bind(wx.EVT_MENU, self.OnTaskBarQuit, id=self.TBMENU_QUIT)

    def CreatePopupMenu(self):
        """Override of the base class method.
        
        This method is called by the base class when it needs to popup
        the menu for the default EVT_RIGHT_DOWN event.

        """
        menu = wx.Menu()
        menu.Append(self.TBMENU_ABOUT, self.ABOUT_MENU_ITEM)
        menu.Append(self.TBMENU_CONFIG, self.CONFIG_MENU_ITEM)
        if self.steno_engine.is_running :
            menu.Append(self.TBMENU_PAUSE, self.PAUSE_MENU_ITEM)
        else :
            menu.Append(self.TBMENU_RESUME, self.RESUME_MENU_ITEM)
        menu.AppendSeparator()
        menu.Append(self.TBMENU_QUIT, self.QUIT_MENU_ITEM)
        return menu

    def OnTaskBarActivate(self, event):
        """Called when the icon is left-clicked."""
        if self.steno_engine.is_running :
            self.steno_engine.stop()
        else :
            self.steno_engine.start()
        self._update_icon()
        
    def OnTaskBarAbout(self, event):
        """Called when the About menu item is chosen."""
        info = wx.AboutDialogInfo()
        info.Name = __software_name__
        info.Version = __version__
        info.Copyright = __copyright__
        info.Description = __long_description__
        info.WebSite = __url__
        info.Developers = __credits__
        info.License = __license__
        wx.AboutBox(info)

    def OnTaskBarConfig(self, event):
        """Called when the Configure menu item is chosen."""
        dialog = ConfigurationUI(self.steno_engine.config_file)
        dialog.Show()

    def OnTaskBarPause(self, event):
        """Called when the Pause menu item is chosen."""
        self.steno_engine.stop()
        self._update_icon()
        
    def OnTaskBarResume(self, event):
        """Called when the Resume menu item is chosen."""
        self.steno_engine.start()
        self._update_icon()
        
    def OnTaskBarQuit(self, event):
        """Called when the Quit menu item is chosen."""
        self.steno_engine.stop()
        self.Destroy()

    def _update_icon(self):
        # Update the image used for the icon to reflect the state of
        # the steno engine.
        if self.steno_engine.is_running:
            self.SetIcon(self.on_icon, self.ON_MESSAGE)
        else:
            self.SetIcon(self.off_icon, self.OFF_MESSAGE)


class ConfigurationUI(wx.Dialog):
    """A GUI for viewing and editing Plover configuration files.

    Changes to the configuration file are saved when the GUI is
    closed. Changes will take effect the next time the configuration
    file is read by the application, which is typically after an
    application restart.

    """
    def __init__(self, config_file,
                 parent=None,
                 id=-1,
                 title="Plover Configuration",
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE):
        """Create a configuration GUI based on the given config file.

        Argument:

        config_file -- The absolute or relative path to the
        configuration file to view and edit.
        
        """
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)
        self.config_file = config_file
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.config_file)

        sizer = wx.BoxSizer(wx.VERTICAL)

        notebook = wx.Notebook(self)
        notebook.AddPage(MachineConfig(self.config, notebook),
                         MACHINE_CONFIG_TAB_NAME)
        notebook.AddPage(DictionaryConfig(self.config, notebook),
                         DICTIONARY_CONFIG_TAB_NAME)
        notebook.AddPage(LoggingConfig(self.config, notebook),
                         LOGGING_CONFIG_TAB_NAME)
        sizer.Add(notebook)

        button_sizer = wx.StdDialogButtonSizer()
        save_button = wx.Button(self, wx.ID_OK, SAVE_CONFIG_BUTTON_NAME)
        save_button.SetDefault()
        button_sizer.AddButton(save_button)
        cancel_button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()        
        sizer.Add(button_sizer)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def OnClose(self, event):
        with open(self.config_file, 'w') as f:
            self.config.write(f)


class MachineConfig(wx.Panel):
    def __init__(self, config, parent):
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
        sizer = wx.BoxSizer(wx.VERTICAL)
        machines = machine.supported.keys()
        combo_box = wx.ComboBox(self,
                                value=config.get(app.MACHINE_CONFIG_SECTION,
                                                 app.MACHINE_TYPE_OPTION),
                                choices=machines,
                                style=wx.CB_DROPDOWN | wx.CB_SORT)
        combo_box.SetEditable(False)
        sizer.Add(combo_box, 0, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)


class DictionaryConfig(wx.Panel):
    def __init__(self, config, parent):
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
        sizer = wx.GridSizer(3, 2, 5, 5)
        sizer.Add(wx.StaticText(self, label="Format:", style=wx.ALIGN_RIGHT))
        dictionaries = dictionary.supported.keys()
        combo_box = wx.ComboBox(self,
                                value=config.get(app.DICTIONARY_CONFIG_SECTION,
                                                 app.DICTIONARY_FORMAT_OPTION),
                                choices=dictionaries,
                                style=wx.CB_DROPDOWN | wx.CB_SORT)
        combo_box.SetEditable(False)
        sizer.Add(combo_box, 0, wx.EXPAND)
        sizer.Add(wx.StaticText(self, label="Encoding:", style=wx.ALIGN_RIGHT))
        self.SetSizer(sizer)
        sizer.Fit(self)


class LoggingConfig(wx.Panel):
    def __init__(self, config, parent):
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
