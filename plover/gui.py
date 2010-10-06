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
    ABOUT_MENU_ITEM = "About Plover"
    PAUSE_MENU_ITEM = "Pause"
    RESUME_MENU_ITEM = "Resume"
    QUIT_MENU_ITEM = "Quit"

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
        self.Bind(wx.EVT_MENU, self.OnTaskBarPause, id=self.TBMENU_PAUSE)
        self.Bind(wx.EVT_MENU, self.OnTaskBarResume, id=self.TBMENU_RESUME)
        self.Bind(wx.EVT_MENU, self.OnTaskBarQuit, id=self.TBMENU_QUIT)

    def _update_icon(self):
        # Update the image used for the icon to reflect the state of
        # the steno engine.
        if self.steno_engine.is_running:
            self.SetIcon(self.on_icon, self.ON_MESSAGE)
        else:
            self.SetIcon(self.off_icon, self.OFF_MESSAGE)

    def CreatePopupMenu(self):
        """Override of the base class method.
        
        This method is called by the base class when it needs to popup
        the menu for the default EVT_RIGHT_DOWN event.
        """
        menu = wx.Menu()
        menu.Append(self.TBMENU_ABOUT, self.ABOUT_MENU_ITEM)
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
