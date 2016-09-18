# coding: utf-8
# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration dialog graphical user interface."""

import os
import os.path
import wx
from wx.lib.utils import AdjustRectToScreen
from collections import namedtuple
import wx.lib.filebrowsebutton as filebrowse
from wx.lib.scrolledpanel import ScrolledPanel
import plover.config as conf
from plover.gui.serial_config import SerialConfigDialog
import plover.gui.add_translation
import plover.gui.lookup
import plover.gui.dictionary_editor
from plover import log
from plover.app import update_engine
from plover.machine.registry import machine_registry
from plover.dictionary.loading_manager import manager as dict_manager
from plover.gui.paper_tape import StrokeDisplayDialog
from plover.gui.suggestions import SuggestionsDisplayDialog
from plover.gui.keyboard_config import KeyboardConfigDialog
from plover.misc import SimpleNamespace


EDIT_BUTTON_NAME = "Dictionary Editor"
ADD_TRANSLATION_BUTTON_NAME = "Add Translation"
ADD_DICTIONARY_BUTTON_NAME = "Add Dictionary"
LOOKUP_BUTTON_NAME = "Lookup"
MACHINE_CONFIG_TAB_NAME = "Machine"
DISPLAY_CONFIG_TAB_NAME = "Display"
OUTPUT_CONFIG_TAB_NAME = "Output"
DICTIONARY_CONFIG_TAB_NAME = "Dictionary"
LOGGING_CONFIG_TAB_NAME = "Logging"
SAVE_CONFIG_BUTTON_NAME = "Save"
MACHINE_LABEL = "Stenotype Machine:"
MACHINE_AUTO_START_LABEL = "Automatically Start"
LOG_FILE_LABEL = "Log File:"
LOG_STROKES_LABEL = "Log Strokes"
LOG_TRANSLATIONS_LABEL = "Log Translations"
LOG_FILE_DIALOG_TITLE = "Select a Log File"
CONFIG_BUTTON_NAME = u"Configure…"
SPACE_PLACEMENTS_LABEL = "Space Placement:"
SPACE_PLACEMENT_BEFORE = "Before Output"
SPACE_PLACEMENT_AFTER = "After Output"
SPACE_PLACEMENTS = [SPACE_PLACEMENT_BEFORE, SPACE_PLACEMENT_AFTER]
UNDO_LEVELS_LABEL = "Stroke Undo Limit:"
FIRST_STROKE_LABEL = "First Stroke:"
START_CAPITALIZED_LABEL = "Start Capitalized"
START_ATTACHED_LABEL = "Suppress Space"
TRANSLATION_OPACITY_LABEL = "Translation Dialog Opacity"

UI_BORDER = 4
COMPONENT_SPACE = 3
UP_IMAGE_FILE = os.path.join(conf.ASSETS_DIR, 'up.png')
DOWN_IMAGE_FILE = os.path.join(conf.ASSETS_DIR, 'down.png')
REMOVE_IMAGE_FILE = os.path.join(conf.ASSETS_DIR, 'remove.png')
TITLE = "Plover Configuration"


