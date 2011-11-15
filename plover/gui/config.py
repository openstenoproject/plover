# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration dialog graphical user interface."""

import os
import wx
import wx.lib.filebrowsebutton as filebrowse
import ConfigParser
from serial import Serial
import plover.machine as machine
import plover.dictionary as dictionary
import plover.config as conf
import plover.gui.serial_config as serial_config

RESTART_DIALOG_MESSAGE = "Plover must be restarted before changes take effect."
RESTART_DIALOG_TITLE = "Plover"
MACHINE_CONFIG_TAB_NAME = "Machine"
DICTIONARY_CONFIG_TAB_NAME = "Dictionary"
LOGGING_CONFIG_TAB_NAME = "Logging"
SAVE_CONFIG_BUTTON_NAME = "Save"
MACHINE_LABEL = "Stenotype Machine:"
MACHINE_AUTO_START_LABEL = "Automatically Start"
DICT_FILE_LABEL = "Dictionary File:"
DICT_FILE_DIALOG_TITLE = "Select a Dictionary File"
LOG_FILE_LABEL = "Log File:"
LOG_STROKES_LABEL = "Log Strokes"
LOG_TRANSLATIONS_LABEL = "Log Translations"
LOG_FILE_DIALOG_TITLE = "Select a Log File"
CONFIG_BUTTON_NAME = "Configure..."
CONFIG_PANEL_SIZE = (600, 400)
UI_BORDER = 4
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
        self.machine_config = MachineConfig(self.config, notebook)
        self.dictionary_config = DictionaryConfig(self.config, notebook)
        self.logging_config = LoggingConfig(self.config, notebook)
        notebook.AddPage(self.machine_config, MACHINE_CONFIG_TAB_NAME)
        notebook.AddPage(self.dictionary_config, DICTIONARY_CONFIG_TAB_NAME)
        notebook.AddPage(self.logging_config, LOGGING_CONFIG_TAB_NAME)
        sizer.Add(notebook)

        button_sizer = wx.StdDialogButtonSizer()
        save_button = wx.Button(self, wx.ID_SAVE, SAVE_CONFIG_BUTTON_NAME)
        save_button.SetDefault()
        button_sizer.AddButton(save_button)
        cancel_button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()        
        sizer.Add(button_sizer, flag=wx.ALL | wx.ALIGN_RIGHT, border=UI_BORDER)

        self.Bind(wx.EVT_BUTTON, self._save, save_button)
        self.Bind(wx.EVT_BUTTON, self._cancel, cancel_button)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def _save(self, event):
        self.machine_config.save()
        self.dictionary_config.save()
        self.logging_config.save()
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        restart_dialog = wx.MessageDialog(self,
                                          RESTART_DIALOG_MESSAGE,
                                          RESTART_DIALOG_TITLE,
                                          wx.OK | wx.ICON_INFORMATION)
        restart_dialog.ShowModal()
        restart_dialog.Destroy()
        self.Destroy()

    def _cancel(self, event):
        self.Destroy()


