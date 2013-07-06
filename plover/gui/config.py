# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration dialog graphical user interface."""

import os
import wx
import wx.lib.filebrowsebutton as filebrowse
import plover.config as conf
import plover.gui.serial_config as serial_config
from plover.app import update_engine
from plover.machine.registry import machine_registry
from plover.exception import InvalidConfigurationError

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

    Changes to the configuration file are saved when the GUI is closed. Changes
    will take effect the next time the configuration file is read by the
    application, which is typically after an application restart.

    """
    def __init__(self, engine, config, config_file,
                 parent=None,
                 id=-1,
                 title="Plover Configuration",
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE):
        """Create a configuration GUI based on the given config file.

        Arguments:

        config_file -- The absolute or relative path to the
        configuration file to view and edit.
        during_plover_init -- If this is set to True, the configuration dialog
        won't tell the user that Plover needs to be restarted.
        """
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)
        self.engine = engine
        self.config = config
        self.config_file = config_file

        self._setup_ui()

    def _setup_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # The tab container
        notebook = wx.Notebook(self)

        # Configuring each tab
        self.machine_config = MachineConfig(self.config, notebook)
        self.dictionary_config = DictionaryConfig(self.config, notebook)
        self.logging_config = LoggingConfig(self.config, notebook)

        # Adding each tab
        notebook.AddPage(self.machine_config, MACHINE_CONFIG_TAB_NAME)
        notebook.AddPage(self.dictionary_config, DICTIONARY_CONFIG_TAB_NAME)
        notebook.AddPage(self.logging_config, LOGGING_CONFIG_TAB_NAME)

        sizer.Add(notebook)

        # The bottom button container
        button_sizer = wx.StdDialogButtonSizer()

        # Configuring and adding the save button
        save_button = wx.Button(self, wx.ID_SAVE, SAVE_CONFIG_BUTTON_NAME)
        save_button.SetDefault()
        button_sizer.AddButton(save_button)

        # Configuring and adding the cancel button
        cancel_button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()

        sizer.Add(button_sizer, flag=wx.ALL | wx.ALIGN_RIGHT, border=UI_BORDER)
        self.SetSizer(sizer)
        sizer.Fit(self)

        # Binding the save button to the self._save callback
        self.Bind(wx.EVT_BUTTON, self._save, save_button)

    def _save(self, event):
        old_config = self.config.clone()
        
        self.machine_config.save()
        self.dictionary_config.save()
        self.logging_config.save()

        try:
            update_engine(self.engine, old_config, self.config)
        except InvalidConfigurationError as e:
            alert_dialog = wx.MessageDialog(self,
                                            unicode(e),
                                            "Configuration error",
                                            wx.OK | wx.ICON_INFORMATION)
            alert_dialog.ShowModal()
            alert_dialog.Destroy()
            return

        with open(self.config_file, 'wb') as f:
            self.config.save(f)

        if self.IsModal():
            self.EndModal(wx.ID_SAVE)
        else:
            self.Close()


class MachineConfig(wx.Panel):
    """Stenotype machine configuration graphical user interface."""

    def __init__(self, config, parent):
        """Create a configuration component based on the given ConfigParser.

        Arguments:

        config -- A Config object.

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
        machines = machine_registry.get_all_names()
        value = self.config.get_machine_type()
        self.choice = wx.Choice(self, choices=machines)
        self.choice.SetStringSelection(machine_registry.resolve_alias(value))
        self.Bind(wx.EVT_CHOICE, self._update, self.choice)
        box.Add(self.choice, proportion=1, flag=wx.EXPAND)
        self.config_button = wx.Button(self,
                                       id=wx.ID_PREFERENCES,
                                       label=CONFIG_BUTTON_NAME)
        box.Add(self.config_button)

        self.auto_start_checkbox = wx.CheckBox(self,
                                               label=MACHINE_AUTO_START_LABEL)
        auto_start = config.get_auto_start()
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
        self.config.set_machine_type(machine_type)
        auto_start = self.auto_start_checkbox.GetValue()
        self.config.set_auto_start(auto_start)
        if self.advanced_options:
            self.config.set_machine_specific_options(machine_type, 
                                                     self.advanced_options)

    def _advanced_config(self, event=None):
        class Struct(object):
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
        config_instance = Struct(**self.advanced_options)
        scd = serial_config.SerialConfigDialog(config_instance, self)
        scd.ShowModal()
        #scd.Close()
        self.advanced_options = config_instance.__dict__

    def _update(self, event=None):
        # Refreshes the UI to reflect current data.
        machine_name = self.choice.GetStringSelection()
        options = self.config.get_machine_specific_options(machine_name)
        self.advanced_options = options
        self.config_button.Enable(bool(options))
        # TODO: figure out why advanced options are being copied from machine to machine