class ConfigurationDialog(wx.Dialog):
    """A GUI for viewing and editing Plover configuration files.

    Changes to the configuration file are saved when the GUI is closed. Changes
    will take effect the next time the configuration file is read by the
    application, which is typically after an application restart.

    """

    # Keep track of other instances of ConfigurationDialog.
    other_instances = []

    def __init__(self, engine, config, parent):
        """Create a configuration GUI based on the given config file.

        Arguments:

        configuration file to view and edit.
        during_plover_init -- If this is set to True, the configuration dialog
        won't tell the user that Plover needs to be restarted.
        """
        pos = (config.get_config_frame_x(), config.get_config_frame_y())
        size = wx.Size(config.get_config_frame_width(),
                       config.get_config_frame_height())
        wx.Dialog.__init__(self, parent, title=TITLE, pos=pos, size=size,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.engine = engine
        self.config = config

        # Close all other instances.
        if self.other_instances:
            for instance in self.other_instances:
                instance.Close()
        del self.other_instances[:]
        self.other_instances.append(self)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # The tab container
        notebook = wx.Notebook(self)

        # Configuring each tab
        self.machine_config = MachineConfig(self.config, notebook)
        self.dictionary_config = DictionaryConfig(self.engine, self.config,
                                                  notebook)
        self.logging_config = LoggingConfig(self.config, notebook)
        self.display_config = DisplayConfig(self.config, notebook, self.engine)
        self.output_config = OutputConfig(self.config, notebook)

        # Adding each tab
        notebook.AddPage(self.machine_config, MACHINE_CONFIG_TAB_NAME)
        notebook.AddPage(self.dictionary_config, DICTIONARY_CONFIG_TAB_NAME)
        notebook.AddPage(self.logging_config, LOGGING_CONFIG_TAB_NAME)
        notebook.AddPage(self.display_config, DISPLAY_CONFIG_TAB_NAME)
        notebook.AddPage(self.output_config, OUTPUT_CONFIG_TAB_NAME)

        sizer.Add(notebook, proportion=1, flag=wx.EXPAND)

        # The bottom button container
        button_sizer = wx.StdDialogButtonSizer()

        # Configuring and adding the save button
        save_button = wx.Button(self, wx.ID_SAVE, SAVE_CONFIG_BUTTON_NAME)
        save_button.SetDefault()
        button_sizer.AddButton(save_button)

        # Configuring and adding the cancel button
        cancel_button = wx.Button(self, wx.ID_CANCEL, label='Cancel')
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()

        sizer.Add(button_sizer, flag=wx.ALL | wx.ALIGN_RIGHT, border=UI_BORDER)

        self.SetSizerAndFit(sizer)
        self.Layout()
        self.SetRect(AdjustRectToScreen(self.GetRect()))

        # Binding the save button to the self._save callback
        self.Bind(wx.EVT_BUTTON, self._save, save_button)

        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_config_frame_x(pos[0])
        self.config.set_config_frame_y(pos[1])
        event.Skip()

    def on_size(self, event):
        size = self.GetSize()
        self.config.set_config_frame_width(size.GetWidth())
        self.config.set_config_frame_height(size.GetHeight())
        event.Skip()

    def on_close(self, event):
        self.other_instances.remove(self)
        event.Skip()

    def _save(self, event):

        self.machine_config.save()
        self.dictionary_config.save()
        self.logging_config.save()
        self.display_config.save()
        self.output_config.save()

        try:
            update_engine(self.engine, self.config)
        except Exception:
            log.error('updating engine configuration failed', exc_info=True)
            return

        with open(self.config.target_file, 'wb') as f:
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
        wx.Panel.__init__(self, parent)
        self.config = config

        sizer = wx.FlexGridSizer(2, 3)
        sizer.AddGrowableCol(1)

        sizer_flags = wx.SizerFlags(1) \
            .Align(wx.ALIGN_CENTER_VERTICAL) \
            .Border(wx.ALL, UI_BORDER)

        sizer.AddF(
            wx.StaticText(self, label=MACHINE_LABEL),
            sizer_flags.Left())
        machines = machine_registry.get_all_names()
        current_machine = self.config.get_machine_type()
        self.choice = wx.Choice(self, choices=sorted(machines))
        selected_machine = machine_registry.resolve_alias(current_machine)
        self.choice.SetStringSelection(selected_machine)
        sizer.AddF(self.choice, sizer_flags.Expand())
        self.Bind(wx.EVT_CHOICE, self._update, self.choice)

        self.config_button = wx.Button(
            self,
            id=wx.ID_PREFERENCES,
            label=CONFIG_BUTTON_NAME)
        sizer.AddF(self.config_button, sizer_flags.Right())
        self.Bind(wx.EVT_BUTTON, self._advanced_config, self.config_button)

        self.auto_start_checkbox = wx.CheckBox(
            self, label=MACHINE_AUTO_START_LABEL)
        auto_start = config.get_auto_start()
        self.auto_start_checkbox.SetValue(auto_start)
        sizer.AddF(self.auto_start_checkbox, sizer_flags.Left())

        self.SetSizerAndFit(sizer)
        self._update()

    def save(self):
        """Write all parameters to the config."""
        machine_type = self.choice.GetStringSelection()
        self.config.set_machine_type(machine_type)
        auto_start = self.auto_start_checkbox.GetValue()
        self.config.set_auto_start(auto_start)
        if self.advanced_options:
            self.config.set_machine_specific_options(machine_type,
                                                     self.advanced_options)

    def _advanced_config(self, event=None):
        config_instance = SimpleNamespace(**self.advanced_options)
        if 'port' in self.advanced_options:
            scd = SerialConfigDialog(config_instance, self, self.config)
            scd.ShowModal()  # SerialConfigDialog destroys itself.
        else:
            kbd = KeyboardConfigDialog(config_instance, self, self.config)
            kbd.ShowModal()
        self.advanced_options = config_instance.__dict__

    def _update(self, event=None):
        # Refreshes the UI to reflect current data.
        machine_name = self.choice.GetStringSelection()
        try:
            options = self.config.get_machine_specific_options(machine_name)
        except Exception:
            log.error('could not get machine specific options', exc_info=True)
            options = {}
        self.advanced_options = options
        self.config_button.Enable(bool(options))


class DictionaryConfig(ScrolledPanel):

    DictionaryControls = namedtuple('DictionaryControls',
                                    'sizer up down remove label')

    """Dictionary configuration graphical user interface."""
    def __init__(self, engine, config, parent):
        """Create a configuration component based on the given ConfigParser.

        Arguments:

        config -- A Config object.

        parent -- This component's parent component.

        """
        ScrolledPanel.__init__(self, parent)
        self.engine = engine
        self.config = config

        self.up_bitmap = wx.Bitmap(UP_IMAGE_FILE, wx.BITMAP_TYPE_PNG)
        self.down_bitmap = wx.Bitmap(DOWN_IMAGE_FILE, wx.BITMAP_TYPE_PNG)
        self.remove_bitmap = wx.Bitmap(REMOVE_IMAGE_FILE, wx.BITMAP_TYPE_PNG)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        button = wx.Button(self, wx.ID_ANY, EDIT_BUTTON_NAME)
        button_sizer.Add(button, border=UI_BORDER, flag=wx.ALL)
        button.Bind(wx.EVT_BUTTON, self.show_edit)

        button = wx.Button(self, wx.ID_ANY, ADD_TRANSLATION_BUTTON_NAME)
        button_sizer.Add(button, border=UI_BORDER, flag=wx.ALL)
        button.Bind(wx.EVT_BUTTON, self.show_add_translation)

        button = wx.Button(self, wx.ID_ANY, ADD_DICTIONARY_BUTTON_NAME)
        button_sizer.Add(button, border=UI_BORDER, flag=wx.ALL)
        button.Bind(wx.EVT_BUTTON, self.add_dictionary)

        button = wx.Button(self, wx.ID_ANY, LOOKUP_BUTTON_NAME)
        button_sizer.Add(button, border=UI_BORDER, flag=wx.ALL)
        button.Bind(wx.EVT_BUTTON, self.show_lookup)

        main_sizer.Add(button_sizer)

        self.dictionary_controls = []
        self.dicts_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self.dicts_sizer)

        self.mask = 'Json files (*%s)|*%s|RTF/CRE files (*%s)|*%s' % (
            conf.JSON_EXTENSION, conf.JSON_EXTENSION,
            conf.RTF_EXTENSION, conf.RTF_EXTENSION,
        )

        self.SetSizerAndFit(main_sizer)
        self.SetupScrolling()

        # Fill in dictionaries *after* setting the minimum client size.
        for filename in config.get_dictionary_file_names():
            self.add_row(filename)

    def save(self):
        """Write all parameters to the config."""
        filenames = [x.label.GetLabel() for x in self.dictionary_controls]
        self.config.set_dictionary_file_names(filenames)

    def show_add_translation(self, event):
        plover.gui.add_translation.Show(self, self.engine, self.config)

    def show_lookup(self, event):
        plover.gui.lookup.Show(self, self.engine, self.config)

    def show_edit(self, event):
        plover.gui.dictionary_editor.Show(self, self.engine, self.config)

    def add_dictionary(self, event):
        dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", self.mask,
                            wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            all_dicts = [x.label.GetLabel() for x in self.dictionary_controls]
            for path in paths:
                if not os.path.isfile(path):
                    log.warning('"%s" is not a file.', path)
                elif path in all_dicts:
                    log.warning('Dictionary already added, "%s"', path)
                else:
                    self.add_row(path)
        dlg.Destroy()

    def add_row(self, filename):
        dict_manager.start_loading(filename)
        index = len(self.dictionary_controls)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        up = wx.BitmapButton(self, bitmap=self.up_bitmap)
        up.Bind(wx.EVT_BUTTON, lambda e: self.move_row_down(index-1))
        if len(self.dictionary_controls) == 0:
            up.Disable()
        else:
            self.dictionary_controls[-1].down.Enable()
        sizer.Add(up)
        down = wx.BitmapButton(self, bitmap=self.down_bitmap)
        down.Bind(wx.EVT_BUTTON, lambda e: self.move_row_down(index))
        down.Disable()
        sizer.Add(down)
        remove = wx.BitmapButton(self, bitmap=self.remove_bitmap)
        remove.Bind(wx.EVT_BUTTON,
                    lambda e: wx.CallAfter(self.remove_row, index))
        sizer.Add(remove)
        label = wx.StaticText(self, label=filename)
        sizer.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        controls = self.DictionaryControls(sizer, up, down, remove, label)
        self.dictionary_controls.append(controls)
        self.dicts_sizer.Add(sizer)
        self.FitInside()

    def remove_row(self, index):
        names = [self.dictionary_controls[i].label.GetLabel()
                 for i in range(index+1, len(self.dictionary_controls))]
        for i, name in enumerate(names, start=index):
            self.dictionary_controls[i].label.SetLabel(name)
        controls = self.dictionary_controls[-1]
        self.dicts_sizer.Detach(controls.sizer)
        for e in controls:
            e.Destroy()
        del self.dictionary_controls[-1]
        if self.dictionary_controls:
            self.dictionary_controls[-1].down.Disable()
        self.FitInside()

    def move_row_down(self, index):
        top_label = self.dictionary_controls[index].label
        bottom_label = self.dictionary_controls[index+1].label
        tmp = bottom_label.GetLabel()
        bottom_label.SetLabel(top_label.GetLabel())
        top_label.SetLabel(tmp)
        self.GetSizer().Layout()


