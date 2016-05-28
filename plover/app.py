# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: unit test this module

"""Configuration, initialization, and control of the Plover steno pipeline.

This module's single class, StenoEngine, encapsulates the configuration,
initialization, and control (starting and stopping) of a complete stenographic
processing pipeline, from reading stroke keys from a stenotype machine to
outputting translated English text to the screen. Configuration parameters are
read from a user-editable configuration file. In addition, application log files
are maintained by this module. This module does not provide a graphical user
interface.

"""


import os
# Import plover modules.
import plover.config as conf
import plover.formatting as formatting
import plover.steno as steno
import plover.translation as translation
from plover.exception import InvalidConfigurationError
from plover.machine.registry import machine_registry, NoSuchMachineException
from plover.suggestions import Suggestions
from plover import log
from plover.dictionary.loading_manager import manager as dict_manager
from plover import system
from plover.misc import SimpleNamespace


def init_engine(engine, config):
    """Initialize a StenoEngine from a config object."""
    engine.set_is_running(config.get_auto_start())
    update_engine(engine, config)

def reset_machine(engine, config):
    """Set the machine on the engine based on config."""
    update_engine(engine, config, reset_machine=True)

def update_engine(engine, config, reset_machine=False):
    """Modify a StenoEngine using a before and after config object.
    
    Using the before and after allows this function to not make unnecessary 
    changes.
    """
    machine_type = config.get_machine_type()
    try:
        machine_class = machine_registry.get(machine_type)
    except NoSuchMachineException as e:
        raise InvalidConfigurationError(str(e))
    machine_options = config.get_machine_specific_options(machine_type)
    machine_mappings = config.get_system_keymap(machine_type)
    engine.set_machine(machine_class, machine_options, machine_mappings,
                       reset_machine=reset_machine)

    dictionary_file_names = config.get_dictionary_file_names()
    engine.set_dictionaries(dictionary_file_names)

    log_file_name = config.get_log_file_name()
    if log_file_name:
        # Older versions would use "plover.log" for logging strokes.
        if os.path.realpath(log_file_name) == os.path.realpath(log.LOG_FILENAME):
            log.warning('stroke logging must use a different file than %s, '
                        'renaming to %s', log.LOG_FILENAME, conf.DEFAULT_LOG_FILE)
            log_file_name = conf.DEFAULT_LOG_FILE
            config.set_log_file_name(log_file_name)
            with open(config.target_file, 'wb') as f:
                config.save(f)
    engine.set_log_file_name(log_file_name)

    enable_stroke_logging = config.get_enable_stroke_logging()
    engine.enable_stroke_logging(enable_stroke_logging)

    enable_translation_logging = config.get_enable_translation_logging()
    engine.enable_translation_logging(enable_translation_logging)

    space_placement = config.get_space_placement()
    engine.set_space_placement(space_placement)

    undo_levels = config.get_undo_levels()
    engine.set_undo_levels(undo_levels)

    start_capitalized = config.get_start_capitalized()
    start_attached = config.get_start_attached()
    engine.set_starting_stroke_state(attach=start_attached,
                                     capitalize=start_capitalized)

def same_thread_hook(fn, *args):
    fn(*args)

