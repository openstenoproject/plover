# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration dialog graphical user interface."""

import os
import wx
import wx.lib.filebrowsebutton as filebrowse
import ConfigParser
import plover.machine as machine
import plover.dictionary as dictionary
import plover.config as conf

MACHINE_CONFIG_TAB_NAME = "Machine"
DICTIONARY_CONFIG_TAB_NAME = "Dictionary"
LOGGING_CONFIG_TAB_NAME = "Logging"
SAVE_CONFIG_BUTTON_NAME = "Save"
MACHINE_LABEL = "Stenotype Machine:"
FORMAT_LABEL = "Dictionary Format:"
FILE_LABEL = "Dictionary File:"
FILE_DIALOG_TITLE = "Select a Dictionary File"
CONFIG_BUTTON_NAME = "Configure..."
CONFIG_PANEL_SIZE = (600, 400)
UI_BORDER = 15
COMPONENT_SPACE = 3

class ConfigurationDialog(wx.Dialog):
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

#    def OnClose(self, event):
#        with open(self.config_file, 'w') as f:
#            self.config.write(f)


class MachineConfig(wx.Panel):
    def __init__(self, config, parent):
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
        self.config_class = None
        sizer = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, label=MACHINE_LABEL),
                border=COMPONENT_SPACE,
                flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT)
        machines = machine.supported.keys()
        value = config.get(conf.MACHINE_CONFIG_SECTION,
                           conf.MACHINE_TYPE_OPTION)
        self.choice = wx.Choice(self, choices=machines)
        self.choice.SetStringSelection(value)
        self.Bind(wx.EVT_CHOICE, self.update, self.choice)
        box.Add(self.choice, proportion=1, flag=wx.EXPAND)
        sizer.Add(box, border=UI_BORDER, flag=wx.ALL | wx.EXPAND)
        self.config_button = wx.Button(self,
                                       id=wx.ID_PREFERENCES,
                                       label=CONFIG_BUTTON_NAME)
        box.Add(self.config_button)
        self.SetSizer(sizer)
        self.update()

    def update(self, event=None):
        """Refreshes the UI to reflect current data."""
        mod = conf.import_named_module(self.choice.GetStringSelection(),
                                       machine.supported)
        if ((mod is not None) and
            hasattr(mod, 'Stenotype') and
            hasattr(mod.Stenotype, 'CONFIG_CLASS')):
            self.config_class = mod.Stenotype.CONFIG_CLASS
        else:
            self.config_class = None
        self.config_button.Enable(self.config_class is not None)


class DictionaryConfig(wx.Panel):
    def __init__(self, config, parent):
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
        sizer = wx.BoxSizer(wx.VERTICAL)
        dict_file = config.get(conf.DICTIONARY_CONFIG_SECTION,
                               conf.DICTIONARY_FILE_OPTION)
        dict_file = os.path.join(conf.CONFIG_DIR, dict_file)
        dict_dir = os.path.split(dict_file)[0]
        self.file_browser = filebrowse.FileBrowseButton(self,
                                                        labelText=FILE_LABEL,
                                                        fileMask='*' + \
                                                           conf.JSON_EXTENSION,
                                                        fileMode=wx.OPEN,
                                                        dialogTitle= \
                                                           FILE_DIALOG_TITLE,
                                                        initialValue=dict_file,
                                                        startDirectory=dict_dir)
        sizer.Add(self.file_browser,
                  border=UI_BORDER,
                  flag=wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, label=FORMAT_LABEL),
                border=COMPONENT_SPACE,
                flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT)
        formats = dictionary.supported.keys()
        value = config.get(conf.DICTIONARY_CONFIG_SECTION,
                           conf.DICTIONARY_FORMAT_OPTION)
        self.choice = wx.Choice(self, choices=formats)
        self.choice.SetStringSelection(value)
        box.Add(self.choice, proportion=1)
        sizer.Add(box,
                  border=UI_BORDER,
                  flag=wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND)
        self.SetSizer(sizer)
        return

        
class LoggingConfig(wx.Panel):
    def __init__(self, config, parent):
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