class LoggingConfig(wx.Panel):
    """Logging configuration graphical user interface."""
    def __init__(self, config, parent):
        """Create a configuration component based on the given Config.

        Arguments:

        config -- A Config object.

        parent -- This component's parent component.

        """
        wx.Panel.__init__(self, parent)
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
        self.log_translations_checkbox = wx.CheckBox(
            self, label=LOG_TRANSLATIONS_LABEL)
        translation_logging = config.get_enable_translation_logging()
        self.log_translations_checkbox.SetValue(translation_logging)
        sizer.Add(self.log_translations_checkbox,
                  border=UI_BORDER,
                  flag=wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)

    def save(self):
        """Write all parameters to the config."""
        self.config.set_log_file_name(self.file_browser.GetValue())
        self.config.set_enable_stroke_logging(
            self.log_strokes_checkbox.GetValue())
        self.config.set_enable_translation_logging(
            self.log_translations_checkbox.GetValue())


class DisplayConfig(wx.Panel):

    START_MINIMIZED_TEXT = "Start Plover minimized"
    SHOW_STROKES_TEXT = "Open stroke display on startup"
    SHOW_STROKES_BUTTON_TEXT = "Open stroke display"
    SHOW_SUGGESTIONS_TEXT = "Open stroke suggestions on startup"
    SHOW_SUGGESTIONS_BUTTON_TEXT = "Open stroke suggestions"

    """Display configuration graphical user interface."""
    def __init__(self, config, parent, engine):
        """Create a configuration component based on the given Config.

        Arguments:

        config -- A Config object.

        parent -- This component's parent component.

        """
        wx.Panel.__init__(self, parent)
        self.config = config
        self.engine = engine
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.start_minimized = wx.CheckBox(self, label=self.START_MINIMIZED_TEXT)
        self.start_minimized.SetValue(config.get_start_minimized())

        sizer.Add(self.start_minimized, border=UI_BORDER, flag=wx.ALL)

        # SHOW STROKES:
        #  [ Open stroke display ]
        #  [X] Open on startup
        show_strokes_button = wx.Button(
            self, label=self.SHOW_STROKES_BUTTON_TEXT)
        show_strokes_button.Bind(wx.EVT_BUTTON, self.on_show_strokes)

        self.show_strokes = wx.CheckBox(self, label=self.SHOW_STROKES_TEXT)
        self.show_strokes.SetValue(config.get_show_stroke_display())

        show_strokes_sizer = wx.BoxSizer(wx.VERTICAL)
        show_strokes_sizer.Add(
            show_strokes_button,
            border=UI_BORDER,
            flag=wx.ALL)
        show_strokes_sizer.Add(
            self.show_strokes,
            border=UI_BORDER,
            flag=(wx.LEFT | wx.RIGHT | wx.BOTTOM))

        sizer.Add(show_strokes_sizer, border=UI_BORDER, flag=wx.BOTTOM)

        # SHOW SUGGESTIONS:
        #  [ Open stroke suggestions ]
        #  [ ] Open on startup
        show_suggestions_button = wx.Button(
            self, label=self.SHOW_SUGGESTIONS_BUTTON_TEXT)
        show_suggestions_button.Bind(wx.EVT_BUTTON, self.on_show_suggestions)

        self.show_suggestions = wx.CheckBox(
            self, label=self.SHOW_SUGGESTIONS_TEXT)
        self.show_suggestions.SetValue(config.get_show_suggestions_display())

        show_suggestions_sizer = wx.BoxSizer(wx.VERTICAL)
        show_suggestions_sizer.Add(
            show_suggestions_button,
            border=UI_BORDER,
            flag=wx.ALL)
        show_suggestions_sizer.Add(
            self.show_suggestions,
            border=UI_BORDER,
            flag=(wx.LEFT | wx.RIGHT | wx.BOTTOM))
        sizer.Add(show_suggestions_sizer, border=UI_BORDER, flag=wx.BOTTOM)

        # OPACITY:
        #   Translation Opacity Title Label
        #   Invisible ----------||---- Opaque: 75%
        translation_opacity_label = wx.StaticText(
            self, label=TRANSLATION_OPACITY_LABEL)

        zero_percent_label = wx.StaticText(self, label="Invisible")

        configured_opacity = self.config.\
            get_translation_frame_opacity()
        self.translation_opacity_slider = wx.Slider(
            self, value=configured_opacity, minValue=0, maxValue=100)
        # NOTE: SetTick is only supported under Windows.
        # This is a wx limitation, not a native GUI toolkit issue.
        for quarter in [25, 50, 75]:
            self.translation_opacity_slider.SetTick(quarter)
        self.translation_opacity_slider.\
            Bind(wx.EVT_SLIDER, self.on_opacity_slider_move)

        self.translation_opacity_value = wx.StaticText(
            self, label=self.label_for_opacity(configured_opacity))

        sizer_flags = wx.SizerFlags(0) \
            .Align(wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        slider_row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        slider_row_sizer.AddF(
            zero_percent_label,
            sizer_flags)

        slider_flags = wx.SizerFlags(2)\
            .Align(wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)\
            .Border(wx.LEFT | wx.RIGHT, UI_BORDER)\
            .Expand()
        slider_row_sizer.AddF(
            self.translation_opacity_slider,
            slider_flags)
        slider_row_sizer.AddF(
            self.translation_opacity_value, sizer_flags)

        opacity_column_sizer = wx.BoxSizer(wx.VERTICAL)
        opacity_column_sizer.AddF(
            translation_opacity_label,
            wx.SizerFlags(0).Align(wx.ALIGN_LEFT).Border(wx.ALL, UI_BORDER))
        opacity_column_sizer.AddF(
            slider_row_sizer,
            wx.SizerFlags(0)
              .Align(wx.ALIGN_LEFT)
              .Border(wx.LEFT | wx.BOTTOM | wx.RIGHT, UI_BORDER)
              .Expand())

        sizer.Add(opacity_column_sizer,
                  border=UI_BORDER, flag=wx.BOTTOM | wx.EXPAND)

        self.SetSizerAndFit(sizer)

    def save(self):
        """Write all parameters to the config."""
        should_start_minimized = self.start_minimized.GetValue()
        should_show_strokes = self.show_strokes.GetValue()
        should_show_suggestions = self.show_suggestions.GetValue()
        translation_opacity = self.\
            translation_opacity_slider.GetValue()
        self.config.set_start_minimized(should_start_minimized)
        self.config.set_show_stroke_display(should_show_strokes)
        self.config.set_show_suggestions_display(should_show_suggestions)
        self.config.set_translation_frame_opacity(
            translation_opacity)

    def on_show_strokes(self, event):
        StrokeDisplayDialog.display(self.GetParent(), self.config)

    def on_show_suggestions(self, event):
        SuggestionsDisplayDialog.display(
            self.GetParent(), self.config, self.engine)

    def on_opacity_slider_move(self, event):
        opacity = self.translation_opacity_slider.GetValue()
        label = self.label_for_opacity(opacity)
        self.translation_opacity_value.SetLabel(label)

    def label_for_opacity(self, opacity):
        label = 'Opaque: {0}%'.format(opacity)
        return label


class OutputConfig(wx.Panel):
    """Display configuration graphical user interface."""

    def __init__(self, config, parent):
        """Create a configuration component based on the given Config.

        Arguments:

        config -- A Config object.

        parent -- This component's parent component.

        """
        wx.Panel.__init__(self, parent)
        self.config = config
        gap = COMPONENT_SPACE * 3
        sizer = wx.GridBagSizer(gap, gap)

        # Space Placement Dropdown
        sizer.Add(wx.StaticText(self, label=SPACE_PLACEMENTS_LABEL),
                  pos=(0, 0),
                  flag=wx.ALIGN_CENTER_VERTICAL)
        self.space_placement_choice = wx.Choice(self, choices=SPACE_PLACEMENTS)
        self.space_placement_choice.SetStringSelection(
            self.config.get_space_placement())
        sizer.Add(self.space_placement_choice,
                  flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
                  pos=(0, 1))

        # Undo Levels Spin Control
        sizer.Add(wx.StaticText(self, label=UNDO_LEVELS_LABEL),
                  pos=(1, 0),
                  flag=wx.ALIGN_CENTER_VERTICAL)
        buffer_selector = wx.SpinCtrl(self)
        buffer_selector.SetRange(conf.MINIMUM_OUTPUT_CONFIG_UNDO_LEVELS,
                                 100000)
        buffer_selector.SetValue(config.get_undo_levels())
        sizer.Add(buffer_selector,
                  pos=(1, 1),
                  flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)

        self.start_attached = wx.CheckBox(self,
                                          label=START_ATTACHED_LABEL)
        self.start_attached.SetValue(self.config.get_start_attached())
        self.start_capitalized = wx.CheckBox(
            self, label=START_CAPITALIZED_LABEL
        )
        self.start_capitalized.SetValue(self.config.get_start_capitalized())

        sizer.Add(wx.StaticText(self, label=FIRST_STROKE_LABEL),
                  pos=(2, 0))

        starting_options = wx.BoxSizer(wx.VERTICAL)
        starting_options.Add(self.start_attached)
        starting_options.Add(self.start_capitalized)
        sizer.Add(starting_options,
                  pos=(2, 1),
                  span=(1, 2),
                  flag=wx.ALIGN_CENTER_VERTICAL)

        self.buffer_selector = buffer_selector

        border = wx.BoxSizer(wx.HORIZONTAL)
        border.AddF(sizer, wx.SizerFlags().Border(wx.ALL, UI_BORDER))

        self.SetSizer(border)

    def save(self):
        """Write all parameters to the config."""
        self.config.set_space_placement(
            self.space_placement_choice.GetStringSelection()
        )
        self.config.set_start_attached(self.start_attached.GetValue())
        self.config.set_start_capitalized(self.start_capitalized.GetValue())
        self.config.set_undo_levels(self.buffer_selector.GetValue())
