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
from plover.exception import InvalidConfigurationError,DictionaryLoaderException
from plover.machine.registry import machine_registry, NoSuchMachineException
from plover import log
from plover.dictionary.loading_manager import manager as dict_manager
from plover import system

# Because 2.7 doesn't have this yet.
class SimpleNamespace(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items))


def init_engine(engine, config):
    """Initialize a StenoEngine from a config object."""
    update_engine(engine, None, config)
    engine.set_is_running(config.get_auto_start())

def reset_machine(engine, config):
    """Set the machine on the engine based on config."""
    update_engine(engine, config, config, reset_machine=True)

def update_engine(engine, old, new, reset_machine=False):
    """Modify a StenoEngine using a before and after config object.
    
    Using the before and after allows this function to not make unnecessary 
    changes.
    """
    if old is None:
        # Fake config that will return None for each
        # option, hence triggering an update.
        class NoneConfig(object):
            def __getattr__(self, name):
                return lambda *args: None
        old = NoneConfig()

    machine_type = new.get_machine_type()
    machine_mappings = new.get_system_keymap(machine_type)
    machine_options = new.get_machine_specific_options(machine_type)
    if (reset_machine or
            old.get_machine_type() != machine_type or
            old.get_system_keymap(machine_type) != machine_mappings or
            old.get_machine_specific_options(machine_type) != machine_options):
        try:
            machine_class = machine_registry.get(machine_type)
        except NoSuchMachineException as e:
            raise InvalidConfigurationError(unicode(e))
        machine = machine_class(machine_options)
        if machine_mappings is None:
            log.warning('no mappings defined for %s, the machine won\'t be usable', machine_type)
        else:
            machine.set_mappings(machine_mappings)
        engine.set_machine(machine)

    dictionary_file_names = new.get_dictionary_file_names()
    if old.get_dictionary_file_names() != dictionary_file_names:
        try:
            dicts = dict_manager.load(dictionary_file_names)
        except DictionaryLoaderException as e:
            raise InvalidConfigurationError(unicode(e))
        engine.get_dictionary().set_dicts(dicts)

    log_file_name = new.get_log_file_name()
    if old.get_log_file_name() != log_file_name:
        engine.set_log_file_name(new)

    enable_stroke_logging = new.get_enable_stroke_logging()
    if old.get_enable_stroke_logging() != enable_stroke_logging:
        engine.enable_stroke_logging(enable_stroke_logging)

    enable_translation_logging = new.get_enable_translation_logging()
    if old.get_enable_translation_logging() != enable_translation_logging:
        engine.enable_translation_logging(enable_translation_logging)

    space_placement = new.get_space_placement()
    if old.get_space_placement() != space_placement:
        engine.set_space_placement(space_placement)

    start_capitalized = new.get_start_capitalized()
    start_attached = new.get_start_attached()
    if (old.get_start_capitalized() != start_capitalized or
            old.get_start_attached() != start_attached):
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
        self.thread_hook = thread_hook

        self.translator = translation.Translator()
        self.formatter = formatting.Formatter()
        self.translator.add_listener(log.translation)
        self.translator.add_listener(self.formatter.format)
        # This seems like a reasonable number. If this becomes a problem it can
        # be parameterized.
        self.translator.set_min_undo_length(10)

        self.full_output = SimpleNamespace()
        self.command_only_output = SimpleNamespace()
        self.running_state = self.translator.get_state()
        self.set_is_running(False)

    def set_machine(self, machine):
        if self.machine is not None:
            self.machine.remove_state_callback(self._machine_state_callback)
            self.machine.remove_stroke_callback(
                self._translator_machine_callback)
            self.machine.remove_stroke_callback(log.stroke)
            self.machine.stop_capture()
        self.machine = machine
        if self.machine is not None:
            self.machine.add_state_callback(self._machine_state_callback)
            self.machine.add_stroke_callback(log.stroke)
            self.machine.add_stroke_callback(self._translator_machine_callback)
            self.machine.start_capture()
            self.set_is_running(self.is_running)
        else:
            self.set_is_running(False)

    def set_dictionary(self, d):
        self.translator.set_dictionary(d)

    def get_dictionary(self):
        return self.translator.get_dictionary()

    def set_is_running(self, value):
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
        
    def set_log_file_name(self, config):
        """Set the file name for log output."""
        filename = config.get_log_file_name()
        if not filename:
            return
        if os.path.realpath(filename) == os.path.realpath(log.LOG_FILENAME):
            log.warning('stroke logging must use a different file than %s, '
                        'renaming to %s', log.LOG_FILENAME, conf.DEFAULT_LOG_FILE)
            filename = conf.DEFAULT_LOG_FILE
            config.set_log_file_name(filename)
            with open(config.target_file, 'wb') as f:
                config.save(f)
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