class StenoEngine(object):
    """Top-level class for using a stenotype machine for text input.

    This class combines all the non-GUI pieces needed to use a stenotype machine
    as a general purpose text entry device. The pipeline consists of the 
    following elements:

    machine: An instance of the Stenotype class from one of the submodules of 
    plover.machine. This object is responsible for monitoring a particular type 
    of hardware for stenotype output and passing that output on to the 
    translator.

    translator: An instance of the plover.steno.Translator class. This object 
    converts raw steno keys into strokes and strokes into translations. The 
    translation objects are then passed on to the formatter.

    formatter: An instance of the plover.formatting.Formatter class. This object 
    converts translation objects into printable text that can be displayed to 
    the user. Orthographic and lexical rules, such as capitalization at the 
    beginning of a sentence and pluralizing a word, are taken care of here. The 
    formatted text is then passed on to the output.

    output: An instance of plover.oslayer.keyboardcontrol.KeyboardEmulation 
    class plus a hook to the application allows output to the screen and control
    of the app with steno strokes.

    In addition to the above pieces, a logger records timestamped strokes and
    translations.

    """

    def __init__(self, thread_hook=same_thread_hook):
        """Creates and configures a single steno pipeline."""
        self.subscribers = []
        self.stroke_listeners = []
        self.is_running = False
        self.machine = None
        self.machine_class = None
        self.machine_options = None
        self.machine_mappings = None
        self.suggestions = None
        self.thread_hook = thread_hook

        self.translator = translation.Translator()
        self.formatter = formatting.Formatter()
        self.translator.add_listener(log.translation)
        self.translator.add_listener(self.formatter.format)

        self.full_output = SimpleNamespace()
        self.command_only_output = SimpleNamespace()
        self.running_state = self.translator.get_state()
        self.set_is_running(False)

    def set_machine(self, machine_class,
                    machine_options=None,
                    machine_mappings=None,
                    reset_machine=False):
        if (not reset_machine and
            self.machine_class == machine_class and
            self.machine_options == machine_options and
            self.machine_mappings == machine_mappings):
            return
        if self.machine is not None:
            log.debug('stopping machine: %s', self.machine_class.__name__)
            self.machine.remove_state_callback(self._machine_state_callback)
            self.machine.remove_stroke_callback(
                self._translator_machine_callback)
            self.machine.remove_stroke_callback(log.stroke)
            self.machine.stop_capture()
            self.machine_class = None
            self.machine_options = None
            self.machine_mappings = None
            self.machine = None
        if machine_class is not None:
            log.debug('starting machine: %s', machine_class.__name__)
            machine = machine_class(machine_options)
            if machine_mappings is not None:
               machine.set_mappings(machine_mappings)
            machine.add_state_callback(self._machine_state_callback)
            machine.add_stroke_callback(log.stroke)
            machine.add_stroke_callback(self._translator_machine_callback)
            self.machine = machine
            self.machine_class = machine_class
            self.machine_options = machine_options
            self.machine_mappings = machine_mappings
            self.machine.start_capture()
            is_running = self.is_running
        else:
            is_running = False
        self.set_is_running(is_running)

    def set_dictionaries(self, file_names):
        dictionary = self.translator.get_dictionary()
        dicts = dict_manager.load(file_names)
        dictionary.set_dicts(dicts)
        self.suggestions = Suggestions(dictionary)

    def get_dictionary(self):
        return self.translator.get_dictionary()

    def get_suggestions(self, translation):
        return self.suggestions.find(translation)

    def set_is_running(self, value):
        if value != self.is_running:
            log.debug('%s output', 'enabling' if value else 'disabling')
        self.is_running = value
        if self.is_running:
            self.translator.set_state(self.running_state)
            self.formatter.set_output(self.full_output)
        else:
            self.translator.clear_state()
            self.formatter.set_output(self.command_only_output)
        if self.machine is not None:
            self.machine.set_suppression(self.is_running)
        for callback in self.subscribers:
            callback(None)

    def set_output(self, o):
        self.full_output.send_backspaces = o.send_backspaces
        self.full_output.send_string = o.send_string
        self.full_output.send_key_combination = o.send_key_combination
        self.full_output.send_engine_command = o.send_engine_command
        self.command_only_output.send_engine_command = o.send_engine_command

    def destroy(self):
        """Halts the stenography capture-translate-format-display pipeline.

        Calling this method causes all worker threads involved to terminate.
        This method should be called at least once if the start method had been
        previously called. Calling this method more than once or before the
        start method has been called has no effect.

        """
        if self.machine:
            self.machine.stop_capture()
        self.is_running = False

    def add_callback(self, callback):
        """Subscribes a function to receive changes of the is_running state.

        Arguments:

        callback -- A function that takes no arguments.

        """
        self.subscribers.append(callback)
        
    def set_log_file_name(self, filename):
        """Set the file name for log output."""
        log.set_stroke_filename(filename)

    def enable_stroke_logging(self, b):
        """Turn stroke logging on or off."""
        log.enable_stroke_logging(b)

    def set_space_placement(self, s):
        """Set whether spaces will be inserted before the output or after the output."""
        self.formatter.set_space_placement(s)

    def set_starting_stroke_state(self, capitalize=False, attach=False):
        self.formatter.start_attached = attach
        self.formatter.start_capitalized = capitalize

    def set_undo_levels(self, levels):
        """Set the maximum number of changes that can be undone."""
        self.translator.set_min_undo_length(levels)

    def enable_translation_logging(self, b):
        """Turn translation logging on or off."""
        log.enable_translation_logging(b)

    def add_stroke_listener(self, listener):
        self.stroke_listeners.append(listener)
        
    def remove_stroke_listener(self, listener):
        self.stroke_listeners.remove(listener)

    def _translate_stroke(self, s):
        stroke = steno.Stroke(s)
        self.translator.translate(stroke)
        for listener in self.stroke_listeners:
            listener(stroke)

    def _translator_machine_callback(self, s):
        self.thread_hook(self._translate_stroke, s)

    def _notify_listeners(self, s):
        for callback in self.subscribers:
            callback(s)

    def _machine_state_callback(self, s):
        self.thread_hook(self._notify_listeners, s)