class MachineConfig(wx.Panel):
    """Stenotype machine configuration graphical user interface."""
    
    def __init__(self, config, parent):
        """Create a configuration component based on the given ConfigParser.

        Arguments:

        config -- A ConfigParser object.

        parent -- This component's parent component.

        """
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
        self.config_class = None
        self.config_instance = None
        sizer = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, label=MACHINE_LABEL),
                border=COMPONENT_SPACE,
                flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT)
        machines = machine.supported.keys()
        value = self.config.get(conf.MACHINE_CONFIG_SECTION,
                                conf.MACHINE_TYPE_OPTION)
        self.choice = wx.Choice(self, choices=machines)
        self.choice.SetStringSelection(value)
        self.Bind(wx.EVT_CHOICE, self._update, self.choice)
        box.Add(self.choice, proportion=1, flag=wx.EXPAND)
        self.config_button = wx.Button(self,
                                       id=wx.ID_PREFERENCES,
                                       label=CONFIG_BUTTON_NAME)
        box.Add(self.config_button)

        self.auto_start_checkbox = wx.CheckBox(self, label=MACHINE_AUTO_START_LABEL)
        auto_start = config.getboolean(conf.MACHINE_CONFIG_SECTION,
                                       conf.MACHINE_AUTO_START_OPTION)
        self.auto_start_checkbox.SetValue(auto_start)

        sizer.Add(box, border=UI_BORDER, flag=wx.ALL | wx.EXPAND)
        sizer.Add(self.auto_start_checkbox,
                  border=UI_BORDER,
                  flag=wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)
        self._update()
        self.Bind(wx.EVT_BUTTON, self._advanced_config, self.config_button)

    def save(self):
        """Write all parameters to the configuration parser."""
        machine_type = self.choice.GetStringSelection()
        self.config.set(conf.MACHINE_CONFIG_SECTION,
                        conf.MACHINE_TYPE_OPTION,
                        machine_type)
        auto_start = self.auto_start_checkbox.GetValue()
        self.config.set(conf.MACHINE_CONFIG_SECTION,
                        conf.MACHINE_AUTO_START_OPTION,
                        auto_start)
        if self.config_instance is not None:
            if self.config_class is Serial:
                conf.set_serial_params(self.config_instance,
                                       machine_type,
                                       self.config)

    def _advanced_config(self, event=None):
        # Brings up a more detailed configuration UI, if available.
        if self.config_class:
            machine_type = self.choice.GetStringSelection()
            if self.config_class is Serial:
                if self.config_instance is None:
                    self.config_instance = conf.get_serial_params(machine_type,
                                                                  self.config)
                scd = serial_config.SerialConfigDialog(self.config_instance,
                                                       self)
                scd.ShowModal()
                scd.Destroy()

    def _update(self, event=None):
        # Refreshes the UI to reflect current data.
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
    """Dictionary configuration graphical user interface."""
    def __init__(self, config, parent):
        """Create a configuration component based on the given ConfigParser.

        Arguments:

        config -- A ConfigParser object.

        parent -- This component's parent component.

        """
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
        sizer = wx.BoxSizer(wx.VERTICAL)
        dict_file = config.get(conf.DICTIONARY_CONFIG_SECTION,
                               conf.DICTIONARY_FILE_OPTION)
        dict_file = os.path.join(conf.CONFIG_DIR, dict_file)
        dict_dir = os.path.split(dict_file)[0]
        self.file_browser = filebrowse.FileBrowseButton(self,
                                                     labelText=DICT_FILE_LABEL,
                                                     fileMask='*' + \
                                                        conf.JSON_EXTENSION,
                                                     fileMode=wx.OPEN,
                                                     dialogTitle= \
                                                        DICT_FILE_DIALOG_TITLE,
                                                     initialValue=dict_file,
                                                     startDirectory=dict_dir)
        sizer.Add(self.file_browser, border=UI_BORDER, flag=wx.ALL| wx.EXPAND)
        self.SetSizer(sizer)

    def save(self):
        """Write all parameters to the configuration parser."""
        self.config.set(conf.DICTIONARY_CONFIG_SECTION,
                        conf.DICTIONARY_FILE_OPTION,
                        self.file_browser.GetValue())

        
class LoggingConfig(wx.Panel):
    """Logging configuration graphical user interface."""
    def __init__(self, config, parent):
        """Create a configuration component based on the given ConfigParser.

        Arguments:

        config -- A ConfigParser object.

        parent -- This component's parent component.

        """
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
        sizer = wx.BoxSizer(wx.VERTICAL)
        log_file = config.get(conf.LOGGING_CONFIG_SECTION,
                              conf.LOG_FILE_OPTION)
        log_file = os.path.join(conf.CONFIG_DIR, log_file)
        log_dir = os.path.split(log_file)[0]
        self.file_browser = filebrowse.FileBrowseButton(self,
                                                     labelText=LOG_FILE_LABEL,
                                                     fileMask='*' + \
                                                        conf.LOG_EXTENSION,
                                                     fileMode=wx.SAVE,
                                                     dialogTitle= \
                                                        LOG_FILE_DIALOG_TITLE,
                                                     initialValue=log_file,
                                                     startDirectory=log_dir)
        sizer.Add(self.file_browser, border=UI_BORDER, flag=wx.ALL | wx.EXPAND)
        self.log_strokes_checkbox = wx.CheckBox(self, label=LOG_STROKES_LABEL)
        stroke_logging = config.getboolean(conf.LOGGING_CONFIG_SECTION,
                                           conf.ENABLE_STROKE_LOGGING_OPTION)
        self.log_strokes_checkbox.SetValue(stroke_logging)
        sizer.Add(self.log_strokes_checkbox,
                  border=UI_BORDER,
                  flag=wx.ALL | wx.EXPAND)
        self.log_translations_checkbox = wx.CheckBox(self,
                                                 label=LOG_TRANSLATIONS_LABEL)
        translation_logging = config.getboolean(conf.LOGGING_CONFIG_SECTION,
                                        conf.ENABLE_TRANSLATION_LOGGING_OPTION)
        self.log_translations_checkbox.SetValue(translation_logging)
        sizer.Add(self.log_translations_checkbox,
                  border=UI_BORDER,
                  flag=wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)

    def save(self):
        """Write all parameters to the configuration parser."""
        self.config.set(conf.LOGGING_CONFIG_SECTION,
                        conf.LOG_FILE_OPTION,
                        self.file_browser.GetValue())
        self.config.set(conf.LOGGING_CONFIG_SECTION,
                        conf.ENABLE_STROKE_LOGGING_OPTION,
                        self.log_strokes_checkbox.GetValue())
        self.config.set(conf.LOGGING_CONFIG_SECTION,
                        conf.ENABLE_TRANSLATION_LOGGING_OPTION,
                        self.log_translations_checkbox.GetValue())