class DictionaryConfig(wx.Panel):
    """Dictionary configuration graphical user interface."""
    def __init__(self, config, parent):
        """Create a configuration component based on the given ConfigParser.

        Arguments:

        config -- A Config object.

        parent -- This component's parent component.

        """
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
        sizer = wx.BoxSizer(wx.VERTICAL)
        dict_file = config.get_dictionary_file_name()
        dict_file = os.path.join(conf.CONFIG_DIR, dict_file)
        dict_dir = os.path.split(dict_file)[0]
        mask = 'Json files (*%s)|*%s|RTF/CRE files (*%s)|*%s' % (
            conf.JSON_EXTENSION, conf.JSON_EXTENSION, 
            conf.RTF_EXTENSION, conf.RTF_EXTENSION, 
        )
        self.file_browser = filebrowse.FileBrowseButton(
                                        self,
                                        labelText=DICT_FILE_LABEL,
                                        fileMask=mask,
                                        fileMode=wx.OPEN,
                                        dialogTitle=DICT_FILE_DIALOG_TITLE,
                                        initialValue=dict_file,
                                        startDirectory=dict_dir,
                                        )
        sizer.Add(self.file_browser, border=UI_BORDER, flag=wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)

    def save(self):
        """Write all parameters to the configuration parser."""
        self.config.set_dictionary_file_name(self.file_browser.GetValue())


class LoggingConfig(wx.Panel):
    """Logging configuration graphical user interface."""
    def __init__(self, config, parent):
        """Create a configuration component based on the given ConfigParser.

        Arguments:

        config -- A Config object.

        parent -- This component's parent component.

        """
        wx.Panel.__init__(self, parent, size=CONFIG_PANEL_SIZE)
        self.config = config
        sizer = wx.BoxSizer(wx.VERTICAL)
        log_file = config.get_log_file_name()
        log_file = os.path.join(conf.CONFIG_DIR, log_file)
        log_dir = os.path.split(log_file)[0]
        self.file_browser = filebrowse.FileBrowseButton(
                                            self,
                                            labelText=LOG_FILE_LABEL,
                                            fileMask='*' + conf.LOG_EXTENSION,
                                            fileMode=wx.SAVE,
                                            dialogTitle=LOG_FILE_DIALOG_TITLE,
                                            initialValue=log_file,
                                            startDirectory=log_dir,
                                            )
        sizer.Add(self.file_browser, border=UI_BORDER, flag=wx.ALL | wx.EXPAND)
        self.log_strokes_checkbox = wx.CheckBox(self, label=LOG_STROKES_LABEL)
        stroke_logging = config.get_enable_stroke_logging()
        self.log_strokes_checkbox.SetValue(stroke_logging)
        sizer.Add(self.log_strokes_checkbox,
                  border=UI_BORDER,
                  flag=wx.ALL | wx.EXPAND)
        self.log_translations_checkbox = wx.CheckBox(self,
                                                 label=LOG_TRANSLATIONS_LABEL)
        translation_logging = config.get_enable_translation_logging()
        self.log_translations_checkbox.SetValue(translation_logging)
        sizer.Add(self.log_translations_checkbox,
                  border=UI_BORDER,
                  flag=wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)

    def save(self):
        """Write all parameters to the configuration parser."""
        self.config.set_log_file_name(self.file_browser.GetValue())
        self.config.set_enable_stroke_logging(
            self.log_strokes_checkbox.GetValue())
        self.config.set_enable_translation_logging(
            self.log_translations_checkbox.GetValue())
